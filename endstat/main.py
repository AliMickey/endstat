from flask import (
    Blueprint, g, redirect, render_template, request, url_for
)
from datetime import datetime
import json

# App imports
from endstat.auth import login_required
from endstat.db import get_db
from endstat.profile import getAlertIcon
from endstat.websites import loadScanResults

bp = Blueprint('main', __name__)

# Main view for website information
@bp.route('/')
def index():
    return render_template('main/index.html')

# View for user dashboard
@bp.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    totalSecurityRating = 0
    totalSecurityCounter = 0
    latestScan = [None, None]
    previousScans = []
    soonestExpiry = [None, None]
    websiteUsage = 0

    # Get all websits for user
    userWebsitesDb = db.execute('SELECT id, domain FROM websites WHERE user_id = ?', (g.user['id'],)).fetchall()
    websiteUsage = len(userWebsitesDb)
    if websiteUsage == 0:
        return render_template('error/general.html', error="You do not seem to have any websites added, come back here once you have.")

    for website in userWebsitesDb:
        # Get past 5 logs for website
        websiteLogs = db.execute('SELECT datetime(date_time), status, general, ssl, safety, ports from website_log WHERE website_id = ? ORDER BY datetime(date_time) DESC Limit 5', (website[0],)).fetchall()
        for log in websiteLogs:
            # Get latest scan out of all logs
            if latestScan[0] is not None:
                if log[0] > latestScan[0][0]:
                    previousScans.append([latestScan[0], latestScan[1]])
                    latestScan[0] = log
                    latestScan[1] = website[0]
                else:
                    previousScans.append([log, website[0]])
            else:
                latestScan[0] = log
                latestScan[1] = website[0]

            if log['ssl'] is None:
                return render_template('error/general.html', error="Your dashboard is not quite ready yet, come back after a scan has been completed.")

            # Get soonest cert expiry of all logs
            ssl = json.loads(log['ssl']) 
            currentExpiry = int(ssl['sslExpiry'])
            if soonestExpiry[0] is None:
                soonestExpiry[0] = currentExpiry
                soonestExpiry[1] = website[1]
            else:
                if soonestExpiry[0] > currentExpiry:
                    soonestExpiry[0] = currentExpiry
                    soonestExpiry[1] = website[1]

            # Get safety rating for log and add to master var
            safety = json.loads(log['safety'])
            totalSecurityRating += int(safety['securePercentage'])
            totalSecurityCounter += 1

        # Sort previous 4 scans and pass as dict
        sortedPreviousScans = sorted(previousScans, key=lambda t: datetime.strptime(t[0][0], '%Y-%m-%d %H:%M:%S'))
        next4Scans = []
        for log in sortedPreviousScans:
            next4Scans.append(loadScanResults(log[0], log[1]))
        next4Scans.reverse()

        # Get average security rating
        averageRatingPercentage = int(totalSecurityRating/totalSecurityCounter)  

    return render_template('main/dashboard.html', latestScan=loadScanResults(latestScan[0], latestScan[1]), averageRatingPercentage=averageRatingPercentage, soonestExpiry=soonestExpiry, websiteUsage=websiteUsage, next4Scans=next4Scans[:4])

# View for privacy policy
@bp.route('/privacy-policy')
def privacyPolicy():
    return render_template('main/privacy-policy.html')

# View for terms and conditions
@bp.route('/terms-and-conditions')
def termsAndConditions():
    return render_template('main/terms-and-conditions.html')

# 404 page not found error
@bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('error/404.html'), 404

# 403 authorisation error
@bp.app_errorhandler(403)
def authorisation_error(e):
    return render_template('error/403.html'), 403

# Supply each page view with unread user alerts.
@bp.app_context_processor
def injectNavDetails():
    db = get_db()
    if (g.user):
        navDetailsDict = {}
        navDetailsDB = db.execute('SELECT message, datetime(date_time), type, id FROM user_alerts WHERE user_id = ? AND read = 0', (g.user['id'],)).fetchall()
        for row in navDetailsDB:
            message, dateTime, type, id = row
            conv_date = datetime.strptime(dateTime, "%Y-%m-%d %H:%M:%S").date().strftime("%d/%m/%Y")
            icon = getAlertIcon(type)
            navDetailsDict[message] = [conv_date, icon, id]
        return dict(navDetails=navDetailsDict)
    return dict(navDetails={"None":"None"})