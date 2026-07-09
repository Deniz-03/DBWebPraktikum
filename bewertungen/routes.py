#Author Tim Deppe (413323)
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from auth.queries import get_user_role, get_user_info, is_seminar_occupied
from themen.utils import pruefe_dozent
from bewertungen.queries import *
from bewertungen.utils import *

"""<a href="{{ url_for('bewertungen.vortrag_bewerten') }}" class="sidebarLinks">Vortrag Bewerten</a>"""
"""<a href="{{ url_for('bewertungen.ausarbeitung_bewerten') }}" class="sidebarLinks">Ausarbeitungen Bewerten</a>"""
"""<a href="{{ url_for('bewertungen.seminarleistung') }}" class="sidebarLinks">Seminarleistung Bewerten</a>"""

bewertungen_bp = Blueprint('bewertungen', __name__, template_folder='templates')

KRITERIEN = [
    ('foliengestaltung', 'Foliengestaltung'),
    ('sprachliche_praesentation', 'Sprachliche Präsentation'),
    ('stil', 'Präsentationsstil'),
    ('zeitliche_gestaltung', 'Zeitliche Gestaltung'),
    ('verstaendnis', 'Verständnis'),
    ('inhalt', 'Inhaltliche Aufbereitung'),
    ('verknuepfung', 'Verknüpfung mit anderen Vorträgen'),
    ('diskussion', 'Diskussionsführung (eigener Vortrag)'),
    ('beteiligung', 'Beteiligung an Diskussionen (andere Vorträge)'),
]

SKALA_LABELS = {1: '--', 2: '-', 3: 'o', 4: '+', 5: '++'}

@bewertungen_bp.route('/bewertungen/vortrag_bewerten', methods=['GET', 'POST'])
def vortrag_bewerten():
    if request.method == 'GET':
        if 'user_id' in session: #Unangemeldete User werden auf die Startseite zurückgeleitet
            vortraege = get_bewertbare_vortraege(exclude_account_id=session['user_id'])
            if vortraege is None:
                flash('Kein Vortrag angegeben.')
                return redirect(url_for('themen.themen_uebersicht'))
            return render_template('bewertungen/vortrag.html',
                vortraege=vortraege, kriterien=KRITERIEN, skala=SKALA_LABELS)
        return render_template("index.html")

    else:
        if 'user_id' in session:
            form = request.form

            t_id_raw = form.get('t_id')
            if not t_id_raw or not t_id_raw.isdigit():
                flash('Bitte einen Vortrag auswählen.')
                return redirect(url_for('bewertungen.vortrag_bewerten'))
            t_id = int(t_id_raw)

            if not ist_vortrag_bewertbar(t_id, session['user_id']):
                flash('Dieser Vortrag steht aktuell nicht zur Bewertung.')
                return redirect(url_for('bewertungen.vortrag_bewerten'))

            if ist_eigener_vortrag(t_id, session['user_id']):
                flash('Du kannst deinen eigenen Vortrag nicht bewerten.')
                return redirect(url_for('bewertungen.vortrag_bewerten'))

            data = {'t_id': t_id, 'bewertender_id': session['user_id']}

            for feld, label in KRITERIEN:
                wert = form.get(feld)
                if wert not in (1, 2, 3, 4, 5):
                    flash(f'Bitte "{label}" bewerten.')
                    vortraege = get_bewertbare_vortraege(exclude_account_id=session['user_id'])
                    return render_template(
                        'bewertungen/vortrag.html',
                        vortraege=vortraege, kriterien=KRITERIEN, skala=SKALA_LABELS
                    )
                data[feld] = int(wert)

            kommentar = form.get('kommentar', '').strip()
            data['kommentar'] = kommentar if kommentar else None

            erfolg = create_bew_vortrag(data)
            if erfolg:
                flash('Bewertung erfolgreich gespeichert.')
                return redirect(url_for('themen.themen_uebersicht'))
            else:
                flash('Bewertung konnte nicht gespeichert werden (evtl. hast du bereits bewertet).')
                vortraege = get_bewertbare_vortraege(exclude_account_id=session['user_id'])
                return render_template(
                    'bewertungen/vortrag.html',
                    vortraege=vortraege, kriterien=KRITERIEN, skala=SKALA_LABELS
                )
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