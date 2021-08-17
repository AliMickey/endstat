import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from endstat.db import get_db
from endstat.notifications import send_email

bp = Blueprint('auth', __name__, url_prefix='/auth')

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
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif password != password_repeat:
            error = 'Passwords do not match.'
        elif tempUserID is not None:
            error = 'User "{}" is already registered.'.format(email)

        if error is None:
            # Create user
            db.execute(
                'INSERT INTO users (first_name, email, password) VALUES (?, ?, ?)',
                (first_name, email, generate_password_hash(password))
            )
            db.commit()
            send_email(email, "Welcome to End Stat", "Thanks for trying out End Stat, this is an email to confirm that your account has been created. Head over to https://endstat.com if you havn't already!")
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
            return redirect(url_for('index'))

    return render_template('auth/login.html', error=error)


@bp.route('/forgot-password', methods=('GET', 'POST'))
def forgotPassword():
    print("forgot password")

    #return render_template('auth/forgot-password.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view