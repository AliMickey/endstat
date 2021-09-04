import socket, threading, sys, json, datetime
from queue import Queue
from threading import Thread
from urllib.request import ssl, socket
from pysafebrowsing import SafeBrowsing
from flask import current_app

print_lock = threading.Lock()
socket.setdefaulttimeout(0.2)

# Open port scanner
def portScanThread(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try: 
        result = sock.connect_ex((ip, port))
        if result == 0:
            return port
        sock.close()
    except socket.error:
        sys.exit()
    except KeyboardInterrupt: #dev temp
        sys.exit()

# Return all open ports on domain with multi-threading
def portScan(domain):
    threadsList = list()
    que = Queue() 
    openPorts = []
    remoteServerIP = socket.gethostbyname(domain) # Get ip for provided domain
    for x in range(65535):
        thread = Thread(target=lambda q, arg1,arg2: q.put(portScanThread(arg1,arg2)), args=(que, remoteServerIP, x))
        thread.start()
        threadsList.append(thread)
    for t in threadsList:
        t.join()
    while not que.empty():
        result = que.get()
        if result is not None:
            openPorts.append(result)
    print(openPorts)

# Return expiry date of ssl certificate on domain
def sslCheck(domain):
    context = ssl.create_default_context()
    with socket.create_connection((domain, 443)) as sock:
        with context.wrap_socket(sock, server_hostname=domain) as ssock:
            print(ssock.version())
            data = json.loads(json.dumps(ssock.getpeercert()))
    return (datetime.datetime.strptime(data["notAfter"], r'%b %d %H:%M:%S %Y %Z'))

# Return google's safe browsing api check on domain 
def safetyCheck(domain):
    api = SafeBrowsing(current_app.config['GOOGLE_API'])
    check = api.lookup_urls([domain])[domain]
    if (check['malicious']):
        return True, check['threats']
    return False