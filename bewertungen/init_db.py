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

        cur.execute("CREATE TABLE bew_vortrag (bv_id SERIAL PRIMARY KEY,"
                    "t_id INT NOT NULL,"
                    "bewertender_id INT NOT NULL,"
                    "foliengestaltung BEWERTUNGSSKALA NOT NULL,"
                    "sprachliche_praesentation BEWERTUNGSSKALA NOT NULL,"
                    "stil BEWERTUNGSSKALA NOT NULL,"
                    "zeitliche_gestaltung BEWERTUNGSSKALA NOT NULL,"
                    "verstaendnis BEWERTUNGSSKALA NOT NULL,"
                    "inhalt BEWERTUNGSSKALA NOT NULL,"
                    "verknuepfung BEWERTUNGSSKALA NOT NULL,"
                    "diskussion BEWERTUNGSSKALA NOT NULL,"
                    "beteiligung BEWERTUNGSSKALA NOT NULL,"
                    "kommentar TEXT,"
                    "FOREIGN KEY (t_id) REFERENCES seminarthema(themen_id) ON DELETE CASCADE,"
                    "FOREIGN KEY (bewertender_id) REFERENCES account(id) ON DELETE CASCADE,"
                    "CONSTRAINT eine_bewertung_pro_acc UNIQUE (t_id, bewertender_id))")
        cur.execute("CREATE TABLE bew_ausarbeitung (ba_id SERIAL PRIMARY KEY,"
                    "t_id INT NOT NULL,"
                    "umfang BEWERTUNGSSKALA NOT NULL,"
                    "referenzen BEWERTUNGSSKALA NOT NULL,"
                    "sprachliche_gestaltung BEWERTUNGSSKALA NOT NULL,"
                    "inhalt BEWERTUNGSSKALA NOT NULL,"
                    "schwierigkeitsgrad BEWERTUNGSSKALA NOT NULL,"
                    "kommentar TEXT,"
                    "FOREIGN KEY (t_id) REFERENCES seminarthema(themen_id) ON DELETE CASCADE,"
                    "CONSTRAINT eine_bewertung_pro_ausarbeitung UNIQUE (t_id))")
        cur.execute("CREATE TABLE seminarleistung (t_id INT PRIMARY KEY,"
                    "note DECIMAL(2,1) NOT NULL "
                        "CHECK (note IN (1.0, 1.3, 1.7, 2.0, 2.3, 2.7, 3.0, 3.3, 3.7, 4.0, 5.0)),"
                    "FOREIGN KEY (t_id) REFERENCES seminarthema(themen_id) ON DELETE CASCADE)")

        conn.commit()