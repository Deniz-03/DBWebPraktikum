#Author Peer Schulze (410246)

import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, session
from themen.queries import get_dozierenden, thema_anlegen, thema_bearbeiten, get_seminarthema, get_student_by_id

themen_bp = Blueprint('themen', __name__)

# Post und Get Methode zum Anlegen eines Seminarthemas
@themen_bp.route('/themen/neu', methods=['GET', 'POST'])
def themen_neu():
    # Lädt die Thema anlegen Seite, füllt das Dropdown für die Dozierenden
    # und hat den eingeloggten Dozenten vorausgewählt
    if request.method == 'GET':
        dozierenden = get_dozierenden()
        eingeloggter_dozent = session.get('user_id')
        return render_template('themen/thema_anlegen.html',
                                dozierende = dozierenden,
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
        eingeloggter_dozent = session.get('user_id')

        # Prüfen der Pflichtfelder und das der Dozent ausgewählt wurde (Vorauswahl oder manuel geändert)
        if not titel or not oberbegriff or not beschreibung or not d_id:
            return render_template('themen/thema_anlegen.html',
                                   fehler = 'Bitte alle Pflichtfelder ausfüllen',
                                   dozierende = dozierenden,
                                   eingeloggter_dozent = eingeloggter_dozent,)

        # request.files.get('pdf') holt die hochgeladene Datei aus dem Formular
        pdf = request.files.get('pdf')
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
        thema_anlegen(titel, d_id, oberbegriff, beschreibung, semester=semester, pdf_pfad=pdf_pfad)

        # Weiterleiten
        return redirect(url_for('themen.themen_uebersicht')) # URL funktioniert wenn anf 4 fertig ist

# Post und Get Methode zum Bearbeiten eines Seminarthemas
@themen_bp.route('/themen/<int:themen_id>/bearbeiten', methods=['GET', 'POST'])
def themen_bearbeiten(themen_id):
    # Get Methode zum laden der Bearbeitungsseite mit vorausgefüllten Feldern
    if request.method == 'GET':
        data = get_seminarthema(themen_id)
        # data[x] da es in einem Tupel gespeichert ist
        titel = data[1]
        d_id = data[2]
        oberbegriff = data[4]
        beschreibung = data[5]
        s_id = data[6]
        semester = data[7]
        pdf = data[8]

        # Namen des Studenten holen, wenn er eingetragem ist
        if s_id:
            student = get_student_by_id(s_id)
        else:
            student = None

        dozierenden = get_dozierenden()

        return render_template('themen/thema_bearbeiten.html',
                        titel=titel,
                        d_id=d_id,
                        oberbegriff=oberbegriff,
                        beschreibung=beschreibung,
                        student=student,
                        semester=semester,
                        pdf_pfad=pdf,
                        dozierenden=dozierenden,)

    # Post Methode um bearbeitete Felder zu Speichern
    if request.method == 'POST':
        data = request.form
        titel = data.get('titel')
        d_id = data.get('d_id')
        oberbegriff = data.get('oberbegriff')
        beschreibung = data.get('beschreibung')
        semester = data.get('semester')

        dozierenden = get_dozierenden()
        eingeloggter_dozent = session.get('user_id')

        # Ziehen der/des PDF Files/File
        pdf = request.files.get('pdf')
        if pdf and pdf.filename != '':
            dateiname = secure_filename(pdf.filename)
            pdf.save(os.path.join('themen/uploads', dateiname))
            pdf_pfad = dateiname
        else:
            pdf_pfad = None

        # Prüfen der Pflichtfelder und das der Dozent ausgewählt wurde (Vorauswahl oder manuel geändert)
        if not titel or not oberbegriff or not beschreibung or not d_id:
            return render_template('themen/thema_bearbeiten.html',
                                    fehler='Bitte alle Pflichtfelder ausfüllen',
                                    dozierende=dozierenden,
                                    eingeloggter_dozent=eingeloggter_dozent, )

        # Neue Daten werden gespeichert
        thema_bearbeiten(themen_id, titel, d_id, oberbegriff, beschreibung, semester, pdf_pfad)

        return redirect(url_for('themen.themen_uebersicht'))  # URL funktioniert wenn ANF 4 fertig ist