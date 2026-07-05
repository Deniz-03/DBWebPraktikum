#Author Tim Deppe (413323)
import db
import psycopg

#with db.connect_to_db() as conn:
#   with conn.cursor() as cur:   für db zugriff

#Gibt den Wahrheitswert an, ob ein Vortrag zu dem Seminarthema bereits gegeben wurde
def is_seminar_vorgetragen(themen_id):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:

            cur.execute("SELECT vorgetragen FROM seminarthema WHERE themen_id = %s", (int(themen_id),))
            vorgetragen = cur.fetchone()

            return vorgetragen

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
                return erlaubt

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
                     data.get('sprachliche_praesentation'),
                     data.get('stil'),
                     data.get('zeitliche_gestaltung'),
                     data.get('verstaendnis'),
                     data.get('inhalt'),
                     data.get('verknuepfung'),
                     data.get('diskussion'),
                     data.get('beteiligung'),
                     data.get('kommentar') or None,))
                conn.commit()
                return erlaubt
            except psycopg.errors.UniqueViolation:
                conn.rollback()
                return "bereits_bewertet"