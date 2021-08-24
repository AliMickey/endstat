from flask import (
    Blueprint, g, redirect, render_template, request, session, url_for, send_file, current_app
)
import validators, datetime
from endstat.db import get_db
from werkzeug.exceptions import abort
from endstat.auth import login_required, checkWebsiteAuthentication
import endstat.notifications as notif


bp = Blueprint('websites', __name__)


@bp.route('/websites')
@login_required
def websiteList():
    db = get_db()
    websiteDict = {}
    websitesDB = db.execute('SELECT domain, protocol, id FROM websites WHERE user_id = ?', (g.user['id'],)).fetchall()
    for row in websitesDB:
        domain, protocol, id = row
        websiteDict[domain] = [protocol, id]

    return render_template('websites/website-list.html', websites=websiteDict)


@bp.route('/websites/add-website', methods=('GET', 'POST'))
@login_required
def addWebsite():
    error = None
    db = get_db()
    if request.method == 'POST':
        domain = request.form['domain']
        protocol = request.form.get('protocol')

        if not domain or not validators.domain(domain):
            error = "A valid URL is required"

        elif db.execute('SELECT EXISTS(SELECT 1 FROM websites WHERE user_id = ? AND domain = ?)', (g.user['id'], domain)).fetchone()[0]:
            error = "This website already exists."

        if error is None:
            certCheck = portCheck = blistCheck = 0
            if (request.form.get('certificate')): certCheck = 1
            if (request.form.get('ports')): portCheck = 1
            if (request.form.get('blacklists')): blistCheck = 1
            db.execute(
                    'INSERT INTO websites (domain, protocol, user_id, cert_check, ports_check, blacklists_check) VALUES (?, ?, ?, ?, ?, ?)', 
                        (domain, protocol, g.user['id'], certCheck, portCheck, blistCheck))
            db.commit()
            websiteId = db.execute('SELECT id FROM websites WHERE domain = ? AND user_id = ?', (domain, g.user['id'])).fetchone()['id']
            db.execute(
                    'INSERT INTO website_log (date_time, status, cert_expiry, ports_open, safety_check, website_id) VALUES (?, ?, ?, ?, ?, ?)', 
                        (datetime.datetime.now(), "N/A", "N/A", "N/A", "N/A", websiteId))
            db.commit()
            return redirect(url_for('websites.websiteList'))

    return render_template('websites/add-website.html', error=error)


@bp.route('/websites/view/<int:websiteId>', methods=('GET', 'POST'))
@login_required
def viewWebsite(websiteId):
    db = get_db()
    if checkWebsiteAuthentication(websiteId):
        # Get latest website scan results
        websitesDB = db.execute('SELECT * FROM website_log WHERE website_id = ? AND id = (SELECT MAX(id) FROM website_log)', 
            (int(websiteId),)).fetchone()
        domain = db.execute('SELECT domain FROM websites WHERE id = ?', (websiteId,)).fetchone()[0]
        
        return render_template('websites/website.html', website=websitesDB, domain=domain) 
    
    else:
        abort(403)


@bp.route('/websites/settings/<int:websiteId>')
@login_required
def websiteSettings(websiteId):
    db = get_db()