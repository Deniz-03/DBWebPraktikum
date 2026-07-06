#Author Tim Deppe (413323)
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from auth.queries import get_user_role, get_user_info, is_seminar_occupied
from themen.utils import pruefe_dozent
from bewertungen.queries import *
from bewertungen.utils import *

"""<a href="{{ url_for('bewertungen.vortrag_bewerten') }}" class="sidebarLinks">Vortrag Bewerten</a>"""
"""<a href="{{ url_for('bewertungen.ausarbeitung_bewerten') }}" class="sidebarLinks">Ausarbeitungen Bewerten</a>"""
"""<a href="{{ url_for('bewertungen.seminarleistung') }}" class="sidebarLinks">Seminarleistung Bewerten</a>"""

bewertungen_bp = Blueprint('bewertungen', __name__, template_folder='templates')

@bewertungen_bp.route('/bewertungen/vortrag_bewerten', methods=['GET', 'POST'])
def vortrag_bewerten():
    if request.method == 'GET':
        if 'user_id' in session: #Unangemeldete User werden auf die Startseite zurückgeleitet
            user_id = int(session.get('user_id', '-1'))
            return render_template("bewertungen/vortrag.html", user_id=user_id)
        return render_template("index.html")

    else:
        if 'user_id' in session:
            data = request.form
            user_id = int(session.get('user_id', '-1'))
    #TODO: Logik für method POST
    return render_template("index.html")

@bewertungen_bp.route('/bewertungen/ausarbeitung_bewerten', methods=['GET', 'POST'])
def ausarbeitung_bewerten():
    if request.method == 'GET':
        if 'user_id' in session:
            user_id = int(session.get('user_id', '-1'))
            rolle = get_user_role(user_id)
            if not pruefe_dozent(user_id, rolle): #Studenten werden auf die Startseite zurückgeleitet
                return render_template("index.html")
            return render_template("bewertungen/ausarbeitung.html", user_id=user_id)
        return render_template("index.html")
    #TODO: Logik für method POST
    return render_template("index.html")

@bewertungen_bp.route('/bewertungen/seminarleistung', methods=['GET', 'POST'])
def seminarleistung_bewerten():
    if request.method == 'GET':
        if 'user_id' in session:
            user_id = int(session.get('user_id', '-1'))
            rolle = get_user_role(user_id)
            if not pruefe_dozent(user_id, rolle): # Studenten werden auf die Startseite zurückgeleitet
                return render_template("index.html")
            return render_template("bewertungen/seminarleistung.html", user_id=user_id)
        return render_template("index.html")
    #TODO: Logik für method POST
    return render_template("index.html")