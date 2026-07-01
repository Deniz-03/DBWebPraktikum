#Author Tim Deppe (413323)
import db

#with db.connect_to_db() as conn:
#   with conn.cursor() as cur:   für db zugriff

"""
def is_seminar_vorgetragen(themen_id):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            vorgetragen = True
            cur.execute("SELECT placehold FROM seminarthema WHERE themen_id = %s", (int(themen_id),))
            result = cur.fetchone()

            if result:"""
#TODO: placehold mit vorgetragen spaltennamen aus seminarthemen ersetzen
"""             placehold = result['placehold']
                if placehold == 'False':
                    vorgetragen = False

            return vorgetragen"""