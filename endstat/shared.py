import pytz
from datetime import datetime

# App imports
from endstat.db import get_db

# Convert db utc time to local user settings timezone
def convertToUserTime(dateTime, userId):
    db = get_db()
    userTimeZone = db.execute('SELECT time_zone FROM users WHERE id = ?', (userId,)).fetchone()[0]
    db.close()
    utcDateTime = datetime.strptime(dateTime, "%Y-%m-%d %H:%M:%S")
    try:
        convDateTime = pytz.timezone("UTC").localize(utcDateTime).astimezone(pytz.timezone(userTimeZone))
    except pytz.UnknownTimeZoneError:
        convDateTime = utcDateTime
    convDate = convDateTime.strftime("%d/%m/%Y %H:%M")
    return convDate