from typing import Type
from flask import (
    Blueprint, g, redirect, render_template, request, url_for, current_app
)
import validators, datetime, json
from endstat.db import get_db
from werkzeug.exceptions import abort
from endstat.auth import login_required, checkWebsiteAuthentication
from endstat.notifications import sendNotification
from endstat.profile import getAlertIcon
from endstat.scanner import websiteScanner

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
            protocol = request.form.get('protocol')

            if not domain or not validators.domain(domain):
                error = "A valid URL is required"
            elif db.execute('SELECT EXISTS(SELECT 1 FROM websites WHERE user_id = ? AND domain = ?)', (g.user['id'], domain)).fetchone()[0]:
                error = "This website already exists."

            if error is None:
                db.execute(
                        'INSERT INTO websites (domain, protocol, user_id) VALUES (?, ?, ?)', 
                            (domain, protocol, g.user['id']))
                db.commit()
                websiteId = db.execute('SELECT id FROM websites WHERE domain = ? AND user_id = ?', (domain, g.user['id'])).fetchone()['id']
                websiteScanner(websiteId, domain)
                return redirect(url_for('websites.websiteList'))

        elif request.form["btn"] == "deleteWebsite":
            domainID = request.form['domainID']
            db.execute('DELETE FROM websites WHERE id = ? AND user_id = ?', (domainID, g.user['id']))
            db.commit()
            db.execute('DELETE FROM website_log WHERE website_id = ?', (domainID,))
            db.commit()
            db.execute('DELETE FROM user_alerts WHERE website_id = ?', (domainID,))
            db.commit()
            return redirect(url_for('websites.websiteList'))
        
    websitesDB = db.execute('SELECT domain, protocol, id FROM websites WHERE user_id = ?', (g.user['id'],)).fetchall()
    for row in websitesDB:
        domain, protocol, id = row
        websiteDict[domain] = [id, protocol]
        
    return render_template('websites/website-list.html', error=error, websites=websiteDict)

# View for viewing website specific logs
@bp.route('/view/<int:websiteId>', methods=('GET', 'POST'))
@login_required
def viewWebsite(websiteId):
    db = get_db()
    if checkWebsiteAuthentication(websiteId):
        # Get latest website scan results
        websitesDB = db.execute('SELECT datetime(date_time), status, general, ssl, safety, ports FROM website_log WHERE website_id = ? AND id = (SELECT MAX(id) FROM website_log)', 
            (int(websiteId),)).fetchone()

        # Map and convert row data into dictionaries/strings
        domain = db.execute('SELECT domain FROM websites WHERE id = ?', (websiteId,)).fetchone()[0]
        try:
            dateTime = datetime.datetime.strptime(websitesDB[0], "%Y-%m-%d %H:%M:%S").date().strftime("%d/%m/%Y")
            status = websitesDB[1]
            general = json.loads(websitesDB[2])
            ssl = json.loads(websitesDB[3])
            safety = json.loads(websitesDB[4])
            ports = json.loads(websitesDB[5])
        except TypeError as e:
            print(f"{e}. Error found at viewWebsite() in websites.py")
            return render_template('error/general.html', 
                error="""
                    There was an error with loading the website scan results.
                    If this is the first scan, please wait for around 10 seconds then try again.
                    Otherwise, send an email to 'mail@endstat.com' to let us know.
                    """)

        return render_template('websites/website.html', domain=domain, dateTime=dateTime, status=status, general=general, ssl=ssl, safety=safety, ports=ports) 
    
    else:
        abort(403)

# View for managing website specific settings
@bp.route('/settings/<int:websiteId>')
@login_required
def websiteSettings(websiteId):
    db = get_db()