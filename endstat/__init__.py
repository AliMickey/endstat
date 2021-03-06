import os
from flask import Flask
from flask_qrcode import QRcode

def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import websites
    app.register_blueprint(websites.bp)

    from . import profile
    app.register_blueprint(profile.bp)

    from . import main
    app.register_blueprint(main.bp)
    app.add_url_rule('/', endpoint='index')

    # In case app is restarted, all websites will be assigned a new scheduler job
    from . import scheduler
    app.before_first_request(scheduler.schedInitJobs)

    # Extends the app with qrcode functionlity for totp.
    QRcode(app)
    
    return app