#Author Peer Schulze (410246)

import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from auth.queries import get_user_role, get_user_info
from themen.queries import get_dozierenden, thema_anlegen, thema_bearbeiten, get_seminarthema, get_student_by_id
from themen.utils import validiere_thema_form, pruefe_dozent

themen_bp = Blueprint('themen', __name__)

# Post und Get Methode zum Anlegen eines Seminarthemas
@themen_bp.route('/themen/neu', methods=['GET', 'POST'])
def themen_neu():
    # Abfangen von Nutzern die keine Dozenten sind oder wenn keiner User_id in der Session ist
    user_id = int(session.get('user_id'))
    rolle = get_user_role(user_id) if user_id else None
    if not pruefe_dozent(user_id, rolle):
        return redirect(url_for('auth.index'))

    # Lädt die Thema anlegen Seite, füllt das Dropdown für die Dozierenden
    # und hat den eingeloggten Dozenten vorausgewählt
    if request.method == 'GET':
        dozierenden = get_dozierenden()
        eingeloggter_dozent = user_id
        return render_template('themen/thema_anlegen.html',
                                dozierenden = dozierenden,
                                eingeloggter_dozent = eingeloggter_dozent,)

    # Auslesen des Formulars und Speichern des Seminarthemas in der DB
    if request.method == 'POST':
        data = request.form
        titel = data.get('titel')
        oberbegriff = data.get('oberbegriff')
        beschreibung = data.get('beschreibung')
        d_id = data.get('d_id')
        semester = data.get('semester')

        dozierenden = get_dozierenden()
        eingeloggter_dozent = user_id

        # Prüfen der Pflichtfelder und das der Dozent ausgewählt wurde (Vorauswahl oder manuel geändert)
        if not titel or not oberbegriff or not beschreibung or not d_id:
            return render_template('themen/thema_anlegen.html',
                                   fehler = 'Bitte alle Pflichtfelder ausfüllen',
                                   dozierenden = dozierenden,
                                   eingeloggter_dozent = eingeloggter_dozent,)

        # request.files.get('pdf') holt die hochgeladene Datei aus dem Formular
        pdf = request.files.get('pdf')
        # Dateiname auslesen
        pdf_dateiname = pdf.filename if pdf and pdf.filename != '' else None

        # Validieren der mitgeschickten Felder.
        fehler = validiere_thema_form(titel, oberbegriff, beschreibung, d_id, semester, pdf_dateiname, dozierenden)
        if fehler:
            return render_template('themen/thema_anlegen.html',
                                   fehler=fehler,
                                   dozierenden=dozierenden,
                                   eingeloggter_dozent=eingeloggter_dozent, )

        # Prüft ob überhaupt eine Datei hochgeladen wurde
        if pdf and pdf.filename != '':
            # bereinigt den Dateinamen, z.B. entfernt Leerzeichen und gefährliche Zeichen
            dateiname = secure_filename(pdf.filename)
            # Speichert die Datei in themen/uploads
            pdf.save(os.path.join('themen/uploads', dateiname))
            # Nur der Dateiname wird in der DB gespeichert
            pdf_pfad = dateiname
        # Wird ausgeführt wenn keine Datei hochgeladen wurde
        else:
            pdf_pfad = None

        # Das Seminarthema wird nun gespeichert
        thema_anlegen(titel, d_id, oberbegriff, beschreibung, semester=semester, pdf_pfad=pdf_pfad,)

        # Weiterleiten
        return redirect(url_for('themen.themen_uebersicht')) # URL funktioniert wenn anf 4 fertig ist

# Post und Get Methode zum Bearbeiten eines Seminarthemas
# Es wird durch <int:theme_id> die Themen_id direkt extrahiert und an die Funktion übergeben
@themen_bp.route('/themen/<int:themen_id>/bearbeiten', methods=['GET', 'POST'])
def themen_bearbeiten(themen_id):
    # Abfangen von Nutzern die keine Dozenten sind oder wenn keiner User_id in der Session ist
    user_id = int(session.get('user_id'))
    rolle = get_user_role(user_id) if user_id else None
    if not pruefe_dozent(user_id, rolle):
        return redirect(url_for('auth.index'))

    # Get Methode zum laden der Bearbeitungsseite mit vorausgefüllten Feldern
    if request.method == 'GET':
        data = get_seminarthema(themen_id)
        # data ist ein Dictionary, kein Tupel mehr
        titel = data['titel']
        d_id = data['d_id']
        status = data['status']
        oberbegriff = data['oberbegriff']
        beschreibung = data['beschreibung']
        s_id = data['s_id']
        semester = data['semester']
        pdf = data['pdf_pfad']
        vorgetragen = data['vorgetragen']

        # Namen des Studenten holen, wenn er eingetragem ist
        if s_id:
            student = get_student_by_id(s_id)
        else:
            student = None

        dozierenden = get_dozierenden()

        return render_template('themen/thema_bearbeiten.html',
                        titel=titel,
                        d_id=d_id,
                        status=status,
                        oberbegriff=oberbegriff,
                        beschreibung=beschreibung,
                        student=student,
                        semester=semester,
                        pdf_pfad=pdf,
                        dozierenden=dozierenden,
                        vorgetragen=vorgetragen)

    # Post Methode um bearbeitete Felder zu Speichern
    if request.method == 'POST':
        data = request.form
        titel = data.get('titel')
        d_id = data.get('d_id')
        oberbegriff = data.get('oberbegriff')
        beschreibung = data.get('beschreibung')
        semester = data.get('semester')
        # Da False als String übergeben wird wäre bool('False') == True immer True
        vorgetragen = data.get('vorgetragen') == 'True'

        dozierenden = get_dozierenden()
        eingeloggter_dozent = session.get('user_id')

        # Prüfen der Pflichtfelder und das der Dozent ausgewählt wurde (Vorauswahl oder manuel geändert)
        if not titel or not oberbegriff or not beschreibung or not d_id:
            return render_template('themen/thema_bearbeiten.html',
                                   fehler='Bitte alle Pflichtfelder ausfüllen',
                                   dozierenden=dozierenden,
                                   eingeloggter_dozent=eingeloggter_dozent, )

        # Ziehen der/des PDF Files/File
        pdf = request.files.get('pdf')
        pdf_dateiname = pdf.filename if pdf and pdf.filename != '' else None

        # Validieren der mitgeschickten Felder.
        fehler = validiere_thema_form(titel, oberbegriff, beschreibung, d_id, semester, pdf_dateiname, dozierenden)
        if fehler:
            return render_template('themen/thema_bearbeiten.html',
                                   fehler=fehler,
                                   dozierenden=dozierenden,
                                   eingeloggter_dozent=eingeloggter_dozent, )

        if pdf and pdf.filename != '':
            dateiname = secure_filename(pdf.filename)
            pdf.save(os.path.join('themen/uploads', dateiname))
            pdf_pfad = dateiname
        else:
            pdf_pfad = None

        # Neue Daten werden gespeichert
        thema_bearbeiten(themen_id, titel, d_id, oberbegriff, beschreibung, semester, pdf_pfad,
                         vorgetragen=vorgetragen)

        return redirect(url_for('themen.themen_uebersicht'))  # URL funktioniert wenn ANF 4 fertig ist

# Route um die User Seite mittels der ID zu Laden
@themen_bp.route('/themen/profile/<int:student_id>', methods=['GET'])
def profile(student_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.index'))
    user_id = int(user_id)
    rolle = get_user_role(user_id)

    # Nur Dozenten dürfen laut Anf 2 die Profile der Studenten sehen
    if not pruefe_dozent(user_id, rolle):
        flash('Nur Dozenten haben Zugriff auf das Profil', 'error')
        return redirect(url_for('themen.themen_uebersicht'))

    user_info = get_user_info(student_id)
    return render_template('auth/profile.html', view_mode=True, user_info=user_info)


