from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, send_file
)
from endstat.db import get_db
from endstat.auth import login_required

bp = Blueprint('main', __name__)

#Index
@bp.route('/')
def index():
    return render_template('index.html')