from flask import (
    Blueprint, g, redirect, render_template, request, url_for
)
import endstat.notifications as notif
from endstat.db import get_db
from endstat.auth import login_required
from endstat.profile import getAlertIcon
import datetime

bp = Blueprint('main', __name__)

# Main view for website information
@bp.route('/')
def index():
    return render_template('index.html')

# View for user dashboard
@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# 404 page not found error
@bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('error/404.html'), 404

# 403 authorisation error
@bp.app_errorhandler(403)
def authorisation_error(e):
    return render_template('error/403.html'), 403


@bp.app_context_processor
def injectNavDetails():
    db = get_db()
    if (g.user):
        navDetailsDict = {}
        navDetailsDB = db.execute('SELECT message, datetime(date_time), type, id FROM user_alerts WHERE user_id = ? AND read = 0', (g.user['id'],)).fetchall()
        for row in navDetailsDB:
            message, dateTime, type, id = row
            conv_date = datetime.datetime.strptime(dateTime, "%Y-%m-%d %H:%M:%S").date().strftime("%d/%m/%Y")
            icon = getAlertIcon(type)
            navDetailsDict[message] = [conv_date, icon, id]
        return dict(navDetails=navDetailsDict)
    return dict(navDetails={"None":"None"})