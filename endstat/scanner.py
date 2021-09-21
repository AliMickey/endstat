from flask import current_app
import socket, threading, json, requests, time, sqlite3, re
from datetime import datetime
from queue import Queue
from threading import Thread
from urllib.request import socket
from requests.api import get

#App imports
from endstat.db import get_db

print_lock = threading.Lock()
socket.setdefaulttimeout(0.2)

safePorts = {80: 'http', 443: 'https'}
warningPorts = {20: 'ftp'}
dangerPorts = {22: 'ssh'}

# Open port scanner
def portScanThread(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try: 
        result = sock.connect_ex((ip, port))
        sock.settimeout(None)
        if result == 0:
            return port
        sock.close()
    except socket.error:
        return None
    except socket.timeout:
        return None

# Return all open ports on domain with multi-threading
def portScan(domain):
    threadsList = list()
    que = Queue() 
    openPorts = []
    remoteServerIP = socket.gethostbyname(domain) # Get ip for provided domain
    portsToScan = [21, 22, 23, 25, 80, 110, 139, 143, 443, 445, 1433, 1521, 3306, 3389]
    for x in portsToScan:
        thread = Thread(target=lambda q, arg1,arg2: q.put(portScanThread(arg1,arg2)), args=(que, remoteServerIP, x))
        thread.start()
        threadsList.append(thread)
    for t in threadsList:
        t.join()
    while not que.empty():
        result = que.get()
        if result is not None:
            if result in safePorts:
                openPorts.append([result,safePorts[result],'safe'])
            elif result in warningPorts:
                openPorts.append([result,warningPorts[result],'warn'])
            elif result in dangerPorts:
                openPorts.append([result,dangerPorts[result],'danger'])
    return openPorts

# Thread to run the scan
def urlScanIOThread(uuid, logId):
    # Once a scan has been initiated, we wait 5 seconds for urlscan.io to have a result ready,
    # after that we poll every 2 seconds until we get a result. Timeout at one minute.
    db = sqlite3.connect('instance/endstat.sqlite')
    time.sleep(5)
    retries = 30
    result = requests.get(f"https://urlscan.io/api/v1/result/{uuid}/")
    while result.status_code != 200:
        time.sleep(2)
        result = requests.get(f"https://urlscan.io/api/v1/result/{uuid}/")
        retries -= 1
        if retries == 0:
            return None
    resultJson = result.json()

    #General
    if 'server' in resultJson['page']: webServer = resultJson['page']['server']
    else: webServer = "N/A"

    if 'ip' in resultJson['page']: ip = resultJson['page']['ip']
    else: ip = "N/A"

    screenshot = resultJson['task']['screenshotURL']
    generalDict = {'webServer': webServer, 'ip': ip, 'screenshot': screenshot}

    #SSL
    if len(resultJson['stats']['tlsStats']) > 0: sslStatus = resultJson['stats']['tlsStats'][0]['securityState']
    else: sslStatus = "N/A"

    if len(resultJson['lists']['certificates']) > 0: 
        sslExpiry = resultJson['lists']['certificates'][0]['validTo']
        sslExpiryDaysLeft = int(re.sub("[^0-9]", "", str((datetime.now().date() - datetime.fromtimestamp(sslExpiry).date()).days)))
    else: sslExpiryDaysLeft = 0

    sslDict = {'sslStatus': sslStatus, 'sslExpiry': sslExpiryDaysLeft}

    #Safety
    malicious = resultJson['stats']['malicious']
    securePercentage = resultJson['stats']['securePercentage']
    verdicts = resultJson['verdicts']['overall']['score']
    safetyDict = {'malicious': malicious, 'securePercentage': securePercentage, 'verdicts': verdicts}

    if sslStatus != "secure" or sslExpiryDaysLeft < 7 or malicious is True:
        status = "Critical"
    else: status = "Normal" 

    db.execute('UPDATE website_log SET status = ?,general = ?,ssl = ?,safety = ?  WHERE id = ?', (status, json.dumps(generalDict), json.dumps(sslDict), json.dumps(safetyDict), logId))
    db.commit()

# Submit a scan request to urlscan.io, then run a thread to get the results later. Pass through db as thread will be out of app context.
def urlScanIO(domain, logId):
    headers = {'API-Key':f'{current_app.config["URLIO_API"]}','Content-Type':'application/json'}
    data = {"url": f"{domain}", "visibility": "public"}
    request = requests.post('https://urlscan.io/api/v1/scan/', headers=headers, data=json.dumps(data)).json()
    try:
        uuid = request['uuid']
        thread = Thread(target=urlScanIOThread, args=(uuid, logId))
        thread.start()
    except KeyError as e:
        print(e)

# Add all results to dict and return
def websiteScanner(websiteId, domain):
    db = get_db()
    # Make a new website log entry
    db.execute('INSERT INTO website_log (date_time, website_id) VALUES (?, ?)', (datetime.now(), websiteId))
    db.commit()
    # Select the id of the newly made log entry
    logId = db.execute('SELECT id FROM website_log WHERE website_id = ? AND id = (SELECT MAX(id) FROM website_log)', (websiteId,)).fetchone()[0]

    # Run the url and port scanners
    urlScanIO(domain, logId)
    # Wait some time for urlscan.io to process the request.
    time.sleep(3)
    openPorts = portScan(domain)

    db.execute('UPDATE website_log SET ports = ? WHERE id = ?', (json.dumps(openPorts), int(logId)))
    db.commit()