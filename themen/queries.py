#Author Peer Schulze (410246)
import db

# Auslesen aller Dozierenden für das Dropdown menü zum wechseln des verantwortlichen Dozierenden
def get_dozierenden():
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT d_id, vorname, nachname FROM dozierende ORDER BY nachname")
            return cur.fetchall()

# Dozent mittels ID ermitteln
def get_dozent_by_id(d_id):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT d_id, vorname, nachname FROM dozierende WHERE d_id=%s",
                        (d_id,))
            return cur.fetchone()

# Datenbank eintrag für ein neues Seminarthema
# Mit None sind alle Felder markiert die nicht verpflichtend sind
def thema_anlegen(titel, d_id, oberbegriff, beschreibung, s_id=None, semester=None, pdf_pfad=None):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO seminarthema (titel, d_id, oberbegriff, beschreibung, s_id,"
                        " semester, pdf_pfad) "
                        "VALUES(%s, %s, %s, %s, %s, %s, %s)",
                        (titel, d_id, oberbegriff, beschreibung, s_id, semester, pdf_pfad)
            )
        conn.commit()

# Holt das Seminarthema und alle dazugehörigen Attribute zu einer bestimmten Themen_id
def get_seminarthema(themen_id):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM seminarthema WHERE themen_id=%s",
                        (themen_id,))
            return cur.fetchone()

# Bearbeiten von Themen. Wird so umgesetzt das alle nicht geänderten Werte automatisch durch das Template
# weitergegeben werden
def thema_bearbeiten(themen_id, titel, d_id, oberbegriff, beschreibung, s_id, status, semester, pdf_pfad, vorgetragen):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE seminarthema SET titel=%s, d_id=%s, oberbegriff=%s, beschreibung=%s, "
                        "s_id=%s, status=%s, semester=%s, pdf_pfad=%s, vorgetragen=%s WHERE themen_id=%s",
                        (titel, d_id, oberbegriff, beschreibung, s_id, status, semester,
                         pdf_pfad, vorgetragen, themen_id)
            )
        conn.commit()

# Anzeigen des Studenten der sich für das Seminarthema entschieden hat
def student_hinzufuegen(themen_id, s_id, status):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE seminarthema SET s_id=%s, status=%s WHERE themen_id=%s "
                        "AND s_id is NULL AND status='Frei'",
                        (s_id, status, themen_id)
            )
            erfolgreich = False
            if cur.rowcount == 1:
                erfolgreich = True

        conn.commit()

        # Liefert True wenn die beiden Spalten in dem einen Seminarthema geändert wurden
        return erfolgreich

# Namen und Link des Studierenden der später im Seminarthema angezeigt wird
def get_student_by_id(s_id):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT s_id, matr_nr, vorname, nachname FROM studierende WHERE s_id=%s",
                        (s_id,))
            return cur.fetchone()

# Gibt Studenten mit spezifischer Matrikelnummer zurück
def get_student_by_matr_nr(matr_nr):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT s_id, matr_nr, vorname, nachname FROM studierende WHERE matr_nr=%s",
                        (matr_nr,))
            return cur.fetchone()

# Alle eingetragenen s_ids die es in den Seminarthemen gibt
def get_sid_aus_themen():
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT s_id FROM seminarthema")
            return cur.fetchall()

# Abfrage zum Holen aller Seminarthemen die auf die enstprechend gesetzten Filter passen.
# Alle Filter=None da wenn kein Filter gesetzt wurde keine Filterung gemacht werden soll
def get_seminarthemen_by_filter(titel=None, d_id=None, oberbegriff=None, beschreibung=None,
                            s_id=None, semester=None, status=None):
    # Standard abfrage, um alle Seminarthemen zu erhalten
    query = ("SELECT sem.themen_id, sem.titel, sem.semester, sem.status, "
             "d.vorname AS doz_vorname, d.nachname AS doz_nachname "
             "FROM seminarthema sem "
             "JOIN dozierende d ON sem.d_id = d.d_id "
             "LEFT JOIN studierende s ON sem.s_id = s.s_id ")

    bedingungen = []
    werte = []

    # Nach Filterungen schauen und diese dem wert hinzufügen
    # Der Bedingung wird die Where Bedingung für diese Anforderung gesetzt
    if titel:
        bedingungen.append("sem.titel ILIKE %s")
        werte.append(f"%{titel}%")
    if d_id:
        bedingungen.append("sem.d_id = %s")
        werte.append(d_id)
    if oberbegriff:
        bedingungen.append("sem.oberbegriff ILIKE %s")
        werte.append(f"%{oberbegriff}%")
    if beschreibung:
        bedingungen.append("sem.beschreibung ILIKE %s")
        werte.append(f"%{beschreibung}%")
    if s_id:
        bedingungen.append("s.vorname || ' ' || s.nachname ILIKE %s")
        werte.append(f'%{s_id}%')
    if semester:
        bedingungen.append("sem.semester = %s")
        werte.append(semester)
    if status:
        bedingungen.append("sem.status = %s")
        werte.append(status)

    if bedingungen:
        # Die query kriegt eine Where Klausel mit allen in Bedingungen hinzugefügten Klauseln.
        # Diese werden mittels AND verknüpft
        query += " WHERE " + " AND ".join(bedingungen)
    query += " ORDER BY sem.semester, sem.titel"

    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            # Die fertige Abfrage. Vollständige Query und die Werte die für die %s Platzhalter
            # eingesetzt werden, werden mittels Tupel angehängt
            cur.execute(query, tuple(werte))
            return cur.fetchall()

# Gibt alle Semester zurück für das Dropdown menü
def get_semester():
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT semester FROM seminarthema WHERE semester IS NOT NULL ORDER BY semester")
            return cur.fetchall()

# Gibt alle möglichen Statuswerte des Enums für das Dropdown Menü zurück.
# enum_range(NULL::STATUS_TYPE) liefert alle Werte des Enum-Typs in Definitionsreihenfolge,
# unnest macht aus dem Array einzelne Zeilen
def get_status_optionen():
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT unnest(enum_range(NULL::STATUS_TYPE)) AS status")
            return cur.fetchall()

# Setzt das Seminarthema auf Frei wenn die s_id eines Studenten rausgenommen wird.
def set_free(themen_id):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE seminarthema SET s_id = NULL, status = 'Frei'"
                        "WHERE themen_id = %s",
                        (themen_id,))





# Abfrage für Test Seminarthema. Es wird eine d_id aus der Datenbank mittels LIMIT 1 gezogen
def get_test_dozent_id():
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT d_id FROM dozierende LIMIT 1")
            # fetchone speichert ein dictionary {'d_id', 3}
            result = cur.fetchone()
    # Rückgabe des Wertes der Dozierenden id
    return result['d_id']



