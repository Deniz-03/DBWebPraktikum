#Author Deniz Rahnefeld (409637)
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from auth.queries import *
from auth.utils import *
from bewertungen.utils import *

auth_bp = Blueprint('auth', __name__, template_folder='templates')

@auth_bp.route('/')
def index():
    if 'user_id' in session:
        user_id = int(session.get('user_id', '-1'))
        rolle = get_user_role(user_id)
        if rolle is None:
            flash('Fehler beim laden der Session', 'error')
        return render_template('index.html', rolle=rolle)
    else:
        return render_template("index.html")

#Um zu prüfen, ob ein Nutzer angemeldet ist, wird geschaut,
# ob eine user_id in der Session enthalten ist.
#Ein User ist angemeldet genau dann, wenn eine user_id in der Session vermerkt ist.
#Diese user_id kann dann verwendet werden, um userspezifische Informationen aus der DB
# abzufragen.
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect(url_for('auth.profile'))
        else:
            return render_template('auth/login.html', values={})

    else:
        data = request.form

        empty_input_found, leere_felder = check_login_input(data)
        if empty_input_found:
            for feld in leere_felder:
                flash(f'Das Feld {feld} ist leer!', 'error')
            return render_template('auth/login.html', values=data)

        valid_input, flash_messages = validate_login(data)
        if not valid_input:
            for message in flash_messages:
                flash(message, 'error')
            return render_template("auth/login.html", values=data)

        #Ab hier ist der Input geprüft.
        inp_passwort = data.get("passwort", '')
        email = data.get("email", '').strip()
        if check_account(data):
            if user_id := check_password(email, inp_passwort):
                session.clear()
                session['user_id'] = user_id
                return redirect(url_for('auth.profile'))
            else:
                flash('Das Passwort ist falsch!', 'error')
                return render_template("auth/login.html", values=data)
        else:
            flash('Der Account existiert nicht!', 'error')
            return render_template("auth/login.html", values=data)
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Felder: Vorname, Nachname, Matrikelnummer, Email, Passwort, Passwort wiederholen
    #   seminar, studiengang_name, abschluss, seminar_thema
    if request.method == 'GET':
        seminarthemen = get_free_seminarthemen()
        return render_template("auth/register.html", values={}, seminarthemen=seminarthemen)
    else:
        data = request.form
        seminarthemen = get_free_seminarthemen()


        empty_input_found, leere_felder = check_register_input(data)
        if empty_input_found:
            for feld in leere_felder:
                flash(f'Das Feld {feld} ist leer!', 'error')
            return render_template('auth/register.html', values=data, seminarthemen=seminarthemen)

        valid_input, flash_messages = validate_register(data)
        if not valid_input:
            for message in flash_messages:
                flash(message, 'error')
            return render_template("auth/register.html", values=data, seminarthemen=seminarthemen)

        #Hier wird geguckt, ob ein Seminarthema ausgewählt wurde und ob dieses bereits belegt wurde.
        if data.get("seminar_thema", '').strip():
            if is_seminar_occupied(data.get('seminar_thema')):
                flash("Seminar ist bereits belegt!", 'error')
                return render_template("auth/register.html", values=data, seminarthemen=seminarthemen)

        #Ab hier ist der Input validiert.

        #Jetzt wird geprüft, ob der Account bereits existiert
        # und ansonsten wird er erstellt.
        if check_account(data):
            flash('Account existiert bereits!', 'error')
            return render_template("auth/register.html", values=data, seminarthemen=seminarthemen)
        else:
            create_user(data)
            flash('Account erfolgreich erstellt!', 'success')
        return render_template("auth/register.html", values={}, seminarthemen=seminarthemen)




@auth_bp.route('/profile', methods=['GET'])
def profile():
        if 'user_id' in session:
            user_id = int(session.get('user_id', '-1'))
            rolle = get_user_role(user_id)
            user_info = get_user_info(user_id)

            if rolle == "stud":
                avg_vortrag_bew = get_bew_vortrag_for_display(user_id)
                return render_template("auth/profile.html",
                                        user_info=user_info,
                                        rolle=rolle,
                                        avg_vortrag_bew=avg_vortrag_bew)
            else:
                return render_template("auth/profile.html", user_info=user_info, rolle=rolle)
        else:
            return render_template("auth/profile.html")

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():

    #Hier wird zu einer Authentifizierung aufgefordert.
    if request.method == 'GET':
        if 'user_id' in session:
            user_id = int(session.get('user_id', '-1'))
            rolle = get_user_role(user_id)
            user_info = get_user_info(user_id)
            edit_mode = False
            auth_mode = True
            return render_template('auth/profile.html', user_info=user_info, rolle=rolle,
                            edit_mode=edit_mode, auth_mode=auth_mode)
        else:
            return redirect(url_for('auth.profile'))

    #Der Nutzer hat sein Passwort eingegeben.
    #Falls richtig, darf dieser jetzt seine Daten verändern.
    else:
        if 'user_id' in session:
            data = request.form
            user_id = int(session.get('user_id', '-1'))
            inp_passwort = data.get("passwort", '')
            rolle = get_user_role(user_id)
            user_info = get_user_info(user_id)
            email = user_info.get("email", '').strip()
            seminarthemen = get_free_seminarthemen()
            auth_mode = False
            if user_id := check_password(email, inp_passwort):
                session['auth'] = True
                edit_mode = True
            else:
                session['auth'] = False
                auth_mode = True
                edit_mode = False
                flash("Passwort falsch!", 'error')
            return render_template("auth/profile.html", user_info=user_info, rolle=rolle,
                                   edit_mode=edit_mode, auth_mode=auth_mode, seminarthemen=seminarthemen)

        else:
            flash('Session abgelaufen, oder nicht angemeldet!', 'error')
            return render_template("auth/profile.html")
@auth_bp.route('/profiles', methods=['GET', 'POST'])
def stud_profiles():
    if request.method == 'GET':
        if 'user_id' in session:  # angemeldet
            user_id = int(session.get('user_id', '-1'))
            rolle = get_user_role(user_id)

            if rolle == 'doz':
                stud_infos = get_all_stud()

                return render_template('auth/stud_profiles.html', stud_infos=stud_infos, user_rolle=rolle)
            else:
                return redirect(url_for('auth.profile'))
        else:
            return redirect(url_for('auth.index'))
    else:
        if 'user_id' in session:  # angemeldet
            user_id = int(session.get('user_id', '-1'))
            rolle = get_user_role(user_id)
            if rolle == 'doz':
                data = request.form
                s_id = int(data.get("s_id", '-1'))
                if s_id > 0:
                    user_info = get_user_info(s_id)
                    avg_vortrag_bew = get_bew_vortrag_for_display(s_id)
                    aus_bew = get_bew_ausarbeitung_for_display(s_id)
                    sem_leistung = get_seminarleistung_for_display(s_id)
                    return render_template('auth/profile.html',
                                           view_mode=True,
                                           user_info=user_info, #Das sind die Infos des ausgewählten Studis
                                           avg_vortrag_bew = avg_vortrag_bew,
                                           aus_bew =  aus_bew,
                                           sem_leistung = sem_leistung,
                                           rolle=rolle) #Hier handelt es sich um die Rolle des Dozenten
                else:
                    flash("Fehler bei der Auswahl, versuche es später erneut.", "error")
                    return render_template("auth/stud_profiles.html")
            else:
                return redirect(url_for('auth.index'))
        else:
            redirect(url_for('auth.index'))


@auth_bp.route('/update_user', methods=['GET', 'POST'])
def update_user():
    if request.method == 'GET':
        return redirect(url_for('auth.profile'))


    else:
        if 'user_id' in session: #angemeldet
            user_id = int(session.get('user_id', '-1'))
            rolle = get_user_role(user_id)
            user_info = get_user_info(user_id)
            seminarthemen = get_free_seminarthemen()
            if 'auth' in session:
                if session.get('auth', False): #authentifiziert.
                    data = request.form
                    passwort = data.get("passwort", '').strip()
                    with_password = False
                    if passwort:
                        with_password = True
                    valid_input, flash_messages = validate_register(data, with_password, user_id)

                    if not valid_input: #Der User ist noch authentifiziert, aber hat invaliden Input eingegeben.
                            auth_mode = False
                            edit_mode = True
                            if session.get('auth', False):
                                for message in flash_messages:
                                    flash(message, 'error')
                                return render_template("auth/profile.html", user_info=user_info, rolle=rolle,
                                                       edit_mode=edit_mode, auth_mode=auth_mode, seminarthemen=seminarthemen)

                    else: #Hier werden die neuen Daten gespeichert -> valide Daten und authentifiziert.
                        update_user_acc(data, user_id, with_password)
                        flash("Erfolgreich gespeichert!", 'success')
                        session['auth'] = False # Wird zurückgesetzt, damit erneute authentifizierung nötig ist.
                        return redirect(url_for('auth.profile'))

                else: #nicht authentifiziert, weil falsches Passwort.
                    flash('Nicht authentifiziert!', 'error')
                    user_id = int(session.get('user_id', '-1'))
                    rolle = get_user_role(user_id)
                    user_info = get_user_info(user_id)
                    return render_template("auth/profile.html", user_info=user_info, rolle=rolle)

            else: #auch nicht authentifiziert, weil noch nicht probiert.
                flash('Nicht authentifiziert!', 'error')
                user_id = int(session.get('user_id', '-1'))
                rolle = get_user_role(user_id)
                user_info = get_user_info(user_id)
                return render_template("auth/profile.html", user_info=user_info, rolle=rolle)

        else: #nicht angemeldet.
            flash('Session abgelaufen oder nicht angemeldet!', 'error')
            return render_template('auth.profile')


