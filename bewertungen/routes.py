#Author Tim Deppe (413323)
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from auth.queries import get_user_role
from bewertungen.queries import *
from bewertungen.utils import *

"""<a href="{{ url_for('bewertungen.vortrag_ausarbeitung') }}" class="sidebarLinks">Vorträge und Ausarbeitungen Bewerten</a>"""
"""<a href="{{ url_for('bewertungen.seminarleistung') }}" class="sidebarLinks">Seminarleistung</a>"""

bewertungen_bp = Blueprint('bewertungen', __name__, template_folder='templates')

@bewertungen_bp.route('/bewertungen/vortrag_ausarbeitung', methods=['GET', 'POST'])
def vortrag_ausarbeitung_bewerten():
    #TODO: Logik für Vortrag & Ausarbeitung bewerten
    return render_template("index.html")

@bewertungen_bp.route('/bewertungen/seminarleistung', methods=['GET', 'POST'])
def seminarleistung_bewerten():
    #TODO: Logik für Seminarleistung bewerten
    return render_template("index.html")