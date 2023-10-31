# Vladhog Security QDAR
Vladhog Security Quick DNS Antivirus Responder is a simple antivirus created by the Vladhog Security team. It filters domains using our database.

## How It Works
The antivirus replaces your computer's DNS provider with two options: one that operates on 127.0.0.1 (the local host), where QDAR hosts its DNS server, and another using 1.1.1.1 (Cloudflare's DNS) for situations where the main DNS doesn't function for any reason. When someone requests a site that is in our database, the DNS resolver redirects the requests to 127.0.0.1, where the antivirus also hosts a webpage indicating that the site is blocked.

## Installation
Before installation, disable your antivirus software. Some antivirus programs may block the startup file because "startup.exe" is an archive that extracts itself to a temporary folder and then executes "startup.exe" from within that folder. Afterward, run "startup.exe" and add the "C:\Program Files (x86)\Vladhog Security QDAR" folder to your antivirus exceptions. This is necessary because "startup.exe" will be used later to automatically start the antivirus when Windows boots and for updating it with each start.

## Customization
You can customize your block page by editing the "blocked.html" file.

## Terms of Usage
There are two simple rules: this protection is free for everyone, and it's for non-commercial use only. You can find the general terms for all Vladhog Security services [here](https://vladhog.ru/promo/securitybot/tos).

## License
Vladhog Security Quick DNS Antivirus Responder © 2023 by Vladhog Security is licensed under Attribution-NonCommercial-ShareAlike 4.0 International.

## Contact Us
Email: security@vladhog.ru
