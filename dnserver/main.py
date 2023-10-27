from __future__ import annotations as _annotations

from .db import link_db
import asyncio
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from textwrap import wrap
from typing import Any, List
import threading

from dnslib import QTYPE, RR, DNSLabel, dns
from dnslib.proxy import ProxyResolver as LibProxyResolver
from dnslib.server import BaseResolver as LibBaseResolver, DNSServer as LibDNSServer

from .load_records import Records, Zone, load_records

__all__ = 'DNSServer', 'logger'

SERIAL_NO = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s: %(message)s', datefmt='%H:%M:%S'))

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

TYPE_LOOKUP = {
    'A': (dns.A, QTYPE.A),
    'AAAA': (dns.AAAA, QTYPE.AAAA),
    'CAA': (dns.CAA, QTYPE.CAA),
    'CNAME': (dns.CNAME, QTYPE.CNAME),
    'DNSKEY': (dns.DNSKEY, QTYPE.DNSKEY),
    'MX': (dns.MX, QTYPE.MX),
    'NAPTR': (dns.NAPTR, QTYPE.NAPTR),
    'NS': (dns.NS, QTYPE.NS),
    'PTR': (dns.PTR, QTYPE.PTR),
    'RRSIG': (dns.RRSIG, QTYPE.RRSIG),
    'SOA': (dns.SOA, QTYPE.SOA),
    'SRV': (dns.SRV, QTYPE.SRV),
    'TXT': (dns.TXT, QTYPE.TXT),
    'SPF': (dns.TXT, QTYPE.TXT),
}
DEFAULT_PORT = 53
DEFAULT_UPSTREAM = '1.1.1.1'

response_list = {}


class Record:
    def __init__(self, zone: Zone):
        self._rname = DNSLabel(zone.host)

        rd_cls, self._rtype = TYPE_LOOKUP[zone.type]

        args: list[Any]
        if isinstance(zone.answer, str):
            if self._rtype == QTYPE.TXT:
                args = [wrap(zone.answer, 255)]
            else:
                args = [zone.answer]
        else:
            if self._rtype == QTYPE.SOA and len(zone.answer) == 2:
                # add sensible times to SOA
                args = zone.answer + [(SERIAL_NO, 3600, 3600 * 3, 3600 * 24, 3600)]
            else:
                args = zone.answer

        if self._rtype in (QTYPE.NS, QTYPE.SOA):
            ttl = 3600 * 24
        else:
            ttl = 300

        self.rr = RR(
            rname=self._rname,
            rtype=self._rtype,
            rdata=rd_cls(*args),
            ttl=ttl,
        )

    def match(self, q):
        return q.qname == self._rname and (q.qtype == QTYPE.ANY or q.qtype == self._rtype)

    def sub_match(self, q):
        return self._rtype == QTYPE.SOA and q.qname.matchSuffix(self._rname)

    def __str__(self):
        return str(self.rr)
def resolve(request, handler, records):
    def md5(url):
        m = hashlib.md5()
        m.update(url.encode('utf-8'))
        return m.hexdigest()

    name = str(request.q.qname)[:len(str(request.q.qname))-1]
    if name != "vladhog.ru":
        name_md5 = md5(name)
        if name_md5 not in list(response_list):
            res = link_db.find_one({"hash": name_md5})
            if res is None:
                res = {"hash": name_md5, "malicious": "0"}
            response_list[name_md5] = res
        else:
            res = response_list[name_md5]
        #print(res)
        if res["malicious"] == "1":
            records.zones.append(Zone(name, "A", "127.0.0.1"))

    records = [Record(zone) for zone in records.zones]
    type_name = QTYPE[request.q.qtype]
    reply = request.reply()
    for record in records:
        if record.match(request.q):
            reply.add_answer(record.rr)

    if reply.rr:
        logger.info('found zone for %s[%s], %d replies', request.q.qname, type_name, len(reply.rr))
        return reply

    # no direct zone so look for an SOA record for a higher level zone
    for record in records:
        if record.sub_match(request.q):
            reply.add_answer(record.rr)

    if reply.rr:
        logger.info('found higher level SOA resource for %s[%s]', request.q.qname, type_name)
        return reply


class BaseResolver(LibBaseResolver):
    def __init__(self, records: Records):
        self.records = records
        super().__init__()

    def resolve(self, request, handler):
        answer = resolve(request, handler, self.records)
        if answer:
            return answer

        type_name = QTYPE[request.q.qtype]
        logger.info('no local zone found, not proxying %s[%s]', request.q.qname, type_name)
        return request.reply()


class ProxyResolver(LibProxyResolver):
    def __init__(self, records: Records, upstream: str):
        self.records = records
        super().__init__(address=upstream, port=53, timeout=5)

    def resolve(self, request, handler):
        answer = resolve(request, handler, self.records)
        if answer:
            return answer

        type_name = QTYPE[request.q.qtype]
        logger.info('no local zone found, proxying %s[%s]', request.q.qname, type_name)
        return super().resolve(request, handler)


class DNSServer:
    def __init__(
        self,
        records: Records | None = None,
        port: int | str | None = DEFAULT_PORT,
        upstream: str | None = DEFAULT_UPSTREAM,
    ):
        self.port: int = DEFAULT_PORT if port is None else int(port)
        self.upstream: str | None = upstream
        self.udp_server: LibDNSServer | None = None
        self.tcp_server: LibDNSServer | None = None
        self.records: Records = records if records else Records(zones=[])

    @classmethod
    def from_toml(
        cls, zones_file: str | Path, *, port: int | str | None = DEFAULT_PORT, upstream: str | None = DEFAULT_UPSTREAM
    ) -> 'DNSServer':
        records = load_records(zones_file)
        logger.info(
            'loaded %d zone record from %s, with %s as a proxy DNS server',
            len(records.zones),
            zones_file,
            upstream,
        )
        return DNSServer(records, port=port, upstream=upstream)

    def start(self):
        if self.upstream:
            logger.info('starting DNS on port: %d, upstream DNS server "%s"', self.port, self.upstream)
            resolver = ProxyResolver(self.records, self.upstream)
        else:
            logger.info('starting DNS on port: %d, without upstream DNS server', self.port)
            resolver = BaseResolver(self.records)

        self.udp_server = LibDNSServer(resolver, port=self.port)
        udp_thread = threading.Thread(target=self.udp_server.start)
        udp_thread.start()

        self.tcp_server = LibDNSServer(resolver, port=self.port, tcp=True)
        tcp_thread = threading.Thread(target=self.tcp_server.start)
        tcp_thread.start()

    def stop(self):
        if self.udp_server:
            self.udp_server.stop()
            self.udp_server.server.server_close()
        if self.tcp_server:
            self.tcp_server.stop()
            self.tcp_server.server.server_close()

    @property
    def is_running(self):
        udp_alive = self.udp_server and self.udp_server.isAlive()
        tcp_alive = self.tcp_server and self.tcp_server.isAlive()
        return udp_alive or tcp_alive

    def add_record(self, zone: Zone):
        self.records.zones.append(zone)

    def set_records(self, zones: List[Zone]):
        self.records.zones = zones
