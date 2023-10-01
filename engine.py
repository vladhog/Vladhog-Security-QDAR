import threading
import traceback

from flask import Flask, request, redirect, render_template

app = Flask("DNS_QUIC")
app2 = Flask("DNS_QUIC_HTTP", template_folder='./')

@app.before_request
def before_request():
    if request.url.startswith('https://'):
        url = request.url.replace('https://', 'http://', 1)
        code = 301
        return redirect(url, code=code)

@app2.route('/')
@app2.route('/<first>')
@app2.route('/<first>/<path:rest>')
def nopath_index1(first=None, rest=None):
    try:
        return render_template('blocked.html')
    except Exception:
        return """<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>This domain was blocked by Vladhog Security</title>
    </head>
    <body>
        <h1 align="center">This domain is malicious</h1>
        <h2 align="center">Protected by Vladhog Security</h2>
    </body>
    </html>"""


threading.Thread(target=app2.run, args=("127.0.0.1", 80)).start()
app.run(port=443, ssl_context="adhoc")
