#Author Tim Deppe (413323)
import db
import psycopg

#with db.connect_to_db() as conn:
#   with conn.cursor() as cur:   für db zugriff

#Gibt den Wahrheitswert zurück, ob ein Vortrag zu dem Seminarthema bereits gegeben wurde
def is_seminar_vorgetragen(themen_id):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:

            cur.execute("SELECT vorgetragen FROM seminarthema WHERE themen_id = %s", (int(themen_id),))
            vorgetragen = cur.fetchone()

            if not vorgetragen:
                return False

            return bool(vorgetragen["vorgetragen"])

#Gibt jede Vortragsbewertung zurück, die zu einem bestimmten Vortrag gemacht wurde
def get_bew_vortrag(themen_id):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:

            cur.execute("SELECT * FROM bew_vortrag WHERE t_id = %s", (int(themen_id),))

            result = cur.fetchall()
            if result:
                return result
            return None

BEWERTUNGSSKALA = {
    1: '1',
    2: '2',
    3: '3',
    4: '4',
    5: '5',
}

def _bewertungsskala_wert(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return None

    return BEWERTUNGSSKALA.get(value)

#Erstellt eine neue Vortragsbewertung
def create_bew_vortrag(data):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:

            erlaubt = is_seminar_vorgetragen(data.get('t_id'))
            if not erlaubt:
                return False

            bewertungen = [
                _bewertungsskala_wert(data.get("foliengestaltung")),
                _bewertungsskala_wert(data.get("sprachliche_praesentation")),
                _bewertungsskala_wert(data.get("stil")),
                _bewertungsskala_wert(data.get("zeitliche_gestaltung")),
                _bewertungsskala_wert(data.get("verstaendnis")),
                _bewertungsskala_wert(data.get("inhalt")),
                _bewertungsskala_wert(data.get("verknuepfung")),
                _bewertungsskala_wert(data.get("diskussion")),
                _bewertungsskala_wert(data.get("beteiligung")),
            ]

            if any(wert is None for wert in bewertungen):
                return False

            try:
                cur.execute(
                    "INSERT INTO bew_vortrag ("
                    "t_id, bewertender_id, foliengestaltung, sprachliche_praesentation, "
                    "stil, zeitliche_gestaltung, verstaendnis, inhalt, verknuepfung, "
                    "diskussion, beteiligung, kommentar) "
                    "VALUES (%s, %s, CAST(%s AS bewertungsskala), CAST(%s AS bewertungsskala),"
                    "CAST(%s AS bewertungsskala), CAST(%s AS bewertungsskala), CAST(%s AS bewertungsskala),"
                    "CAST(%s AS bewertungsskala), CAST(%s AS bewertungsskala), CAST(%s AS bewertungsskala),"
                    "CAST(%s AS bewertungsskala), %s"
                    ")",
                    (data.get("t_id"),
                        data.get("bewertender_id"),
                        *bewertungen,
                        data.get("kommentar") or None,))
                conn.commit()
                return True

            except psycopg.errors.UniqueViolation:
                conn.rollback()
                return "bereits_bewertet"

def get_bewertbare_vortraege(exclude_account_id=None):
    """
    Liefert alle Seminarthemen mit Status 'vergeben' und vorgetragen = TRUE,
    inkl. Titel sowie Vor- und Nachname des vortragenden Studierenden.
    Über exclude_account_id kann der eigene Vortrag (falls vorhanden)
    direkt aus der Auswahl ausgeblendet werden.
    """
    with db.connect_to_db() as conn:
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT st.themen_id, st.titel, s.vorname, s.nachname
                    FROM seminarthema st
                    JOIN studierende s ON st.s_id = s.s_id
                    WHERE st.status = 'Vergeben' AND st.vorgetragen = TRUE
                """
                params = []
                if exclude_account_id is not None:
                    query += " AND st.s_id != %s"
                    query += " AND st.themen_id NOT IN (SELECT t_id FROM bew_vortrag WHERE bewertender_id = %s)"
                    params.extend([exclude_account_id, exclude_account_id])
                query += " ORDER BY s.nachname, s.vorname"

                cur.execute(query, params)
                rows = cur.fetchall()
                return [
                    {'t_id': r['themen_id'], 'titel': r['titel'], 'vorname': r['vorname'],
                        'nachname': r['nachname']}
                    for r in rows
                ]
        finally:
            conn.close()


def ist_vortrag_bewertbar(t_id, account_id=None):
    """
    Prüft serverseitig, ob t_id aktuell tatsächlich Status 'vergeben'
    und vorgetragen = TRUE hat. Notwendig, da ein Dropdown-Wert im
    POST-Request manipuliert werden könnte (z. B. per curl).
    """
    with db.connect_to_db() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                SELECT 1 FROM seminarthema
                WHERE themen_id = %s AND status = 'Vergeben' AND vorgetragen = TRUE
                AND themen_id NOT IN (
                    SELECT t_id FROM bew_vortrag WHERE bewertender_id = %s
                )
                """,
                (t_id, account_id)
                )
                return cur.fetchone() is not None
        finally:
            conn.close()

def ist_eigener_vortrag(t_id, account_id):
    """
    Prüft, ob der Studierende mit gegebener account_id selbst der
    Vortragende des Seminarthemas t_id ist.
    Gibt True zurück, wenn es sich um den eigenen Vortrag handelt,
    sonst False (z. B. auch dann, wenn account_id zu einem Dozenten gehört,
    da der JOIN dann keinen Treffer liefert).
    """
    with db.connect_to_db() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1
                    FROM seminarthema st
                    JOIN studierende s ON st.s_id = s.s_id
                    WHERE st.themen_id = %s AND s.s_id = %s
                    """,
                    (t_id, account_id)
                )
                return cur.fetchone() is not None
        finally:
            conn.close()

# Abfrage für Test Seminarthema. Es wird eine s_id aus der Datenbank mittels LIMIT 1 gezogen
def get_test_student_id():
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT s_id FROM studierende LIMIT 1")
            # fetchone speichert ein dictionary {'s_id', 3}
            result = cur.fetchone()
    # Rückgabe des Wertes der Studierenden id
    if result:
        return result['s_id']
    return None