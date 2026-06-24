#Author Deniz Rahnefeld (409637)

from flask import Blueprint, render_template, request, redirect, url_for, flash
from auth.queries import *
from auth.utils import *

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
    # Felder: Vorname, Nachname, Matrikelnummer, Email, Passwort, Passwort wiederholen
    #   seminar, studiengang_name, abschluss, seminar_thema
    if request.method == 'GET':
        return render_template("auth/register.html")
    else:
        data = request.form
        empty_input_found, leere_felder = check_register_input(data)

        if empty_input_found:
            for feld in leere_felder:
                flash(f'Das Feld {feld} ist leer!', 'error')
            return render_template('auth/register.html', values=data)





@auth_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'GET':
        #if logged in:
        #else:
        return redirect(url_for('auth.login'))
    else:
        #TODO Authentifikation hinzufügen
        return render_template("auth/profile.html")



