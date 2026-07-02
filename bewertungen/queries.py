#Author Tim Deppe (413323)
import db

#with db.connect_to_db() as conn:
#   with conn.cursor() as cur:   für db zugriff

def is_seminar_vorgetragen(themen_id):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            vorgetragen = True
            cur.execute("SELECT vorgetragen FROM seminarthema WHERE themen_id = %s", (int(themen_id),))
            result = cur.fetchone()

            if result:
                vorgetragen = result['vorgetragen']
            if vorgetragen == 'False':
                vorgetragen = False

            return vorgetragen