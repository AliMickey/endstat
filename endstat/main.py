from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, send_file
)
from endstat.db import get_db
from endstat.auth import login_required
from werkzeug.security import check_password_hash, generate_password_hash
import endstat.notifications as notif

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
    return render_template('websites/website-list.html')


@bp.route('/websites/add-website', methods=('GET', 'POST'))
@login_required
def addWebsite():
    error = None
    db = get_db()
    if request.method == 'POST':
        url = request.form['url']
        certificate = request.form['certificate']

    return render_template('websites/add-website.html')


@bp.route('/profile', methods=('GET', 'POST'))
@login_required
def profileSettings():
    error = None
    db = get_db()  
    userDetails = db.execute('SELECT id, password, email FROM users WHERE id = ?', (g.user['id'],)).fetchone()
    if request.method == 'POST':
        if request.form["btn"] == "user":
            first_name = request.form['first_name']
            email = request.form['email']
            if (first_name):
                db.execute(
                'UPDATE users SET first_name = ? WHERE id = ?', (first_name, userDetails['id']))
                db.commit()
            if (email):
                db.execute(
                'UPDATE users SET email = ? WHERE id = ?', (email, userDetails['id']))
                db.commit()
                notif.send_email(userDetails['email'], "End Stat Password Reset", f"Letting you know that your email was changed to '{email}'")
            session.clear()
            return redirect(url_for('auth.login'))
            
        elif request.form["btn"] == "password":
            current_password = request.form['current_password']
            password = request.form['password']
            password_repeat = request.form['password_repeat']

            if not current_password or not password or not password_repeat:
                error = "All fields are required."
            elif check_password_hash(userDetails['password'], current_password):
                error = "Current password is incorrect."
            elif len(password) < 8:
                error = 'Password is shorter than 8 characters.'
            elif password != password_repeat:
                error = "New passwords do not match."
           
            if error is None:
                db.execute('UPDATE users SET password = ? WHERE id = ?', (generate_password_hash(password), userDetails['id']))
                db.commit()
                notif.send_email(userDetails['email'], "End Stat Password Reset", "Letting you know that your password was reset.")
                session.clear()
                return redirect(url_for('auth.login'))

    return render_template('profile-settings.html', error=error, currentEmail=userDetails['email'])


# Error views
@bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('error/404.html'), 404

@bp.app_errorhandler(403)
def authorisation_error(e):
    return render_template('error/403.html'), 403