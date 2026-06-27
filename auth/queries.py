#Author Deniz Rahnefeld (409637)
import db
from auth.utils import hash_passwort


def check_account(data) -> bool:
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            acc_exists = False

            email = data.get("email", '').strip()
            cur.execute("SELECT email FROM account WHERE email = %s", (email,))
            result = cur.fetchone()

            if result is not None:
                acc_exists = True

            return acc_exists


def create_user(data):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:

            #Zunächst Account erstellen
            passwort_hash = hash_passwort(data.get("passwort", ''))
            cur.execute('INSERT INTO account (email, passwort, rolle) '
                        'VALUES (%s, %s, %s) '
                        'RETURNING id',
                        (data.get("email", ''),
                         passwort_hash,
                         'stud'))
            acc_id = cur.fetchone()['id']

            #Studenten Informationen speichern
            cur.execute("INSERT INTO studierende (s_id, matr_nr, vorname, nachname, "
                        "studiengang_name, abschluss, bel_seminar)"
                        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (acc_id,
                         data.get("matr_nr", ''),
                         data.get("vorname", ''),
                         data.get("nachname", ''),
                         data.get('studiengang_name', ''),
                         data.get('abschluss', ''),
                         data.get('bel_seminar', ''),))

            #Optional Seminar_thema belegen
            themen_id = data.get("seminar_thema", '').strip()
            if themen_id :
                    cur.execute("UPDATE seminarthema SET s_id = %s, status = 'Vergeben' "
                                "WHERE themen_id = %s ",
                                (acc_id,
                                int(themen_id),))
            conn.commit()

#Diese Funktion gibt bei richtigem Passwort die User_ID zurück, um diese in der
#   Session zu speichern und später mit der DB abzugleichen.
#TODO Dieser Version funtkioniert mit gehashten Passwörtern -> Fragen ob erlaubt ist.
def check_password(data)-> int | None:
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            user_id = None
            email = data.get("email", '').strip()
            inp_passwort = data.get("passwort", '')

            cur.execute("SELECT passwort FROM account WHERE email = %s", (email,))

            result = cur.fetchone()
            if result:
                passwort = result['passwort']
            else:
                passwort = None

            #Nur wenn das Passwort übereinstimmt, wird die user_id zurückgegeben.
            # Ohne user_id merkt sich die Session nicht, dass man eingeloggt ist.
            if hash_passwort(inp_passwort) == passwort:
                cur.execute("SELECT id FROM account WHERE email = %s", (email,))
                user_id = cur.fetchone()[0]

            return user_id #Kann None sein und somit False in If-Abfragen

def get_user_role(user_id):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT rolle FROM account WHERE id = %s", (user_id,))

            result = cur.fetchone()
            if result:
                user_role = result['rolle']
            else:
                user_role = None

            return user_role

def get_user_info(user_id):

    rolle = get_user_role(user_id)
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:

            if rolle == 'doz':
                cur.execute("SELECT d.anrede, d.vorname, d.nachname, a.email "
                            "FROM dozierende d JOIN account a ON (d.d_id = a.id) WHERE d.d_id = %s", (user_id,))
            elif rolle == 'stud':
                cur.execute("SELECT s.vorname, s.nachname, s.studiengang_name, s.abschluss, s.bel_seminar"
                            "FROM studierende s JOIN account a ON (d.d_id = a.id) WHERE d.d_id = %s", (user_id,))
            else:
                pass

def get_seminarthemen():
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT themen_id, titel FROM seminarthema")
            result = cur.fetchall()
            return result

def check_seminarthema(themen_id)-> bool:
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT titel FROM seminarthema WHERE themen_id = %s", (int(themen_id),))

            result = cur.fetchone()
            thema_exists = False
            if result:
                thema_exists = True

            return thema_exists

def is_seminar_occupied(themen_id):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            occupied = True
            cur.execute("SELECT status FROM seminarthema WHERE themen_id = %s", (int(themen_id),))
            result = cur.fetchone()

            if result:
                status = result['status']
                if status == 'Frei':
                    occupied = False

            return occupied


