from flask import current_app
import socket, threading, json, requests, time, sqlite3, re
from datetime import datetime
from queue import Queue
from threading import Thread
from urllib.request import socket

#App imports
from endstat.notifications import sendNotification
from endstat.shared import addAlert

print_lock = threading.Lock()
socket.setdefaulttimeout(0.2)

scanPorts = { 20: ['ftp', 'warn'], 21: ['ftp', 'warn'], 22: ['ssh', 'danger'], 23: ['telnet', 'warn'], 25: ['smtp', 'warn'], 53: ['dns', 'danger'], 80: ['http', 'safe'], 
    110: ['pop', 'warn'], 139: ['NetBIOS', 'danger'], 443: ['https', 'safe'], 445: ['smb', 'danger'], 853: ['DoT', 'safe'], 1433: ['MSSQL', 'danger'], 
    1521: ['Oracle DB', 'danger'], 3306: ['MySQL', 'danger'], 3389: ['RDP', 'danger'], 32400: ['Plex', 'safe'] }

# Open port scanner
def portScanThread(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try: 
        result = sock.connect_ex((ip, port))
        sock.settimeout(0.2)
        if result == 0:
            return port
        sock.close()
    except socket.error:
        return None
    except socket.timeout:
        return None

# Return all open ports on domain with multi-threading
def portScan(domain, userId):
    threadsList = list()
    que = Queue() 
    openPorts = []
    remoteServerIP = socket.gethostbyname(domain) # Get ip for provided domain
    for port in scanPorts:
        thread = Thread(target=lambda q, arg1,arg2: q.put(portScanThread(arg1,arg2)), args=(que, remoteServerIP, port))
        thread.start()
        threadsList.append(thread)
    for t in threadsList:
        t.join()
    while not que.empty():
        result = que.get()
        if result is not None:
            portDict = scanPorts[result]
            openPorts.append([result, portDict[0], portDict[1]])
            if portDict[1] == "danger":
                addAlert(userId, "danger", f"Port '{result}' was detected as open on {domain}.")
    return openPorts

# Thread to run the scan
def urlScanIOThread(uuid, logId, userId):
    # Once a scan has been initiated, we wait 5 seconds for urlscan.io to have a result ready,
    # after that we poll every 2 seconds until we get a result. Timeout at 40 seconds.
    time.sleep(5)
    db = sqlite3.connect('instance/endstat.sqlite')
    retries = 20
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
        sslExpiryDaysLeft = int(re.sub("[^0-9]", "", str((datetime.utcnow().date() - datetime.fromtimestamp(sslExpiry).date()).days)))
    else: sslExpiryDaysLeft = 0

    sslDict = {'sslStatus': sslStatus, 'sslExpiry': sslExpiryDaysLeft}

    #Safety
    malicious = resultJson['stats']['malicious']
    securePercentage = resultJson['stats']['securePercentage']
    verdicts = resultJson['verdicts']['overall']['score']
    safetyDict = {'malicious': malicious, 'securePercentage': securePercentage, 'verdicts': verdicts}

    if sslStatus != "secure" or sslExpiryDaysLeft < 7 or malicious is True:
        db.execute('UPDATE website_log SET status = ? WHERE id = ?', ("Critical", logId))
        db.commit()
        addAlert(userId, "danger", f"A recent scan has resulted in a critical result.")

    db.execute('UPDATE website_log SET general = ?,ssl = ?,safety = ?  WHERE id = ?', (json.dumps(generalDict), json.dumps(sslDict), json.dumps(safetyDict), logId))
    db.commit()
    db.close()

# Submit a scan request to urlscan.io, then run a thread to get the results later. Pass through db as thread will be out of app context.
def urlScanIO(domain, logId, userId, api=None):
    if api is None:
        URLIOAPI = current_app.config["URLIO_API"]
    else:
        URLIOAPI = api
    headers = {'API-Key':URLIOAPI,'Content-Type':'application/json'}
    data = {"url": f"{domain}", "visibility": "unlisted"}
    request = requests.post('https://urlscan.io/api/v1/scan/', headers=headers, data=json.dumps(data)).json()
    if 'status' in request and request['status'] == 400:
        print(f"Blacklist prevented scan for {domain}")
        return None
    try:
        uuid = request['uuid']
        thread = Thread(target=urlScanIOThread, args=(uuid, logId, userId))
        thread.start()
    except KeyError as e:
        print(e)

# Main function to scan a website and add results to database
def websiteScanner(websiteId, domain, userId, apis=None):
    db = sqlite3.connect('instance/endstat.sqlite')
    # Make a new website log entry
    db.execute('INSERT INTO website_log (date_time, website_id, status) VALUES (?, ?, ?)', (datetime.utcnow(), websiteId, "Normal"))
    db.commit()
    # Select the id of the newly made log entry
    logId = db.execute('SELECT id FROM website_log WHERE website_id = ? AND id = (SELECT MAX(id) FROM website_log)', (websiteId,)).fetchone()[0]
    
    # Check if apis are passed to thread, otherwise use app config
    urlApi = None
    mailApi = None
    if apis is not None:
        urlApi = apis[0]
        mailApi = apis[1]

    # Run the url and port scanners
    urlScanIO(domain, logId, userId, urlApi)
    openPorts = portScan(domain, userId)
    for port in openPorts:
        if 'danger' in port:
            db.execute('UPDATE website_log SET status = ? WHERE id = ?', ('Critical', int(logId)))
            db.commit()
            break

    # Wait some time for scans to finish while giving user scanning animation.
    time.sleep(12)
    db.execute('UPDATE website_log SET ports = ? WHERE id = ?', (json.dumps(openPorts), int(logId)))
    db.commit()
    db.close()

    sendNotification(userId, f"Scan completed for {domain}.\nView it at https://endstat.com/websites/view/{websiteId}", mailApi)