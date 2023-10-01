# Vladhog Security QDAR
Vladhog Security Quick DNS Antivirus Responder - simple antivirus from Vladhog Security team that filter domains with our database

# How it works
Antivirus replace computer dns provider with 2 manual: one work on 127.0.0.1 (local host) where QDAR host our own dns server and 1.1.1.1 (cloudflare) dns for situations where main dns dont work for some reason.
When someone request site that is in our database, dns resolver redirect requests to 127.0.0.1 where antivirus also host website with page that shows that site is blocked.

# Install
First of all, before installation disable your antivirus. Some antiviruses dont like startup file because startup.exe is archive that extract itself to temp folder and then execute startup.exe inside that temp folder.
Then, start startup.exe and add C:\Program Files (x86)\Vladhog Security QDAR folder to antivirus exceptions, because startup.exe will be used later for auto start antivirus on windows start and for updating it on every start.

# Customisation
You can customise your block page by editing blocked.html

# Terms of usage
Two simple rules: protection free for everyone and non-commercial usage only.
General terms for all Vladhog Security Services are here: https://vladhog.ru/promo/securitybot/tos

# Contect us
security@vladhog.ru

