from xml.etree.ElementTree import QName

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
        #TODO Angemeldeten Nutzer weiterleiten
        pass


