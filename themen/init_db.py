#Author Peer Schulze (410246)

import db
from themen.queries import get_test_dozent_id

with db.connect_to_db() as conn:
    with conn.cursor() as cur:

        cur.execute('DROP TABLE IF EXISTS seminarthema CASCADE')

        #Enum erstellen, da es innerhalb des Create Table statements nicht möglich ist
        cur.execute("DROP TYPE IF EXISTS STATUS_TYPE CASCADE")
        cur.execute("CREATE TYPE STATUS_TYPE AS ENUM ('Frei', 'Vergeben', 'Abgeschlossen')")

        #String existiert nicht daher varchar(255)
        cur.execute("CREATE TABLE seminarthema (themen_id SERIAL PRIMARY KEY, "
                    "titel VARCHAR(255)  NOT NULL,"
                    "d_id INT NOT NULL,"
                    "status STATUS_TYPE NOT NULL DEFAULT 'Frei',"
                    "oberbegriff VARCHAR(255) NOT NULL," 
                    "beschreibung TEXT NOT NULL,"
                    "s_id INT NULL,"
                    "semester INT,"
                    "pdf_pfad VARCHAR(255),"
                    "vorgetragen BOOLEAN NOT NULL DEFAULT false,"
                    "FOREIGN KEY (d_id) REFERENCES dozierende(d_id) ON DELETE CASCADE,"
                    "FOREIGN KEY (s_id) REFERENCES studierende(s_id) ON DELETE SET NULL)")

        conn.commit()

        # Test Themen
        dozent_id = get_test_dozent_id()

        cur.execute(
            "INSERT INTO seminarthema (titel, d_id, oberbegriff, beschreibung, s_id, semester) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            ('Peter Pan', dozent_id, 'Phantasie', 'eine Folge schreiben', None, 4)
        )

        cur.execute(
            "INSERT INTO seminarthema (titel, d_id, oberbegriff, beschreibung, s_id, semester) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            ('Star Wars', dozent_id, 'Galaxis', 'Beschreibe die Schlacht auf Geonosis', None, 6)
        )

        conn.commit()
