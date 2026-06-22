from xml.etree.ElementTree import QName

from flask import Blueprint, render_template, request, redirect, url_for, session
from auth.queries import *


auth_bp = Blueprint('auth', __name__, template_folder='templates')


