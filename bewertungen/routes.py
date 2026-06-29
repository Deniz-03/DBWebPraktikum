#Author Tim Deppe (413323)
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from bewertungen.queries import *
from bewertungen.utils import *

#bewertungen_bp = Blueprint('bewertungen', __name__, template_folder='templates')