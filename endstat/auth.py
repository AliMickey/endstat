import functools
from flask import (
    Blueprint, g, redirect, render_template, request, session, url_for
)
import validators
from werkzeug.security import check_password_hash, generate_password_hash
from endstat.db import get_db
import endstat.notifications as notif
import uuid, datetime

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Views
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

        if not first_name:
            error = 'First name is required.'
        elif not email or not validators.email(email):
            error = 'Valid email is required.'
        elif len(password) < 8:
            error = 'Password is shorter than 8 characters.'
        elif not password:
            error = 'Password is required.'
        elif password != password_repeat:
            error = 'Passwords do not match.'
        elif tempUserID is not None:
            error = '"{}" is already registered.'.format(email)

        if error is None:
            # Create user
            db.execute(
                'INSERT INTO users (first_name, email, password) VALUES (?, ?, ?)', (first_name, email, generate_password_hash(password)))
            db.commit()
            notif.send_email(email, "Welcome to End Stat", "Thanks for trying out End Stat, this is an email to confirm that your account has been created. Head over to https://endstat.com if you havn't already!")
            return redirect(url_for('auth.login'))

    return render_template('auth/register.html', error=error)


@bp.route('/login', methods=('GET', 'POST'))
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()   
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if user is None or not check_password_hash(user['password'], password):
            error = 'Incorrect email or password. Please try again.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('main.dashboard'))

    return render_template('auth/login.html', error=error)


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
            resetPassDetails = db.execute('SELECT reset_key, datetime(date_time), activated FROM resetPass WHERE user_id = ?', (userID,)).fetchone()
            # Send the same key again
            if (resetPassDetails and checkPasswordResetValidity(resetPassDetails[1], resetPassDetails['activated'])):
                resetKey = resetPassDetails['reset_key']

            else:
                # Generate and send a new key
                resetKey = uuid.uuid4()
                db.execute('INSERT INTO resetPass (reset_key, user_id, date_time, activated) VALUES (?, ?, ?, ?) ', 
                    (str(resetKey), userID, datetime.datetime.now(), False))
                db.commit()
                print("new key generated")

            notif.send_email(email, "Password Reset for EndStat", f"Use the following link to reset your password for EndStat. https://endstat.com/auth/reset-password/{resetKey}")
        
        error = "If your email exists in our system, you will receive an email soon with instructions. Check your spam if you do not see it."

    return render_template('auth/forgot-password.html', error=error)


@bp.route('/reset-password/<string:resetKey>', methods=('GET', 'POST'))
def resetPassword(resetKey):
    error = None
    db = get_db()          
    resetPassDetails = db.execute('SELECT user_id, datetime(date_time), activated FROM resetPass WHERE reset_key = ?', (resetKey,)).fetchone()
    if request.method == 'GET':
        if (resetPassDetails and checkPasswordResetValidity(resetPassDetails[1], resetPassDetails['activated'])): 
            return render_template('auth/reset-password.html', resetKey=resetKey)
        else:
            return render_template('error/general.html', "Either the url is no longer valid, or you are here by mistake.")

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
                print("done")
                db.execute(
                    'UPDATE users SET password = ? WHERE id = ?',
                    (generate_password_hash(password), resetPassDetails['user_id']))
                db.execute(
                    'UPDATE resetPass SET activated = ? WHERE reset_key = ?',
                    (1, resetKey))
                db.commit() 
                notif.send_email(db.execute('SELECT email FROM users WHERE id = ?', (resetPassDetails['user_id'],)).fetchone(), "End Stat Password Reset", "Letting you know that your password was reset.")
                session.clear()
                return redirect(url_for('auth.login'))

    return render_template('auth/reset-password.html', error=error)       


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))


# Functions        
def checkPasswordResetValidity(genTime, activated):
    generatedDateTime = datetime.datetime.strptime(genTime, "%Y-%m-%d %H:%M:%S")
    nowDateTime = datetime.datetime.now()
    diffSeconds = ((nowDateTime.hour * 60 + nowDateTime.minute) * 60 + nowDateTime.second) - ((generatedDateTime.hour * 60 + generatedDateTime.minute) * 60 + generatedDateTime.second)
    if (activated == 0 and diffSeconds < 86400):
        return True        
    return False 


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()




def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view