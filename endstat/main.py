from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, send_file
)
from endstat.db import get_db
from endstat.auth import login_required

bp = Blueprint('main', __name__)

#Main views
@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@bp.route('/websites')
@login_required
def websiteList():
    return render_template('websites.html')


# Error views
@bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('error/404.html'), 404

@bp.app_errorhandler(403)
def authorisation_error(e):
    return render_template('error/403.html'), 403