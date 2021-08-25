import socket, threading, sys, json, datetime
from urllib.request import ssl, socket
from pysafebrowsing import SafeBrowsing
from flask import current_app

print_lock = threading.Lock()
socket.setdefaulttimeout(0.2)

def portScanThread(domain, port):
    openPorts = []
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try: 
        remote_server_IP = socket.gethostbyname(domain)
        result = sock.connect_ex((remote_server_IP, port))
        if result == 0:
            openPorts.append(port)
            print(port)
        sock.close()
    except socket.error:
        print("Couldn't connect to host")
        sys.exit()
    except KeyboardInterrupt:
        sys.exit()

# Return all open ports on domain with multi-threading
def portScan(domain):
    for x in range(65535):
        thread = threading.Thread(target=portScan, args=(domain, x))
        thread.daemon = True
        thread.start()

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