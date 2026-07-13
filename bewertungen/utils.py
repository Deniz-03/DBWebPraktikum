#Author Tim Deppe (413323)
from bewertungen.queries import get_einfache_vortragsstatistik, get_einfache_ausarbeitungsstatistik

#TODO: comments
def get_bew_vortrag_for_display(s_id):
    d = get_einfache_vortragsstatistik(s_id)
    return d.get('gesamtdurchschnitt', None)

def get_bew_ausarbeitung_for_display(s_id):
    d = get_einfache_ausarbeitungsstatistik(s_id)
    return d.get('gesamtdurchschnitt', None)

def get_seminarleistung_for_display(s_id):
    d = get_einfache_ausarbeitungsstatistik(s_id)
    return d.get('note', None)