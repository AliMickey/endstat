from flask import (
    Blueprint, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from endstat.auth import login_required
from endstat.db import get_db
from endstat.notifications import sendNotification

bp = Blueprint('profile', __name__, url_prefix='/profile')

@bp.route('/', methods=('GET', 'POST'))
@login_required
def settings():
    error = None
    db = get_db()  
    userDetails = db.execute('SELECT first_name, password, email FROM users WHERE id = ?', (g.user['id'],)).fetchone()
    notifDetails = db.execute('SELECT email, discord, email_enabled, discord_enabled FROM notification_settings WHERE user_id = ?', 
        (g.user['id'],)).fetchone()

    if request.method == 'POST':
        if request.form["btn"] == "user":
            first_name = request.form['first_name']
            email = request.form['email']

            if (first_name and first_name is userDetails['first_name']):
                error = "Your new name cannot be the same as your existing one."
            elif (email and email is userDetails['email']):
                error = "Your new email cannot be the same as your existing one."

            if error is None:
                if (first_name):
                    db.execute('UPDATE users SET first_name = ? WHERE id = ?', (first_name, g.user['id']))
                    db.commit()
                    return redirect(url_for('profile.settings'))
                if (email and email is not userDetails['email']):
                    db.execute('UPDATE users SET email = ? WHERE id = ?', (email, g.user['id']))
                    db.commit()
                    sendNotification(g.user['id'], f"Letting you know that your email was changed to '{email}'")
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
                db.execute('UPDATE users SET password = ? WHERE id = ?', (generate_password_hash(password), g.user['id']))
                db.commit()
                sendNotification(g.user['id'], "Letting you know that your password was reset.")
                session.clear()
                return redirect(url_for('auth.login'))

        elif request.form["btn"] == "notif":
            chkEmail = request.form.get('chkEmail')
            chkDiscord = request.form.get('chkDiscord')
            print(chkDiscord)
            notifEmail = request.form['notifEmail']
            notifDiscord = request.form['notifDiscord']


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

    return render_template('profile/profile-settings.html', error=error, currentFName=userDetails['first_name'], currentEmail=userDetails['email'], notifDetails=notifDetails)


# View for user alerts
@bp.route('/alerts', methods=('GET', 'POST'))
@login_required
def alerts():
    error = None
    db = get_db()

    return render_template('profile/alerts.html', error=error, alerts=alerts)