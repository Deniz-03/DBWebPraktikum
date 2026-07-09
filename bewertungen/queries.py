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

#Erstellt eine neue Vortragsbewertung
def create_bew_vortrag(data):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:

            erlaubt = is_seminar_vorgetragen(data.get('t_id'))
            if not erlaubt:
                return False

            try:
                cur.execute(
                    "INSERT INTO bew_vortrag ("
                    "t_id, bewertender_id, foliengestaltung, sprachliche_praesentation, "
                    "stil, zeitliche_gestaltung, verstaendnis, inhalt, verknuepfung, "
                    "diskussion, beteiligung, kommentar) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (data.get("t_id"),
                        data.get("bewertender_id"),
                        data.get("foliengestaltung"),
                        data.get("sprachliche_praesentation"),
                        data.get("stil"),
                        data.get("zeitliche_gestaltung"),
                        data.get("verstaendnis"),
                        data.get("inhalt"),
                        data.get("verknuepfung"),
                        data.get("diskussion"),
                        data.get("beteiligung"),
                        data.get("kommentar") or None,)
                    )
                conn.commit()
                return True

            except psycopg.errors.UniqueViolation:
                conn.rollback()
                return "bereits_bewertet"

#Gibt alle Seminarthemen (t_id, Titel, Name des Vortragenden) aus, die bewertbar bzw. vergeben und vorgetragen sind.
#Zusätzlich werden Seminarthemen die dem angemeldeten Nutzer zugeweiesen sind ausgefiltert, da er diese nicht bewerten
#darf.
def get_bewertbare_vortraege(exclude_account_id=None):
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

#Hilfsfunktion um zu prüfen ob ein Seminarthema vergeben sowie vorgetragen wurde. Zusätzlich werden die Seminarthemen
#ausgefiltert, dessen Vorträge vom angemeldeten Nutzern bereits bewertet wurden
def ist_vortrag_bewertbar(t_id, account_id=None):
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

#Hilfsfunktion um zu prüfen ob angemeldeter Nutzer der Vortragende des Seminarthemas t_id ist.
#Gibt True nur dann zurück, wenn der Nutzer der Vortragende ist, sonst False.
def ist_eigener_vortrag(t_id, account_id):
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

# Abfrage für Test Seminarthema. Es wird genau eine s_id aus der Datenbank gezogen
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

#Gibt mit Angabe einer s_id eine dict aus mit der Anzahl an Bewertungen von Vorträgen vom Studierenden gehalten,
#sowie die Durchschnittsbewertung jeder Kategorie.
def get_bewertungsstatistik(s_id):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    SELECT COUNT(*)                                 AS anzahl_bewertungen,
                           ROUND(AVG(foliengestaltung), 2)          AS foliengestaltung,
                           ROUND(AVG(sprachliche_praesentation), 2) AS sprachliche_praesentation,
                           ROUND(AVG(stil), 2)                      AS stil,
                           ROUND(AVG(zeitliche_gestaltung), 2)      AS zeitliche_gestaltung,
                           ROUND(AVG(verstaendnis), 2)              AS verstaendnis,
                           ROUND(AVG(inhalt), 2)                    AS inhalt,
                           ROUND(AVG(verknuepfung), 2)              AS verknuepfung,
                           ROUND(AVG(diskussion), 2)                AS diskussion,
                           ROUND(AVG(beteiligung), 2)               AS beteiligung
                    FROM bewertung_vortrag bv
                             JOIN seminarthema st ON bv.t_id = st.themen_id
                    WHERE st.s_id = %s
                    """,
                    (s_id,)
                )
                row = cur.fetchone()
                spalten = [
                    'anzahl_bewertungen', 'foliengestaltung', 'sprachliche_praesentation',
                    'stil', 'zeitliche_gestaltung', 'verstaendnis', 'inhalt',
                    'verknuepfung', 'diskussion', 'beteiligung'
                ]
                return dict(zip(spalten, row))
            finally:
                conn.close()