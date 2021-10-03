from flask import (
    Blueprint, g, redirect, render_template, request, session, url_for
)
import functools, uuid, validators
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

# App imports
from endstat.db import get_db
from endstat.notifications import sendEmail

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Global authentication checker
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

# View to register a new user
@bp.route('/register', methods=('GET', 'POST'))
def register():
    error = None
    if request.method == 'POST':
        first_name = request.form['first_name']
        email = request.form['email']
        password = request.form['password']
        password_repeat = request.form['password_repeat']
        db = get_db()
        tempUserID = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone() 
        
        if tempUserID is not None:
            error = f'"{email}" is already registered.'
        elif not first_name:
            error = 'First name is required.'
        elif not email or not validators.email(email):
            error = 'Valid email is required.'
        elif len(password) < 8:
            error = 'Password is shorter than 8 characters.'
        elif not password:
            error = 'Password is required.'
        elif password != password_repeat:
            error = 'Passwords do not match.'

        if error is None:
            # Create user
            db.execute(
                'INSERT INTO users (first_name, email, password, time_zone) VALUES (?, ?, ?, ?)', (first_name, email, generate_password_hash(password), "Australia/Sydney"))
            db.commit()
            userID = int(db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()[0])
            # Add default notification settings
            db.execute(
                'INSERT INTO notification_settings (email, email_enabled, discord_enabled, user_id) VALUES (?, ?, ?, ?)', 
                    (email, 1, 0, userID))
            db.commit()
            # Add first user alert
            db.execute(
                'INSERT INTO user_alerts (date_time, type, message, read, user_id) VALUES (?, ?, ?, ?, ?)', 
                    (datetime.utcnow(), "primary", "Welcome to End Stat, we hope you enjoy it!", 0, userID))
            db.commit()
            db.close()
            #TEMPDISABLE sendNotification(userID, "Thanks for trying out End Stat, this is an email to confirm that your account has been created. Head over to https://endstat.com if you haven't already!")
            return redirect(url_for('auth.login'))

    return render_template('auth/register.html', error=error)

# View to login to the system
@bp.route('/login', methods=('GET', 'POST'))
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()   
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        db.close()
        if user is None or not check_password_hash(user['password'], password):
            error = 'Incorrect email or password. Please try again.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('main.dashboard'))

    return render_template('auth/login.html', error=error)

# View to request a new password link
@bp.route('/forgot-password', methods=('GET', 'POST'))
def forgotPassword():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        db = get_db()   
        # Get user id for email if exists
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if user is not None:
            userID = user['id']
            # Check if user has used key or has already requested for a password reset within last 24 hours
            resetPassDetails = db.execute('SELECT reset_key, datetime(date_time), activated FROM reset_pass WHERE user_id = ?', (userID,)).fetchone()
            # Send the same key again
            if (resetPassDetails and checkPasswordResetValidity(resetPassDetails[1], resetPassDetails['activated'])):
                resetKey = resetPassDetails['reset_key']

            else:
                # Generate and send a new key
                resetKey = uuid.uuid4()
                db.execute('INSERT INTO reset_pass (reset_key, user_id, date_time, activated) VALUES (?, ?, ?, ?) ', 
                    (str(resetKey), userID, datetime.now(), False))
                db.commit()
                db.close()
            sendEmail(email, f"Use the following link to reset your password for EndStat. https://endstat.com/auth/reset-password/{resetKey}")
        error = "If your email exists in our system, you will receive an email soon with instructions. Check your spam if you do not see it."

    return render_template('auth/forgot-password.html', error=error)

# View to reset password via uuid
@bp.route('/reset-password/<string:resetKey>', methods=('GET', 'POST'))
def resetPassword(resetKey):
    error = None
    db = get_db()          
    resetPassDetails = db.execute('SELECT user_id, datetime(date_time), activated FROM reset_pass WHERE reset_key = ?', (resetKey,)).fetchone()
    if request.method == 'GET':
        if (resetPassDetails and checkPasswordResetValidity(resetPassDetails[1], resetPassDetails['activated'])): 
            return render_template('auth/reset-password.html', resetKey=resetKey)
        else:
            return render_template('error/general.html', error="Either the url is no longer valid, or you are here by mistake.")

    if request.method == 'POST':
        if (resetPassDetails and checkPasswordResetValidity(resetPassDetails[1], resetPassDetails['activated'])):
            password = request.form['password']
            password_repeat = request.form['password_repeat']
            if not password:
                error = 'Password is required.'
            elif not password_repeat:
                error = 'Password Repeat is required.'
            elif password != password_repeat:
                error = 'Passwords do not match.'
            if error is None:
                db.execute(
                    'UPDATE users SET password = ? WHERE id = ?',
                    (generate_password_hash(password), resetPassDetails['user_id']))
                db.execute(
                    'UPDATE reset_pass SET activated = 1 WHERE reset_key = ?',
                    (resetKey,))
                db.commit() 
                sendEmail(db.execute('SELECT email FROM users WHERE id = ?', (resetPassDetails['user_id'],)).fetchone()[0], "Letting you know that your password was reset.")
                db.close()
                session.clear()
                return redirect(url_for('auth.login'))
    
    return render_template('auth/reset-password.html', error=error)       

# View to clear session
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))

# Function to check if reset password key is still valid       
def checkPasswordResetValidity(genTime, activated):
    generatedDateTime = datetime.strptime(genTime, "%Y-%m-%d %H:%M:%S")
    nowDateTime = datetime.now()
    # Calculate time period between present and key generation
    diffSeconds = ((nowDateTime.hour * 60 + nowDateTime.minute) * 60 + nowDateTime.second) - ((generatedDateTime.hour * 60 + generatedDateTime.minute) * 60 + generatedDateTime.second)
    if (activated == 0 and diffSeconds < 86400):
        return True        
    return False 

# Check if a given website id is owned by the current user.
def checkWebsiteAuthentication(websiteId):
    db = get_db()
    exists = db.execute('SELECT EXISTS(SELECT 1 FROM websites WHERE user_id = ? AND id = ?)', (g.user['id'], websiteId)).fetchone()[0]
    db.close()
    if exists:
        return True
    return False

# Set g.user['id'] to id of user in db
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None: g.user = None
    else: g.user = get_db().execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()