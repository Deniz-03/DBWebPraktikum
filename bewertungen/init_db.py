#Author Tim Deppe (413323)
import db

with db.connect_to_db() as conn:
    with conn.cursor() as cur:

        cur.execute('DROP TABLE IF EXISTS bew_vortrag CASCADE')
        cur.execute('DROP TABLE IF EXISTS bew_ausarbeitung CASCADE')
        cur.execute('DROP TABLE IF EXISTS seminarleistung CASCADE')

        # language=PostgreSQL
        cur.execute('DROP TYPE IF EXISTS BEWERTUNGSSKALA CASCADE')

        cur.execute("CREATE TABLE bew_vortrag (bv_id SERIAL PRIMARY KEY,"
                    "t_id INT NOT NULL,"
                    "bewertender_id INT NOT NULL,"
                    "foliengestaltung SMALLINT NOT NULL,"
                    "sprachliche_praesentation SMALLINT NOT NULL,"
                    "stil SMALLINT NOT NULL,"
                    "zeitliche_gestaltung SMALLINT NOT NULL,"
                    "verstaendnis SMALLINT NOT NULL,"
                    "inhalt SMALLINT NOT NULL,"
                    "verknuepfung SMALLINT NOT NULL,"
                    "diskussion SMALLINT NOT NULL,"
                    "beteiligung SMALLINT NOT NULL,"
                    "kommentar TEXT,"
                    "FOREIGN KEY (t_id) REFERENCES seminarthema(themen_id) ON DELETE CASCADE,"
                    "FOREIGN KEY (bewertender_id) REFERENCES account(id) ON DELETE CASCADE,"
                    "CONSTRAINT eine_bewertung_pro_acc UNIQUE (t_id, bewertender_id),"
                    "CONSTRAINT chk_foliengestaltung CHECK (foliengestaltung BETWEEN 1 AND 5),"
                    "CONSTRAINT chk_sprachliche_praesentation CHECK (sprachliche_praesentation BETWEEN 1 AND 5),"
                    "CONSTRAINT chk_stil CHECK (stil BETWEEN 1 AND 5),"
                    "CONSTRAINT chk_zeitliche_gestaltung CHECK (zeitliche_gestaltung BETWEEN 1 AND 5),"
                    "CONSTRAINT chk_verstaendnis CHECK (verstaendnis BETWEEN 1 AND 5),"
                    "CONSTRAINT chk_inhalt CHECK (inhalt BETWEEN 1 AND 5),"
                    "CONSTRAINT chk_verknuepfung CHECK (verknuepfung BETWEEN 1 AND 5),"
                    "CONSTRAINT chk_diskussion CHECK (diskussion BETWEEN 1 AND 5),"
                    "CONSTRAINT chk_beteiligung CHECK (beteiligung BETWEEN 1 AND 5))")
        cur.execute("CREATE TABLE bew_ausarbeitung (ba_id SERIAL PRIMARY KEY,"
                    "t_id INT NOT NULL,"
                    "umfang SMALLINT NOT NULL,"
                    "referenzen SMALLINT NOT NULL,"
                    "sprachliche_gestaltung SMALLINT NOT NULL,"
                    "inhalt SMALLINT NOT NULL,"
                    "schwierigkeitsgrad SMALLINT NOT NULL,"
                    "kommentar TEXT,"
                    "FOREIGN KEY (t_id) REFERENCES seminarthema(themen_id) ON DELETE CASCADE,"
                    "CONSTRAINT eine_bewertung_pro_ausarbeitung UNIQUE (t_id),"
                    "CONSTRAINT chk_umfang CHECK (umfang BETWEEN 1 AND 5),"
                    "Constraint chk_referenzen CHECK (referenzen BETWEEN 1 AND 5),"
                    "CONSTRAINT chk_sprachliche_gestaltung CHECK (sprachliche_gestaltung BETWEEN 1 AND 5),"
                    "CONSTRAINT chk_inhalt CHECK (inhalt BETWEEN 1 AND 5),"
                    "CONSTRAINT chk_schwierigkeitsgrad CHECK (schwierigkeitsgrad BETWEEN 1 AND 5))")
        cur.execute("CREATE TABLE seminarleistung (t_id INT PRIMARY KEY,"
                    "note DECIMAL(2,1) NOT NULL "
                    "CHECK (note IN (1.0, 1.3, 1.7, 2.0, 2.3, 2.7, 3.0, 3.3, 3.7, 4.0, 5.0)),"
                    "FOREIGN KEY (t_id) REFERENCES seminarthema(themen_id) ON DELETE CASCADE)")

        conn.commit()