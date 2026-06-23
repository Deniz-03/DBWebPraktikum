#Author Deniz Rahnefeld (409637)

from flask import Blueprint, render_template, request, redirect, url_for, session
from auth.queries import *


auth_bp = Blueprint('auth', __name__, template_folder='templates')

@auth_bp.route('/')
def index():
    return render_template("index.html")

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("auth/login.html")
    else:
        #TODO Angemeldeten Nutzer weiterleiten bzw. Nutzer anmelden
        pass

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("auth/register.html")
    else:
        #TODO Registrierung abschließen und Nutzer anlegen
        pass
@auth_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'GET':
        #if logged in:
        #else:
        return redirect(url_for('auth.login'))
    else:
        #TODO Authentifikation hinzufügen
        return render_template("auth/profile.html")



