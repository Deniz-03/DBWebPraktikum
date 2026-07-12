#Author Tim Deppe (413323)
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from auth.queries import get_user_role, get_user_info
from themen.utils import pruefe_dozent
from bewertungen.queries import *

bewertungen_bp = Blueprint('bewertungen', __name__, template_folder='templates')

VORTRAGSKRITERIEN = [
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

@bewertungen_bp.route('/bewertungen/vortrag', methods=['GET', 'POST'])
def vortrag_bewerten():
    if request.method == 'GET':
        if 'user_id' in session:  #Unangemeldete User werden auf die Loginseite zurückgeleitet
            vortraege = get_bewertbare_vortraege(exclude_account_id=int(session.get('user_id', '-1')))
            rolle = get_user_role(int(session.get('user_id', '-1')))
            return render_template('bewertungen/vortrag.html',
                vortraege=vortraege, kriterien=VORTRAGSKRITERIEN, skala=SKALA_LABELS, rolle=rolle)
        flash('Bitte zuerst einloggen.')
        return redirect(url_for('auth.login'))

    else:
        if 'user_id' in session:
            form = request.form
            rolle = get_user_role(int(session.get('user_id', '-1')))

            # Prüft ob ein Vortrag im Formular gewählt wurde
            t_id_raw = form.get('t_id')
            if not t_id_raw or not t_id_raw.isdigit():
                flash('Bitte einen Vortrag auswählen.')
                return redirect(url_for('bewertungen.vortrag_bewerten'))
            t_id = int(t_id_raw)

            # Prüft ob der Vortrag vom angemeldeten Nutzer bewertbar ist
            if not ist_vortrag_bewertbar(t_id, int(session.get('user_id', '-1'))):
                flash('Dieser Vortrag steht aktuell nicht zur Bewertung.')
                return redirect(url_for('bewertungen.vortrag_bewerten'))

            #Prüft ob der angemeldete Nutzer versucht seinen eigenen Vortrag zu bewerten
            if ist_eigener_vortrag(t_id, int(session.get('user_id', '-1'))):
                flash('Du kannst deinen eigenen Vortrag nicht bewerten.')
                return redirect(url_for('bewertungen.vortrag_bewerten'))

            data = {'t_id': t_id, 'bewertender_id': int(session.get('user_id', '-1'))}

            #Prüft ob zu jedem Kriterium eine Bewertung angegeben wurde
            for feld, label in VORTRAGSKRITERIEN:
                wert = form.get(feld, type=int)
                if wert not in (1, 2, 3, 4, 5):
                    flash(f'Bitte "{label}" bewerten.')
                    vortraege = get_bewertbare_vortraege(exclude_account_id=int(session.get('user_id', '-1')))
                    return render_template('bewertungen/vortrag.html',
                        ortraege=vortraege, kriterien=VORTRAGSKRITERIEN, skala=SKALA_LABELS, rolle=rolle)
                data[feld] = int(wert)

            kommentar = form.get('kommentar', '').strip() #Extra Leerzeichen werden entfernt vor der Speicherung
            data['kommentar'] = kommentar if kommentar else None

            erfolg = create_bew_vortrag(data)
            if erfolg: #Nutzer bekommen eine Bestätigung der erfolgreichen Speicherung der Bewertung
                flash('Bewertung erfolgreich gespeichert.')
                return redirect(url_for('themen.themen_uebersicht'))
            else:
                flash('Bewertung konnte nicht gespeichert werden (evtl. hast du bereits bewertet).')
                vortraege = get_bewertbare_vortraege(exclude_account_id=int(session.get('user_id', '-1')))
                return render_template('bewertungen/vortrag.html',
                    vortraege=vortraege, kriterien=VORTRAGSKRITERIEN, skala=SKALA_LABELS, rolle=rolle)
        flash('Bitte zuerst einloggen.')
        return redirect(url_for('auth.login'))


@bewertungen_bp.route('/bewertungen/ansicht', methods=['GET', 'POST'])
def ansicht_statistik():
    if request.method == 'GET':
        return redirect(url_for('auth.profile'))
    else:
        if 'user_id' in session:  #Unangemeldete User werden auf die Loginseite zurückgeleitet
            user_id = int(session.get('user_id', '-1'))
            rolle = get_user_role(user_id)
            if rolle == 'doz': #Dozenten dürfen Profile ansehen, die nicht ihnen selbst zugeordnet sind
                form = request.form
                s_id = form.get('s_id')
                try:
                    user_info = get_user_info(s_id)
                    v_statistik = get_vortragsstatistiken(s_id)
                    a_statistik = get_ausarbeitung_statistiken(s_id)
                    l_statistik = get_seminarleistung(s_id)
                    return render_template('bewertungen/ansicht.html',
                        user_info=user_info, v_statistik=v_statistik, a_statistik=a_statistik, l_statistik=l_statistik,
                        rolle=rolle)
                except ValueError:
                    flash('Das Konto existiert nicht.')
                    return redirect(url_for('themen.themen_uebersicht'))
            #Studierende sehen immer nur ihre eigenen Statistiken
            user_info = get_user_info(int(session.get('user_id', '-1')))
            v_statistik = get_vortragsstatistiken(int(session.get('user_id', '-1')))
            return render_template('bewertungen/ansicht.html',
                user_info=user_info, v_statistik=v_statistik, rolle=rolle)
        flash('Bitte zuerst einloggen.')
        return redirect(url_for('auth.login'))


AUSARBEITUNGSKRITERIEN = [
    ('umfang', 'Umfang'),
    ('referenzen', 'Referenzen'),
    ('sprachliche_gestaltung', 'Sprachliche Gestaltung'),
    ('inhalt', 'Inhaltliche Aufbereitung'),
    ('schwierigkeitsgrad', 'Schwierigkeitsgrad')
]

@bewertungen_bp.route('/bewertungen/ausarbeitung', methods=['GET', 'POST'])
def ausarbeitung_bewerten():
    if request.method == 'GET':
        if 'user_id' in session:  #Unangemeldete User werden auf die Loginseite zurückgeleitet
            user_id = int(session.get('user_id', '-1'))
            rolle = get_user_role(user_id)
            if not pruefe_dozent(user_id, rolle):  #Studenten werden auf die Loginseite zurückgeleitet
                return render_template("index.html")
            ausarbeitungen = get_bewertbare_ausarbeitungen(int(session.get('user_id', '-1')))
            return render_template("bewertungen/ausarbeitung.html",
                ausarbeitungen=ausarbeitungen, kriterien=AUSARBEITUNGSKRITERIEN, skala=SKALA_LABELS, rolle=rolle)
        flash('Bitte zuerst einloggen.')
        return redirect(url_for('auth.login'))
    else:
        if 'user_id' in session: #Unangemeldete User werden auf die Loginseite zurückgeleitet
            form = request.form
            rolle = get_user_role(int(session.get('user_id', '-1')))
            ausarbeitungen = get_bewertbare_ausarbeitungen(int(session.get('user_id', '-1')))

            # Prüft ob eine Ausarbeitung im Formular gewählt wurde
            t_id_raw = form.get('t_id')
            if not t_id_raw or not t_id_raw.isdigit():
                flash('Bitte eine Ausarbeitung auswählen.')
                return redirect(url_for('bewertungen.ausarbeitung_bewerten'))
            t_id = int(t_id_raw)

            #Prüft ob die Ausarbeitung vom Dozenten bereits bewertet wurde
            if not ist_ausarbeitung_bewertbar(t_id):
                flash('Diese Ausarbeitung steht aktuell nicht zur Bewertung.')
                return redirect(url_for('bewertungen.ausarbeitung_bewerten'))

            data = {'t_id': t_id, 'bewertender_id': int(session.get('user_id', '-1'))}

            # Prüft ob zu jedem Kriterium eine Bewertung angegeben wurde, fehlende Kriterien werden dem Nutzer gemeldet
            for feld, label in AUSARBEITUNGSKRITERIEN:
                wert = form.get(feld, type=int)
                if wert not in (1, 2, 3, 4, 5):
                    flash(f'Bitte "{label}" bewerten.')
                    return render_template('bewertungen/vortrag.html',
                        ausarbeitungen=ausarbeitungen, kriterien=VORTRAGSKRITERIEN, skala=SKALA_LABELS, rolle=rolle)
                data[feld] = int(wert)

            kommentar = form.get('kommentar', '').strip()
            data['kommentar'] = kommentar if kommentar else None

            erfolg = create_bew_ausarbeitung(data)
            if erfolg: #Dem Dozenten wird bestätigt, dass die Bewertung erfolgreich gespeichert wurde
                flash('Bewertung erfolgreich gespeichert.')
                return redirect(url_for('themen.themen_uebersicht'))
            else:
                flash('Bewertung konnte nicht gespeichert werden (evtl. hast du bereits bewertet).')
                ausarbeitungen = get_bewertbare_ausarbeitungen(int(session.get('user_id', '-1')))
                return render_template('bewertungen/vortrag.html',
                    ausarbeitungen=ausarbeitungen, kriterien=VORTRAGSKRITERIEN, skala=SKALA_LABELS, rolle=rolle)
        flash('Bitte zuerst einloggen.')
        return redirect(url_for('auth.login'))


ZULAESSIGE_NOTEN = [1.0, 1.3, 1.7, 2.0, 2.3, 2.7, 3.0, 3.3, 3.7, 4.0, 5.0]

@bewertungen_bp.route('/bewertungen/seminarleistung', methods=['GET', 'POST'])
def seminarleistung_bewerten():
    if request.method == 'GET':
        if 'user_id' in session: #Unangemeldete User werden auf die Loginseite zurückgeleitet
            user_id = int(session.get('user_id', '-1'))
            rolle = get_user_role(user_id)
            if rolle == 'doz': #Studierende werden an die Themenübersicht Seite weitergeleitet
                seminarthemen = get_bewertbare_seminarleistungen(user_id)
                return render_template('bewertungen/seminarleistung.html',
                    seminarthemen=seminarthemen, noten=ZULAESSIGE_NOTEN, rolle=rolle)
            flash('Nur Dozenten können die Seminarleistung bewerten.')
            return redirect(url_for('themen.themen_uebersicht'))
        flash('Bitte zuerst einloggen.')
        return redirect(url_for('auth.login'))

    else:
        if 'user_id' in session: #Unangemeldete User werden auf die Loginseite zurückgeleitet
            user_id = int(session.get('user_id', '-1'))
            rolle = get_user_role(user_id)
            if rolle == 'doz': #Studierende werden an die Themenübersicht Seite weitergeleitet
                form = request.form

                t_id_raw = form.get('t_id')
                if not t_id_raw or not t_id_raw.isdigit():
                    flash('Bitte ein Seminarthema auswählen.')
                    return redirect(url_for('bewertungen.seminarleistung_bewerten'))
                t_id = int(t_id_raw)

                note_raw = form.get('note')
                try: #String aus der request form umwandeln
                    note = float(note_raw)
                except (TypeError, ValueError): #Flasche Datentypen/Werte werden als unzulässig abgefangen
                    note = None

                if note is None or note not in ZULAESSIGE_NOTEN:
                    flash('Bitte eine gültige Note auswählen.')
                    seminarthemen = get_bewertbare_seminarleistungen(user_id)
                    return render_template('bewertungen/seminarleistung.html',
                        seminarthemen=seminarthemen, noten=ZULAESSIGE_NOTEN, rolle=rolle)

                #Sicherstellen, dass t_id tatsächlich noch serverseitig zulässig ist (auf mehreren Geräten eingeloggt...)
                zulaessige_ids = [s['t_id'] for s in get_bewertbare_seminarleistungen(user_id)]
                if t_id not in zulaessige_ids:
                    flash('Dieses Seminarthema steht aktuell nicht zur Bewertung.')
                    return redirect(url_for('bewertungen.seminarleistung_bewerten'))

                data = {'t_id': t_id, 'note': note}
                erfolg = create_seminarleistung(data)

                if erfolg: #Dem Dozenten wird bestätigt, dass die Note erfolgreich gespeichert wurde
                    flash('Seminarleistung erfolgreich bewertet.')
                    return redirect(url_for('themen.themen_uebersicht'))
                else:
                    flash('Seminarleistung konnte nicht gespeichert werden.')

                return redirect(url_for('bewertungen.seminarleistung_bewerten'))
            flash('Nur Dozenten können die Seminarleistung bewerten.')
            return redirect(url_for('themen.themen_uebersicht'))
        flash('Bitte zuerst einloggen.')
        return redirect(url_for('auth.login'))