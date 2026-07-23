#Author Tim Deppe (413323)
from bewertungen.queries import get_einfache_vortragsstatistik, get_einfache_ausarbeitungsstatistik, get_seminarleistung


def get_bew_vortrag_for_display(s_id):
    """
    Gibt nach Eingabe einer s_id das Symbol (--, -, o, +, ++) für den Durchschnitt der Vortrag Bewertung aus
    :param s_id:
    :return: string oder None
    """
    d = get_einfache_vortragsstatistik(s_id)
    return d.get('gesamtdurchschnitt', None)

def get_bew_ausarbeitung_for_display(s_id):
    """
    Gibt nach Eingabe einer s_id das Symbol (--, -, o, +, ++) für den Durchschnitt der Bewertung der Ausarbeitung aus
    :param s_id:
    :return: string oder None
    """
    d = get_einfache_ausarbeitungsstatistik(s_id)
    return d.get('gesamtdurchschnitt', None)

def get_seminarleistung_for_display(s_id):
    """
    Gibt nach Eingabe einer s_id die zugehörige Note der Seminarleistung aus
    :param s_id:
    :return: int oder None
    """
    return get_seminarleistung(s_id)