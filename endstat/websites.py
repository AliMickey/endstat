from flask import (
    Blueprint, g, redirect, render_template, request, url_for, current_app
)
import validators, json
from datetime import datetime
from werkzeug.exceptions import abort

# App imports
from endstat.auth import login_required, checkWebsiteAuthentication
from endstat.db import get_db
from endstat.notifications import sendNotification
from endstat.scanner import websiteScanner
from endstat.scheduler import schedAddJob, schedRemoveJob
from endstat.shared import convertToUserTime

bp = Blueprint('websites', __name__, url_prefix='/websites')

# View for listing all websites
@bp.route('/', methods=('GET', 'POST'))
@login_required
def websiteList():
    error = None
    db = get_db()
    websiteDict = {}

    if request.method == 'POST':
        if request.form["btn"] == "addWebsite":
            domain = request.form['domain']

            # Check if website input is valid and if it exists
            if not domain or not validators.domain(domain):
                error = "A valid domain is required. Do not include https or any trailing paths."
            elif db.execute('SELECT EXISTS(SELECT 1 FROM websites WHERE user_id = ? AND domain = ?)', (g.user['id'], domain)).fetchone()[0]:
                error = "This website already exists."
            elif db.execute('SELECT Count(id) FROM websites WHERE user_id = ?', (g.user['id'],)).fetchone()[0] == 5:
                error = "You have reached your 5 website limit. Either delete some websites or upgrade by using the donate link under your profile button."

            if error is None:
                db.execute(
                        'INSERT INTO websites (domain, user_id, scan_time) VALUES (?, ?, ?)', 
                            (domain, g.user['id'], datetime.utcnow()))
                db.commit()
                # Get id for newly added website
                websiteId = db.execute('SELECT id FROM websites WHERE user_id = ? AND domain = ?', (g.user['id'], domain)).fetchone()['id']
                # Add new job and run initial scan
                schedAddJob(websiteId, domain, datetime.utcnow(), g.user['id'])
                websiteScanner(websiteId, domain, g.user['id'])
                return redirect(url_for('websites.websiteList'))

        # Remove all instances of website from database
        elif request.form["btn"] == "deleteWebsite":
            websiteId = request.form['websiteId']
            db.execute('DELETE FROM websites WHERE id = ? AND user_id = ?', (websiteId, g.user['id']))
            db.commit()
            db.execute('DELETE FROM website_log WHERE website_id = ?', (websiteId,))
            db.commit()
            db.execute('DELETE FROM user_alerts WHERE website_id = ?', (websiteId,))
            db.commit()
            schedRemoveJob(websiteId)
            return redirect(url_for('websites.websiteList'))
        
    # Get data for user's websites
    websitesDB = db.execute('SELECT domain, id FROM websites WHERE user_id = ?', (g.user['id'],)).fetchall()
    for row in websitesDB:
        domain, id = row
        websiteLog = db.execute('SELECT datetime(date_time), status FROM website_log WHERE id = (SELECT MAX(id) FROM website_log WHERE website_id = ?)', (int(id),)).fetchone()
        if websiteLog: 
            dateTime = convertToUserTime(websiteLog[0], g.user['id'])
            status = websiteLog[1]
        else: 
            dateTime = "Error"
            status = "Error"
        websiteDict[domain] = [id, dateTime, status]
    
    return render_template('websites/website-list.html', error=error, websites=websiteDict)

# View for viewing website specific logs
@bp.route('/view/<int:websiteId>', methods=('GET', 'POST'))
@login_required
def viewWebsite(websiteId):
    db = get_db()
    if checkWebsiteAuthentication(websiteId):
        # Get latest website scan results
        websitesDB = db.execute('SELECT datetime(date_time), status, general, ssl, safety, ports FROM website_log WHERE id = (SELECT MAX(id) FROM website_log WHERE website_id = ?)', 
            (int(websiteId),)).fetchone()
        
        # Try to load data in, if data is not yet ready show an error.
        try:
            websiteDict = loadScanResults(websitesDB, websiteId)
        except TypeError as e:
            print(f"{e}: Error found at viewWebsite() in websites.py")
            return render_template('error/general.html', 
                error="""
                    There was an error with loading the website scan results.
                    If this is the first scan, please wait for around 5 seconds then try again.
                    Otherwise, send an email to 'endstat@mickit.net' to let us know.
                    """)
        return render_template('websites/website.html', websiteDict=websiteDict) 
    else:
        abort(403)

# View for managing website specific settings
@bp.route('/settings/<int:websiteId>')
@login_required
def websiteSettings(websiteId):
    db = get_db()

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