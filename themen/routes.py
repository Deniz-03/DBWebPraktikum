#Author Peer Schulze (410246)

from flask import Blueprint, render_template, request, redirect, url_for, flash

from auth.queries import get_user_info
from themen.queries import get_dozierenden, thema_anlegen, thema_bearbeiten, get_seminarthema, get_student_by_id, \
    get_alle_seminarthemen, get_dozent_by_id, student_hinzufuegen
from themen.utils import validiere_thema_form, pruefe_dozent, pruefe_student, thema_belegen_pruefen, \
    hole_user_und_rolle, speichere_pdf

themen_bp = Blueprint('themen', __name__)

# Post und Get Methode zum Anlegen eines Seminarthemas
@themen_bp.route('/themen/neu', methods=['GET', 'POST'])
def themen_neu():
    # Abfangen von Nutzern die keine Dozenten sind oder wenn keine User_id in der Session ist
    user_id, rolle = hole_user_und_rolle()
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
            fehler = 'Bitte alle Pflichtfelder ausfüllen'
            return render_template('themen/thema_anlegen.html',
                                   titel=titel,
                                   oberbegriff=oberbegriff,
                                   beschreibung=beschreibung,
                                   d_id=d_id,
                                   semester=semester,
                                   fehler = fehler,
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
                                   titel=titel,
                                   oberbegriff=oberbegriff,
                                   beschreibung=beschreibung,
                                   d_id=d_id,
                                   semester=semester,
                                   fehler=fehler,
                                   dozierenden=dozierenden,
                                   eingeloggter_dozent=eingeloggter_dozent, )

        pdf_pfad = speichere_pdf(pdf)

        # Das Seminarthema wird nun gespeichert
        thema_anlegen(titel, d_id, oberbegriff, beschreibung, semester=semester, pdf_pfad=pdf_pfad,)

        # Weiterleiten
        return redirect(url_for('themen.themen_uebersicht')) # URL funktioniert wenn anf 4 fertig ist

# Post und Get Methode zum Bearbeiten eines Seminarthemas
# Es wird durch <int:theme_id> die Themen_id direkt extrahiert und an die Funktion übergeben
@themen_bp.route('/themen/<int:themen_id>/bearbeiten', methods=['GET', 'POST'])
def themen_bearbeiten(themen_id):
    # Abfangen von Nutzern die keine Dozenten sind oder wenn keine User_id in der Session ist
    user_id, rolle = hole_user_und_rolle()
    if not pruefe_dozent(user_id, rolle):
        return redirect(url_for('auth.index'))

    # Überprüfung ob die übergebene Themen_id auch wirklich in der Datenbank existert
    thema_daten = get_seminarthema(themen_id)
    if not thema_daten:
        return redirect(url_for('themen.themen_uebersicht'))

    # Namen des Studenten holen, wenn einer eingetragen ist
    s_id = thema_daten['s_id']
    if s_id:
        student = get_student_by_id(s_id)
    else:
        student = None

    # Get Methode zum laden der Bearbeitungsseite mit vorausgefüllten Feldern
    if request.method == 'GET':
        # data ist ein Dictionary, kein Tupel mehr
        titel = thema_daten['titel']
        d_id = thema_daten['d_id']
        status = thema_daten['status']
        oberbegriff = thema_daten['oberbegriff']
        beschreibung = thema_daten['beschreibung']
        semester = thema_daten['semester']
        pdf = thema_daten['pdf_pfad']
        vorgetragen = thema_daten['vorgetragen']

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
        status = data.get('status')
        # Da False als String übergeben wird wäre bool('False') == True immer True
        vorgetragen = data.get('vorgetragen') == 'True'

        dozierenden = get_dozierenden()

        # Prüfen der Pflichtfelder und das der Dozent ausgewählt wurde (Vorauswahl oder manuel geändert)
        if not titel or not oberbegriff or not beschreibung or not d_id:
            fehler = 'Bitte alle Pflichtfelder ausfüllen'
            return render_template('themen/thema_bearbeiten.html',
                                   fehler=fehler,
                                   titel=titel,
                                   d_id=d_id,
                                   oberbegriff=oberbegriff,
                                   beschreibung=beschreibung,
                                   semester=semester,
                                   status=status,
                                   student=student,
                                   dozierenden=dozierenden,
                                   vorgetragen=vorgetragen
                                   )

        # Ziehen der/des PDF Files/File
        pdf = request.files.get('pdf')
        pdf_dateiname = pdf.filename if pdf and pdf.filename != '' else None

        # Validieren der mitgeschickten Felder.
        fehler = validiere_thema_form(titel, oberbegriff, beschreibung, d_id, semester, pdf_dateiname, dozierenden)
        if fehler:
            return render_template('themen/thema_bearbeiten.html',
                                   fehler=fehler,
                                   titel=titel,
                                   d_id=d_id,
                                   oberbegriff=oberbegriff,
                                   beschreibung=beschreibung,
                                   semester=semester,
                                   status=status,
                                   vorgetragen=vorgetragen,
                                   student=student,
                                   dozierenden=dozierenden
                                   )

        neuer_pdf_pfad = speichere_pdf(pdf)
        if neuer_pdf_pfad:
            pdf_pfad = neuer_pdf_pfad
        else:
            pdf_pfad = thema_daten['pdf_pfad']

        # Neue Daten werden gespeichert
        thema_bearbeiten(themen_id, titel, d_id, oberbegriff, beschreibung, semester, pdf_pfad,
                         vorgetragen=vorgetragen)

        return redirect(url_for('themen.thema_detail', themen_id=themen_id))

# Route um die User Seite mittels der ID zu Laden
@themen_bp.route('/themen/profile/<int:student_id>', methods=['GET'])
def profile(student_id):
    user_id, rolle = hole_user_und_rolle()
    if not user_id:
        return redirect(url_for('auth.index'))

    # Nur Dozenten dürfen laut Anf 2 die Profile der Studenten sehen
    if not pruefe_dozent(user_id, rolle):
        flash('Nur Dozenten haben Zugriff auf das Profil', 'error')
        return redirect(url_for('themen.themen_uebersicht'))

    user_info = get_user_info(student_id)
    return render_template('auth/profile.html', view_mode=True, user_info=user_info)

# Route um die Themen Übersicht mit allen Anforderungen aus Anf 7 zu Laden
@themen_bp.route('/themen/uebersicht', methods=['GET'])
def themen_uebersicht():
    user_id, rolle = hole_user_und_rolle()
    if not user_id:
        return redirect(url_for('auth.index'))

    themen = get_alle_seminarthemen()
    return render_template('themen/themen_uebersicht.html', themen=themen, rolle=rolle)

# Route für die Detailansicht eines Seminarthemas
@themen_bp.route('/themen/thema_detail/<int:themen_id>', methods=['GET', 'POST'])
def thema_detail(themen_id):
    user_id, rolle = hole_user_und_rolle()
    if not user_id:
        return redirect(url_for('auth.index'))

    # Überprüfung ob die übergebene Themen_id auch wirklich in der Datenbank existert
    data = get_seminarthema(themen_id)
    if not data:
        return redirect(url_for('themen.themen_uebersicht'))

    if request.method == 'GET':
        s_id = data['s_id']
        d_id = data['d_id']

        # Namen des Studenten holen, wenn einer eingetragen ist
        if s_id:
            student = get_student_by_id(s_id)
        else:
            student = None

        dozent = get_dozent_by_id(d_id)

        return render_template('themen/thema_detail.html',
                        thema=data,
                        student=student,
                        dozent=dozent,
                        rolle=rolle,
                        user_id=user_id,)

    if request.method == 'POST':
        # Prüfen ob wirklich ein student eingeloggt ist
        if not pruefe_student(rolle):
            return redirect(url_for('auth.index'))

        if thema_belegen_pruefen(data, user_id):
            status = 'Vergeben'
            flash('Thema erfolgreich ausgewählt.', 'success')
            student_hinzufuegen(themen_id, user_id, status)
        else:
            flash('Das Thema ist bereits belegt oder sie belegen bereits ein Thema.', 'error')

        return redirect(url_for('themen.thema_detail', themen_id=themen_id))


