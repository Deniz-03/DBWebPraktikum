#Author Tim Deppe (413323)
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from auth.queries import get_user_role
from bewertungen.queries import *
from bewertungen.utils import *

bewertungen_bp = Blueprint('bewertungen', __name__, template_folder='templates')

@bewertungen_bp.route('/vortrag_bewerten', methods=['GET', 'POST'])
def vortrag_bewerten():
    #TODO: logik für Vortrag bewerten
    return render_template("index.html")