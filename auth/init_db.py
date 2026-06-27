#Author Deniz Rahnefeld (409637)
import db
from auth.utils import hash_passwort

with db.connect_to_db() as conn:
    with conn.cursor() as cur:

        cur.execute('DROP TABLE IF EXISTS studierende CASCADE')
        cur.execute('DROP TABLE IF EXISTS dozierende CASCADE')
        cur.execute('DROP TABLE IF EXISTS account CASCADE')


        # language=PostgreSQL
        cur.execute('DROP TYPE IF EXISTS STUD_TYPE CASCADE')
        # language=PostgreSQL
        cur.execute('DROP TYPE IF EXISTS ABSCHLUSS_TYPE CASCADE')
        # language=PostgreSQL
        cur.execute('DROP TYPE IF EXISTS SEMINARE CASCADE')
        # language=PostgreSQL
        cur.execute('DROP TYPE IF EXISTS ROLLEN CASCADE')
        # language=PostgreSQL
        cur.execute('DROP TYPE IF EXISTS ANREDE_TYPE CASCADE')

        # language=PostgreSQL
        cur.execute("CREATE TYPE STUD_TYPE AS ENUM ('WINF', 'IMIT', 'AI', 'IIM', 'IKU')")
        # language=PostgreSQL
        cur.execute("CREATE TYPE ABSCHLUSS_TYPE AS ENUM ('B.Sc', 'M.Sc')")
        # language=PostgreSQL
        cur.execute("CREATE TYPE SEMINARE AS ENUM ('IIS', 'WBS')")
        # language=PostgreSQL
        cur.execute("CREATE TYPE ROLLEN AS ENUM ('doz', 'stud')")
        # language=PostgreSQL
        cur.execute("CREATE TYPE ANREDE_TYPE AS ENUM ('Prof. Dr.', 'Dr.', '')")


        cur.execute("CREATE TABLE account (id SERIAL PRIMARY KEY, "
                    "email VARCHAR(255) UNIQUE NOT NULL, "
                    "passwort VARCHAR(255) NOT NULL, "
                    "rolle ROLLEN NOT NULL)")


        cur.execute("CREATE TABLE studierende (s_id INT PRIMARY KEY, "
                    "matr_nr VARCHAR(8) UNIQUE, "
                    "vorname VARCHAR(255) NOT NULL, "
                    "nachname VARCHAR(255) NOT NULL, "
                    "studiengang_name STUD_TYPE NOT NULL, "
                    "abschluss ABSCHLUSS_TYPE NOT NULL, "
                    "bel_seminar SEMINARE NOT NULL, "
                    "FOREIGN KEY (s_id) REFERENCES account(id) ON DELETE CASCADE)")

        cur.execute("CREATE TABLE dozierende (d_id INT PRIMARY KEY, "
                    "anrede ANREDE_TYPE, "
                    "vorname VARCHAR(255) NOT NULL, "
                    "nachname VARCHAR(255) NOT NULL, "
                    "FOREIGN KEY (d_id) REFERENCES account(id) ON DELETE CASCADE)")



        ###################Dozierende#################################
        cur.execute('INSERT INTO account (email, passwort, rolle) '
                    'VALUES (%s, %s, %s) '
                    'RETURNING id',
                    ('althoff@uni-hildesheim.de',
                     hash_passwort('Passwort!123'),
                     'doz'))
        acc_id = cur.fetchone()['id']

        cur.execute("INSERT INTO dozierende (d_id, anrede, vorname, nachname)"
                    "VALUES (%s, %s, %s, %s)",
                    (acc_id,
                     'Prof. Dr.',
                     'Klaus-Dieter',
                     'Althoff'))


        cur.execute('INSERT INTO account (email, passwort, rolle) '
                    'VALUES (%s, %s, %s) '
                    'RETURNING id',
                    ('reusspa@uni-hildesheim.de',
                      hash_passwort('Passwort!123'),
                     'doz'))
        acc_id = cur.fetchone()['id']

        cur.execute("INSERT INTO dozierende (d_id, anrede, vorname, nachname)"
                    "VALUES (%s, %s, %s, %s)",
                    (acc_id,
                     'Dr.',
                     'Pascal',
                     'Reuss'))


        cur.execute('INSERT INTO account (email, passwort, rolle) '
                    'VALUES (%s, %s, %s) '
                    'RETURNING id',
                    ('schoenb@uni-hildesheim.de',
                      hash_passwort('Passwort!123'),
                     'doz'))
        acc_id = cur.fetchone()['id']

        cur.execute("INSERT INTO dozierende (d_id, anrede, vorname, nachname)"
                    "VALUES (%s, %s, %s, %s)",
                    (acc_id,
                     '',
                     'Jakob Michael',
                     'Schönborn'))

        conn.commit()
