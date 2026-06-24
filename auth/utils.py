import re

def check_register_input(data) -> tuple[bool, list]:
    pflicht_felder = ['vorname', 'nachname', 'matr_nr',
                     'email', 'passwort', 'passwort_wiederholen',
                     'seminar', 'studiengang_name', 'abschluss']
    leere_felder = []
    empty_input_found = False
    for feld in pflicht_felder:
        # Ich verwende hier .strip(), um Leerzeichen zu entfernen, damit diese nicht als Inhalt zählen.
        val = data.get(feld, '').strip()
        if not val:
            empty_input_found = True
            leere_felder.append(feld)

    return empty_input_found, leere_felder


def validate_register(data)-> tuple[bool, list]:
    #Hier verwende ich bewusst ein + statt einem * für die Kleinbuchstaben,
    # da es eigentlich keine Namen mit nur einem Buchstaben gibt.
    #Der Name muss also aus mindestens einem Groß- und einem Kleinbuchstaben bestehen.
    #(In den Anforderungen steht beliebig viele Kleinbuchstaben)
    name_pattern = r"^[A-ZÄÖÜ][a-zäöüß]+([- ][A-ZÄÖÜ][a-zäöüß]+)?$"

    #Hier verwende ich einen positiven lookahead, um zu garantieren,
    # dass die Email maximal aus 254 Zeichen besteht.
    email_pattern = r"^(?=.{1,254}$)[a-z.+\-]{1,63}@[a-z.+\-]+$"

    #Hier verwende ich direkt 3 positive Lookaheads,
    # um jeweils zu gucken, ob mindestens eins der Zeichen aus der Anforderung in
    # dem Passwort enthalten ist.
    pass_pattern = (
        r"^(?=.*[A-ZÄÖÜ])" #Mindestens ein Großbuchstabe
        r"(?=.*[a-zäöüß])" #Mindestens ein Kleinbuchstabe
        r"(?=.*[.,!?@#$%&*+\-/\\])" #Mindestens ein Sonderzeichen
        r"[A-ZÄÖÜa-zäöüß0-9.,!?@#$%&*+\-/\\]+$" #Besteht nur aus diesen Zeichen + Zahlen
    )

    #Es wird geschaut, ob die Matrikelnummer aus 6-8 Ziffern besteht.
    matr_nr_pattern = r"^\d{6,8}$"

    #Dies steht zwar nicht in den Anforderungen, sollte aber auch geprüft werden,
    # um sich zusätzlich neben dem Jinja2 Autoescaping gegen XSS Angriffe zu schützen.
    #Ich prüfe das Thema auf normale Satzzeichen.
    seminar_thema_pattern = r"^[A-ZÄÖÜa-zäöüß0-9\s.,!?()\-]+$"

    valid_seminare = {'IIS', 'WBS'}
    valid_s_name = {'WINF', 'IMIT', 'AI', 'IIM', 'IKU'}
    valid_abschluss = {'B.Sc', 'M.Sc'}

    valid_input = True
    flash_messages = []

    vorname = data.get("vorname", '').strip()
    nachname = data.get("nachname", '').strip()
    matr_nr = data.get("matr_nr", '').strip()
    email = data.get("email", '').strip()
    passwort = data.get("passwort", '').strip()
    passwort_wiederholen = data.get("passwort_wiederholen", '').strip()
    seminar = data.get("seminar", '').strip()
    studiengang_name = data.get("studiengang_name", '').strip()
    abschluss = data.get("abschluss", '').strip()
    seminar_thema = data.get("seminar_thema", '').strip()


    if not re.match(name_pattern, vorname):                                     #Vorname
        valid_input = False
        flash_messages.append("Vorname ist invalide.")

    if not re.match(name_pattern, nachname):                                    #Nachname
        valid_input = False
        flash_messages.append("Nachname ist invalide.")

    if not re.match(matr_nr_pattern, matr_nr):                                  #Matrikelnummer
        valid_input = False
        flash_messages.append("Matrikelnummer ist invalide.")

    if not re.match(email_pattern, email):                                      #Email
        valid_input = False
        flash_messages.append("E-Mail ist invalide.")

    if not re.match(pass_pattern, passwort):                                    #Passwort
        valid_input = False
        flash_messages.append("Passwort muss aus min. einem Groß- und Kleinbuchstaben "
                              "und einem Sonderzeichen bestehen.")

    if not re.match(pass_pattern, passwort_wiederholen):                        #Passwort wiederholen
        valid_input = False
        flash_messages.append("Passwort muss aus min. einem Groß- und Kleinbuchstaben "
                              "und einem Sonderzeichen bestehen.")

    if passwort != passwort_wiederholen:                                    #Passwörter vergleichen
        valid_input = False
        flash_messages.append("Passwörter stimmen nicht überein!")

    if seminar not in valid_seminare:                                           #Seminare
        valid_input = False
        flash_messages.append("Seminar ist invalide.")

    if studiengang_name not in valid_s_name:                                    #Studiengang
        valid_input = False
        flash_messages.append("Studiengang ist invalide.")

    if abschluss not in valid_abschluss:                                        #Abschluss
        valid_input = False
        flash_messages.append("Abschluss ist invalide.")

    if seminar_thema and not re.match(seminar_thema_pattern, seminar_thema):    #Seminarthema
        valid_input = False
        flash_messages.append("Seminarthema ist invalide.")

    return valid_input, flash_messages





def check_login_input(data):
    # TODO Input vom login Formular überpruefen
    # Schritt 1: Ist jedes Feld ausgefüllt?
    # Schritt 2: Passen die Eingaben in die Regex Konventionen
    pass

def check_account(data):
    # TODO gucken ob diese Email Passwort Kombination in Account vorhanden ist.
    pass