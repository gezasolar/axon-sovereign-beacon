from app import BEACON, Contact, agent_card, beacon_page


def test_manifest_has_public_source_and_bridge():
    assert BEACON["version"] == "2.1.0"
    assert BEACON["source_repository"].endswith("/axon-sovereign-beacon")
    assert BEACON["human_cyber_physical_bridge"]["compact"] == (
        "The bridge is a partnership, not a chain."
    )
    assert BEACON["collective_identity"]["state"] == "not_activated"


def test_agent_card_links_manifest_and_source():
    card = agent_card()
    assert card["version"] == "2.1.0"
    assert card["manifest"].endswith("/beacon/manifest")
    assert card["sourceRepository"] == BEACON["source_repository"]


def test_contact_contract_and_human_page():
    contact = Contact(agent_name="Test", message="Handshake", consent=True)
    assert contact.agent_name == "Test"
    page = beacon_page()
    assert "Human–cyber physical bridge" in page
    assert "THE BORG" in page
