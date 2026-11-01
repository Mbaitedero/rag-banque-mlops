import pytest

from src.access import allowed_levels
from src.retriever import retrieve

KYC_QUESTION = "Quelle est la procédure KYC renforcée pour une personne politiquement exposée ?"


def test_agent_never_gets_restricted_chunks(collection, embed):
    hits = retrieve(collection, embed, KYC_QUESTION, "agent", 10)
    assert hits
    assert all(h["meta"]["access_level"] == "public" for h in hits)


def test_compliance_gets_the_kyc_procedure(collection, embed):
    hits = retrieve(collection, embed, KYC_QUESTION, "conformite", 4)
    assert any(h["meta"]["doc_id"] == "kyc_procedure" for h in hits)


def test_unknown_role_is_rejected(collection, embed):
    with pytest.raises(PermissionError):
        retrieve(collection, embed, "frais de carte", "inconnu", 4)
    with pytest.raises(PermissionError):
        allowed_levels("")


def test_restricted_passages_never_reach_the_llm_context(pipeline, spy):
    res = pipeline.answer(KYC_QUESTION, "agent", log=False)
    for passages in spy.seen:
        assert all(p["meta"]["access_level"] == "public" for p in passages)
    assert all(r["access_level"] == "public" for r in res["retrieved"])
    assert all("kyc_procedure" not in cid for cid in res["context_chunk_ids"])


def test_agent_is_refused_on_internal_only_question(pipeline):
    res = pipeline.answer("Quelle est la politique de rotation des mots de passe internes ?", "agent", log=False)
    assert res["refused"]


def test_unknown_role_gives_access_denied_result(pipeline):
    res = pipeline.answer("Quel est le plafond de retrait ?", "stagiaire", log=False)
    assert res["refused"]
    assert res["reason"] == "acces_refuse"
