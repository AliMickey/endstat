from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, send_file
)
from endstat.db import get_db
from endstat.auth import login_required
from werkzeug.security import check_password_hash, generate_password_hash

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
    if request.method == 'POST':
        url = request.form['url']
        certificate = request.form['certificate']

    return render_template('websites/add-website.html')


@bp.route('/profile', methods=('GET', 'POST'))
@login_required
def profileSettings():
    error = None
    db = get_db()  
    if request.method == 'POST':
        if request.form["btn"] == "user":
            first_name = request.form['first_name']
            email = request.form['first_name']
            if (first_name):
                db.execute(
                'UPDATE users SET first_name = ? WHERE id = ?', (first_name, g.user['id']))
                db.commit()
            if (email):
                db.execute(
                'UPDATE users SET email = ? WHERE id = ?', (email, g.user['id']))
                db.commit()
            
        elif request.form["btn"] == "password":
            current_password = request.form['current_password']
            password = request.form['password']
            password_repeat = request.form['password_repeat']
            if not current_password or not password or not password_repeat:
                error = "All fields are required."
            elif password != password_repeat:
                error = "New passwords do not match"

            if error is None:
                userPassword = db.execute('SELECT password FROM users WHERE id = ?', (g.user['id'],)).fetchone()
                if (check_password_hash(userPassword[0], current_password)):
                    db.execute('UPDATE users SET password = ? WHERE id = ?', (generate_password_hash(password), g.user['id']))
                    db.commit()
            
    return render_template('profile-settings.html', error=error)


# Error views
@bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('error/404.html'), 404

@bp.app_errorhandler(403)
def authorisation_error(e):
    return render_template('error/403.html'), 403