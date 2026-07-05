#Author Peer Schulze (410246)
import os

from werkzeug.utils import secure_filename

from themen.queries import get_sid_aus_themen
from flask import session
from auth.queries import get_user_role


# Validierungsfunktionen für die Formulardaten von Seminarthema anlegen
# Diese werden von routes.py aufgerufen um die Sicherheit der eingaben zu garantieren

# Prüft ob ein textfeld gültig ist
# Leere Strings und ausschließlich Leerzeichen zählen nicht. Ein leeres Feld ist gültig
def ist_gueltiger_text(wert, max_laenge=None):
    if not wert:
        return True
    if not isinstance(wert, str):
        return False  # alles was kein Text ist, ist hier ungültig
    if not wert.strip():
        return False # Führende und Nachfolgende Leerzeichen werden entfernt
    if max_laenge and len(wert.strip()) > max_laenge:
        return False

    return True

# Prüft ob die übermittelte d_id ein gültiger, existierender Dozent ist
def ist_gueltige_dozent_id(d_id, dozierenden_liste):
    try:
        d_id_int = int(d_id)
    # Abfangen von Strings die sich nicht in Zahlen umwandeln lassen (ValueError)
    # Abfangen von d_ids die None sind
    except (TypeError, ValueError):
        return False

    # Liste aus allen d_id der Datenbank
    gueltige_ids = [d['d_id'] for d in dozierenden_liste]

    if d_id_int in gueltige_ids:
        return True
    else:
        return False

# Semester ist optional, muss aber falls angegeben eine ganze Zahl sein
def ist_gueltiges_semester(semester):
    if semester is None or semester == '':
        return True  # optional, leer ist erlaubt

    # Schauen ob sich der String in einen int umwandeln lässt
    # Da Kommazahlen direkt über ValueError laufe, muss dies nicht weiter abgedeckt werden
    try:
        int(semester)
        return True
    except (TypeError, ValueError):
        return False

# Prüft ob eine hochgeladene Datei wirklich ein PDF ist (anhand der Dateiendung)
ERLAUBTE_PDF_ENDUNG = '.pdf'

def ist_gueltiges_pdf(dateiname):
    if not dateiname:
        return True  # kein Upload ist erlaubt, da PDF optional ist

    return dateiname.lower().endswith(ERLAUBTE_PDF_ENDUNG)

# Alle Prüfungen werden egbündelt ausgeführt
# Sobald ein Fehler gefunden wurde wird eine Fehlermeldung zurückgegeben.
# Wenn kein Fehler gefunden wurde wird None zurückgegeben.
def validiere_thema_form(titel, oberbegriff, beschreibung, d_id, semester, pdf_dateiname, dozierenden_liste):
    if not ist_gueltiger_text(titel, max_laenge=255):
        return 'Titel darf nicht leer sein und muss unter 255 Zeichen liegen'

    if not ist_gueltiger_text(oberbegriff, max_laenge=255):
        return 'Oberbegriff darf nicht leer sein und muss unter 255 Zeichen liegen'

    if not ist_gueltiger_text(beschreibung, max_laenge=None):
        return 'Beschreibung darf nicht leer sein'

    if not ist_gueltige_dozent_id(d_id, dozierenden_liste):
        return 'Bitte einen gültigen Dozenten auswählen'

    if not ist_gueltiges_semester(semester):
        return 'Semester muss eine ganze Zahl sein'

    if not ist_gueltiges_pdf(pdf_dateiname):
        return 'Nur PDF Dateien sind möglich'

    return None

# Schauen ob ein Dozierender angemeldet ist
def pruefe_dozent(user_id, rolle):
    # False wenn None oder 0
    if not user_id:
        return False

    # False wenn ein Student angemeldet ist
    if rolle != 'doz':
        return False

    return True

# Schauen ob ein Student eingeloggt ist
def pruefe_student(rolle):
    if rolle != 'stud':
        return False

    return True

# Schauen ob es eine User_id in der Session gibt
def hole_user_und_rolle():
    user_id = session.get('user_id')
    if not user_id:
        return None, None
    user_id = int(user_id)
    rolle = get_user_role(user_id)
    return user_id, rolle

# Prüfen ob das Thema belegt werden kann und ib der Student noch kein Thema belegt hat
def thema_belegen_pruefen(thema, user_id):
    # Liste der s_ids, die schon ein Thema belegt haben
    studenten_ids = [row['s_id'] for row in get_sid_aus_themen() if row['s_id'] is not None]

    # Belegbar nur wenn: Thema hat noch keinen Studenten,
    # Status ist Frei, UND der Student belegt noch kein anderes Thema
    if not thema['s_id'] and thema['status'] == 'Frei' and user_id not in studenten_ids:
        return True
    else:
        return False

# Speichert ein hochgeladenes PDF und gibt den gespeicherten Dateinamen zurück.
# Gibt None zurück, wenn keine Datei hochgeladen wurde.
def speichere_pdf(pdf):
    if not pdf or pdf.filename == '':
        return None
    dateiname = secure_filename(pdf.filename)
    pdf.save(os.path.join('static/uploads', dateiname))
    return dateiname



