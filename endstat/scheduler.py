import schedule
from datetime import datetime
from threading import Thread
from time import sleep

# App imports
from endstat.db import get_db
from endstat.scanner import websiteScanner

# Get time for each website and init a job for each website.
def schedInitJobs():
    db = get_db()
    # Get all websites
    websitesDB = db.execute('SELECT id, domain, datetime(scan_time) FROM websites').fetchall()
    # For each website, add a job to run a website scan at the specified time
    for row in websitesDB:
        id, domain, scanTime = row
        convDate = datetime.strptime(scanTime, "%Y-%m-%d %H:%M:%S").time().strftime("%H:%M")
        schedule.every().day.at(convDate).do(websiteScanner, websiteId=id, domain=domain).tag(id)
        print(f"Website id: {id}, domain: {domain} scheduled for {convDate}")
    thread = Thread(target=schedPendingRunner)
    thread.start()

# Add a new job to the scheduler
def schedAddJob(websiteId, domain):
    schedule.every().day.at(datetime.now().strftime("%H:%M")).do(websiteScanner, websiteId=websiteId, domain=domain).tag(websiteId)

# Remove a job from the scheduler
def schedRemoveJob(websiteId):
    # Remove the scheduled job for the given website by tag
    schedule.clear(websiteId)

# Runs all pending schedule jobs - runs every minute
def schedPendingRunner():
    while True:
        schedule.run_pending()
        sleep(60)