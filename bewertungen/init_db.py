#Author Tim Deppe (413323)
import db

with db.connect_to_db() as conn:
    with conn.cursor() as cur:

        cur.execute('DROP TABLE IF EXISTS bewertungen')

        conn.commit()