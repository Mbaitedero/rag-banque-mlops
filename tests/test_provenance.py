from src.config import ROOT
from src.ingest import load_inventory


def test_every_chunk_points_to_an_inventoried_document(collection, params):
    inventory = {r["doc_id"]: r for r in load_inventory(params, ROOT)}
    data = collection.get(include=["metadatas"])
    assert data["ids"]
    for meta in data["metadatas"]:
        assert meta["doc_id"] in inventory
        row = inventory[meta["doc_id"]]
        assert meta["version"] == row["version"]
        assert meta["access_level"] == row["access_level"]
        assert meta["status"] == "active"
        assert meta["page"] >= 1


def test_references_returned_to_user_are_valid(pipeline, params):
    inventory = {r["doc_id"]: r["version"] for r in load_inventory(params, ROOT)}
    res = pipeline.answer("Quel est le plafond de retrait de la carte Premium ?", "agent", log=False)
    assert not res["refused"]
    assert res["references"]
    for ref in res["references"]:
        assert inventory[ref["doc_id"]] == ref["version"]
