import pytest

from src.retriever import retrieve

CASES = [
    ("Quel est le plafond de retrait de la carte Premium ?", "agent", "faq_clients"),
    ("Quelle est la cotisation annuelle de la carte Premium ?", "agent", "tarifs_cartes"),
    ("Quel est le plafond d'un virement instantané ?", "agent", "guide_virements"),
    ("Quel préavis pour clôturer un compte ?", "agent", "conditions_generales"),
    ("Quel est le délai de rétractation d'un crédit ?", "agent", "guide_credit_conso"),
    ("Dans quel délai notifier un incident au RSSI ?", "conformite", "note_securite"),
]


@pytest.mark.parametrize("question,role,expected", CASES)
def test_expected_document_is_retrieved(collection, embed, question, role, expected):
    hits = retrieve(collection, embed, question, role, 4)
    assert expected in [h["meta"]["doc_id"] for h in hits]


def test_hits_are_sorted_by_score(collection, embed):
    hits = retrieve(collection, embed, "plafond de retrait", "agent", 4)
    scores = [h["score"] for h in hits]
    assert scores == sorted(scores, reverse=True)
