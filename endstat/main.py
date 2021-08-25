from flask import (
    Blueprint, g, redirect, render_template, request, url_for
)
import endstat.notifications as notif
from endstat.db import get_db
from endstat.auth import login_required

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