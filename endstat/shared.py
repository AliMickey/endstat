from flask import g
import pytz, json, sqlite3
from datetime import datetime

# App imports
from endstat.db import get_db

# Convert db utc time to local user settings timezone
def convertToUserTime(dateTime, userId):
    db = get_db()
    userTimeZone = db.execute('SELECT time_zone FROM users WHERE id = ?', (userId,)).fetchone()[0]
    utcDateTime = datetime.strptime(dateTime, "%Y-%m-%d %H:%M:%S")
    try:
        convDateTime = pytz.timezone("UTC").localize(utcDateTime).astimezone(pytz.timezone(userTimeZone))
    except pytz.UnknownTimeZoneError:
        convDateTime = utcDateTime
    convDate = convDateTime.strftime("%d/%m/%Y %H:%M")
    return convDate

# Parse scan results into dict
def loadScanResults(websiteLog, websiteId):
    db = get_db()
    scanResults = {}
    # Map and convert row data into dictionaries/strings
    scanResults['domain'] = db.execute('SELECT domain FROM websites WHERE id = ?', (websiteId,)).fetchone()[0]
    scanResults['dateTime'] = convertToUserTime(websiteLog[0], g.user['id'])
    scanResults['websiteId'] = websiteId
    scanResults['status'] = websiteLog[1]
    scanResults['general'] = json.loads(websiteLog[2])
    scanResults['ssl'] = json.loads(websiteLog[3])
    scanResults['safety'] = json.loads(websiteLog[4])
    scanResults['ports'] = json.loads(websiteLog[5])
    return scanResults

# Convert alert type to respective icon
def getAlertIcon(type):
    if (type == "primary"): return "check"
    elif (type == "warning"): return "asterisk"
    elif (type == "danger"): return "exclamation-triangle"

# Add an alert for specified user
def addAlert(userId, type, alert):
    db = sqlite3.connect('instance/endstat.sqlite')
    db.execute('INSERT INTO user_alerts (date_time, type, message, read, user_id) VALUES (?, ?, ?, ?, ?)', 
            (datetime.utcnow(), type, alert, 0, userId))
    db.commit()
    db.close()