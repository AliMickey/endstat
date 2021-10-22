from flask import (
    Blueprint, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
import pyotp

# App imports
from endstat.auth import login_required
from endstat.db import get_db
from endstat.notifications import sendNotification
from endstat.shared import convertToUserTime, getAlertIcon

bp = Blueprint('profile', __name__, url_prefix='/profile')

@bp.route('/', methods=('GET', 'POST'))
@login_required
def settings():
    # Individual error vars for each form
    errorUser = None
    errorPass = None
    errorNotif = None
    base32 = None
    qrString = None
    totpEnabled = False
    db = get_db()  
    userDetails = db.execute('SELECT first_name, password, email, time_zone, totp FROM users WHERE id = ?', (g.user['id'],)).fetchone()
    notifDetails = db.execute('SELECT email, discord, email_enabled, discord_enabled FROM notification_settings WHERE user_id = ?', 
        (g.user['id'],)).fetchone()
    if userDetails['totp']: totpEnabled = True

    if request.method == 'POST':
        # If user form is submitted
        if request.form["btn"] == "user":
            first_name = request.form['first_name']
            email = request.form['email']
            timeZone = request.form['time_zone']

            if (first_name and first_name is userDetails['first_name']):
                errorUser = "Your new name cannot be the same as your existing one."
            elif (email and email is userDetails['email']):
                errorUser = "Your new email cannot be the same as your existing one."
            elif (timeZone and timeZone is userDetails['time_zone']):
                errorUser = "Your new time zone cannot be the same as your existing one."

            if errorUser is None:
                if (first_name):
                    db.execute('UPDATE users SET first_name = ? WHERE id = ?', (first_name, g.user['id']))
                    db.commit()
                if (email):
                    db.execute('UPDATE users SET email = ? WHERE id = ?', (email, g.user['id']))
                    db.commit()
                    sendNotification(g.user['id'], f"Letting you know that your email was changed to '{email}'")
                    session.clear()
                if (timeZone):
                    db.execute('UPDATE users SET time_zone = ? WHERE id = ?', (timeZone, g.user['id']))
                    db.commit()
                return redirect(url_for('profile.settings'))

        # If password form is submitted
        elif request.form["btn"] == "password":
            current_password = request.form['current_password']
            password = request.form['password']
            password_repeat = request.form['password_repeat']

            if not current_password or not password or not password_repeat:
                errorPass = "All fields are required."
            elif not check_password_hash(userDetails['password'], current_password):
                errorPass = "Current password is incorrect."
            elif len(password) < 8:
                errorPass = 'Password is shorter than 8 characters.'
            elif password != password_repeat:
                errorPass = "New passwords do not match."
           
            if errorPass is None:
                db.execute('UPDATE users SET password = ? WHERE id = ?', (generate_password_hash(password), g.user['id']))
                db.commit()
                sendNotification(g.user['id'], "Letting you know that your password was reset.")
                session.clear()
                return redirect(url_for('auth.login'))

        # If notification form is submitted
        elif request.form["btn"] == "notif":
            chkEmail = request.form.get('chkEmail')
            chkDiscord = request.form.get('chkDiscord')
            notifEmail = request.form['notifEmail']
            notifDiscord = request.form['notifDiscord']

            # Individual checks for notification agents
            if (chkEmail == "on"):
                db.execute('UPDATE notification_settings SET email_enabled = 1 WHERE user_id = ?', (g.user['id'],))
                db.commit()
            else:
                db.execute('UPDATE notification_settings SET email_enabled = 0 WHERE user_id = ?', (g.user['id'],))
                db.commit()
            if (chkDiscord == "on"):
                db.execute('UPDATE notification_settings SET discord_enabled = 1 WHERE user_id = ?', (g.user['id'],))
                db.commit()
            else:
                db.execute('UPDATE notification_settings SET discord_enabled = 0 WHERE user_id = ?', (g.user['id'],))
                db.commit()
            if (notifEmail):
                db.execute('UPDATE notification_settings SET email = ? WHERE user_id = ?', (notifEmail, g.user['id']))
                db.commit()
            if (notifDiscord):
                db.execute('UPDATE notification_settings SET discord = ? WHERE user_id = ?', (notifDiscord, g.user['id']))
                db.commit()
            return redirect(url_for('profile.settings'))

        # If delete user form is submitted
        elif request.form["btn"] == "deleteUser":
            # Remove all db entries related to the user
            db.execute('DELETE FROM users WHERE id = ?', (g.user['id'],))
            db.commit()
            websiteDB = db.execute("SELECT id FROM websites WHERE user_id = ?", (g.user['id'],)).fetchall()
            for website in websiteDB:
                db.execute('DELETE FROM website_log WHERE website_id = ?', (website[0],))
            db.execute('DELETE FROM websites WHERE user_id = ?', (g.user['id'],))
            db.commit()
            db.execute('DELETE FROM user_alerts WHERE user_id = ?', (g.user['id'],))
            db.commit()
            db.execute('DELETE FROM notification_settings WHERE user_id = ?', (g.user['id'],))
            db.commit()
            db.execute('DELETE FROM reset_pass WHERE user_id = ?', (g.user['id'],))
            session.clear()
            return redirect(url_for('main.index'))

        # If totp form is submitted
        elif request.form["btn"] == "totp":
            user = db.execute('SELECT totp, email FROM users WHERE id = ?', (g.user['id'],)).fetchone()
            if user[0]:
                db.execute('UPDATE users SET totp = ? WHERE id = ?', (None, g.user['id']))
                db.commit()
                errorPass = "Multi-Factor authentication removed."
            else:
                base32 = pyotp.random_base32()
                db.execute('UPDATE users SET totp = ? WHERE id = ?', (base32, g.user['id']))
                db.commit()
                qrString = f"otpauth://totp/{user[1]}?secret={base32}&issuer=Endstat"

    return render_template('profile/profile-settings.html', errorUser=errorUser, errorPass=errorPass, errorNotif=errorNotif, currentFName=userDetails['first_name'], currentEmail=userDetails['email'], currentTZone=userDetails['time_zone'], notifDetails=notifDetails, qrString=qrString, totpCode=base32, totpEnabled=totpEnabled)

# View for user alerts
@bp.route('/alerts', methods=('GET', 'POST'))
@login_required
def alerts():
    error = None
    db = get_db()
    alertsDict = {}
    alertsDB = db.execute('SELECT message, datetime(date_time), type, read FROM user_alerts WHERE user_id = ? ORDER BY id DESC LIMIT 5', (g.user['id'],)).fetchall()
    for row in alertsDB:
        message, dateTime, type, read = row
        icon = getAlertIcon(type)
        convDate = convertToUserTime(dateTime, g.user['id'])
        alertsDict[message] = [convDate, type, icon, bool(read)]
    
    if (request.method == 'POST'):
        db.execute('UPDATE user_alerts SET read = 1 WHERE id = ?', (request.form['read'],))
        db.commit()
    return render_template('profile/alerts.html', error=error, alerts=alertsDict)