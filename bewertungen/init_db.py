#Author Tim Deppe (413323)
import db

with db.connect_to_db() as conn:
    with conn.cursor() as cur:

        cur.execute('DROP TABLE IF EXISTS bew_vortrag CASCADE')
        cur.execute('DROP TABLE IF EXISTS bew_ausarbeitung CASCADE')
        cur.execute('DROP TABLE IF EXISTS seminarleistung CASCADE')

        # language=PostgreSQL
        cur.execute('DROP TYPE IF EXISTS BEWERTUNGSSKALA CASCADE')

        # language=PostgreSQL
        cur.execute("CREATE TYPE BEWERTUNGSSKALA AS ENUM ('1', '2', '3', '4', '5')")

        cur.execute("CREATE TABLE bew_vortrag (bv_id = SERIAL PRIMARY KEY,"
                    "FOREIGN KEY (themen_id) REFERENCES seminarthema(themen_id) ON DELETE CASCADE,)")
        cur.execute("CREATE TABLE bew_ausarbeitung (ba_id = SERIAL PRIMARY KEY,"
                    "FOREIGN KEY (themen_id) REFERENCES seminarthema(themen_id) ON DELETE CASCADE,)")
        cur.execute("CREATE TABLE seminarleistung (bs_id = SERIAL PRIMARY KEY,"
                    "FOREIGN KEY (themen_id) REFERENCES seminarthema(themen_id) ON DELETE CASCADE,)")


        conn.commit()