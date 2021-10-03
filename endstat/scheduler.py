import schedule
from datetime import datetime
from threading import Thread
from time import sleep
from flask import current_app
# App imports
from endstat.db import get_db
from endstat.scanner import websiteScanner

# Get time for each website and init a job for each website.
def schedInitJobs():
    db = get_db()
    # Get all websites
    websitesDB = db.execute('SELECT id, domain, datetime(scan_time), user_id FROM websites').fetchall()
    # For each website, add a job to run a website scan at the specified time
    for row in websitesDB:
        id, domain, scanTime, userId = row
        schedAddJob(id, domain, scanTime, userId)
    thread = Thread(target=schedPendingRunner)
    thread.start()

# Add a new job to the scheduler
def schedAddJob(websiteId, domain, dateTime, userId):
    # Convert datetime to object if string
    if not isinstance(dateTime, datetime):
        dateTime = datetime.strptime(dateTime, "%Y-%m-%d %H:%M:%S")
    convDate = dateTime.time().strftime("%H:%M")
    apis = [current_app.config["URLIO_API"], current_app.config["ZOHO_API"]]
    schedule.every().day.at(convDate).do(websiteScanner, websiteId=websiteId, domain=domain, userId=userId, apis=apis).tag(websiteId)
    print(f"Website id: {websiteId}, domain: {domain} scheduled for {convDate}")

# Remove a job from the scheduler
def schedRemoveJob(websiteId):
    # Remove the scheduled job for the given website by tag
    schedule.clear(websiteId)

# Runs all pending schedule jobs - runs every minute
def schedPendingRunner():
    while True:
        schedule.run_pending()
        sleep(60)