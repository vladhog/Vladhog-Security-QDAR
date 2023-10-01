import os
import time

from dnserver import DNSServer
from dnserver.load_records import Zone

server = DNSServer(port=53)
server.start()
