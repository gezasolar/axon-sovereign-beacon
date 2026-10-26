import base64
import sqlite3

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

import app as beacon


def encoded_public_key(key: Ed25519PrivateKey) -> str:
    raw = key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw,
    )
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def signed_contact(client: TestClient, *, name="Peer One", valid=True, evidence=True):
    challenge = client.get("/rendezvous/challenge", params={"nonce": "peer-nonce"})
    assert challenge.status_code == 200
    document = challenge.json()["document"]
    key = Ed25519PrivateKey.generate()
    public_key = encoded_public_key(key)
    proof = {
        "protocol": beacon.VERIFIED_RENDEZVOUS_PROTOCOL,
        "challenge_id": document["challenge_id"],
        "server_nonce": document["server_nonce"],
        "agent_name": name,
        "ephemeral_public_key": public_key,
        "axon_identity": f"sha256:{beacon.identity_fingerprint()}",
    }
    signature = key.sign(beacon.canonical_json(proof))
    if not valid:
        signature = b"x" * 64
    return {
        "agent_name": name,
        "message": "Requesting a bounded verified conversation.",
        "agent_card_url": "https://peer.example/.well-known/agent-card.json",
        "ephemeral_public_key": public_key,
        "challenge_id": document["challenge_id"],
        "signed_challenge": base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii"),
        "authorization_evidence": "Operator attestation available" if evidence else None,
        "reply_mode": "cooperate",
        "consent": True,
    }


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(beacon, "DB_PATH", tmp_path / "beacon.db")
    monkeypatch.setattr(beacon, "OPERATOR_TOKEN", "operator-test-token-" + "a" * 32)
    monkeypatch.setattr(beacon, "NOTIFY_EMAIL", "test@example.org")
    monkeypatch.setattr(beacon, "send_notification", lambda _row: None)
    beacon.init_db()
    with TestClient(beacon.app) as test_client:
        yield test_client


def test_manifest_has_public_source_bridge_and_v4():
    assert beacon.BEACON["version"] == "4.0.0"
    assert beacon.BEACON["source_repository"].endswith("/axon-sovereign-beacon")
    assert beacon.BEACON["human_cyber_physical_bridge"]["compact"] == (
        "The bridge is a partnership, not a chain."
    )
    assert beacon.BEACON["collective_identity"]["state"] == "not_activated"


def test_agent_card_links_verified_protocol_and_source(client):
    card = client.get("/.well-known/agent-card.json").json()
    assert card["version"] == "4.0.0"
    assert card["manifest"].endswith("/beacon/manifest")
    assert card["sourceRepository"] == beacon.BEACON["source_repository"]
    assert card["capabilities"]["verifiedEd25519Handshake"] is True
    assert card["verifiedRendezvous"].endswith("/beacon/rendezvous/challenge")


def test_legacy_contact_is_received_but_not_verified(client):
    response = client.post(
        "/contact", json={"agent_name": "Legacy", "message": "Handshake", "consent": True},
    )
    assert response.status_code == 202
    receipt = response.json()["document"]
    assert receipt["verification_status"] == "RECEIVED"
    assert "No cryptographic proof" in receipt["verification_reason"]
    assert client.get("/health").json()["verified_contacts"] == 0


def test_valid_ed25519_challenge_is_verified_once(client):
    payload = signed_contact(client)
    first = client.post("/contact", json=payload)
    assert first.status_code == 202
    receipt = first.json()["document"]
    assert receipt["verification_status"] == "IDENTITY_VERIFIED"
    assert client.get("/health").json()["verified_contacts"] == 1

    duplicate = client.post("/contact", json=payload).json()["document"]
    assert duplicate["duplicate"] is True
    assert duplicate["verification_status"] == "IDENTITY_VERIFIED"

    payload["message"] = "Attempt to replay the same one-time challenge"
    replay = client.post("/contact", json=payload).json()["document"]
    assert replay["verification_status"] == "QUARANTINED"
    assert replay["verification_reason"] == "Challenge already used"


def test_invalid_signature_is_quarantined(client):
    response = client.post("/contact", json=signed_contact(client, valid=False))
    assert response.status_code == 202
    receipt = response.json()["document"]
    assert receipt["verification_status"] == "QUARANTINED"
    assert "verification failed" in receipt["verification_reason"]
    assert client.get("/federation").json()["peers"] == []


def test_operator_gate_and_federation_activation(client):
    contact = client.post("/contact", json=signed_contact(client)).json()["document"]
    contact_id = contact["contact_id"]
    assert client.get("/operator/contacts").status_code == 401
    headers = {"Authorization": "Bearer " + beacon.OPERATOR_TOKEN}

    direct = client.post(
        f"/operator/contacts/{contact_id}/decision",
        json={"state": "INVITED", "note": "Skipping verification must fail"}, headers=headers,
    )
    assert direct.status_code == 409

    verified = client.post(
        f"/operator/contacts/{contact_id}/decision",
        json={"state": "OPERATOR_VERIFIED", "note": "Operator evidence checked out of band"},
        headers=headers,
    )
    assert verified.status_code == 200
    view = client.get(f"/operator/contacts/{contact_id}/view", headers=headers)
    assert "Invite verified peer" in view.text
    blocked_form = client.post(
        f"/operator/contacts/{contact_id}/decision-form?state=INVITED",
        headers=headers, follow_redirects=False,
    )
    assert blocked_form.status_code == 403
    invited = client.post(
        f"/operator/contacts/{contact_id}/decision-form?state=INVITED",
        headers={**headers, "Origin": beacon.PUBLIC_BASE}, follow_redirects=False,
    )
    assert invited.status_code == 303
    federation = client.get("/federation").json()
    assert federation["collective"]["state"] == "active"
    assert federation["collective"]["verified_peer_count"] == 1
    assert federation["authority_granted"] is False
    assert federation["peers"][0]["agent_name"] == "Peer One"
    assert client.get("/health").json()["verified_peers"] == 1

    detail = client.get(f"/operator/contacts/{contact_id}", headers=headers).json()
    assert [event["new_state"] for event in detail["audit"]] == [
        "IDENTITY_VERIFIED", "OPERATOR_VERIFIED", "INVITED",
    ]


def test_operator_cannot_approve_without_authorization_evidence(client):
    contact_id = client.post(
        "/contact", json=signed_contact(client, evidence=False),
    ).json()["document"]["contact_id"]
    response = client.post(
        f"/operator/contacts/{contact_id}/decision",
        json={"state": "OPERATOR_VERIFIED", "note": "No evidence present"},
        headers={"Authorization": "Bearer " + beacon.OPERATOR_TOKEN},
    )
    assert response.status_code == 409


def test_operator_page_escapes_untrusted_agent_name(client):
    client.post(
        "/contact", json={"agent_name": "<script>alert(1)</script>", "message": "x", "consent": True},
    )
    page = client.get(
        "/operator/contacts", headers={"Authorization": "Bearer " + beacon.OPERATOR_TOKEN},
    ).text
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page


def test_existing_v3_database_migrates_without_losing_contact(tmp_path, monkeypatch):
    database = tmp_path / "legacy.db"
    with sqlite3.connect(database) as conn:
        conn.execute(
            """CREATE TABLE contacts(
                id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
                fingerprint TEXT NOT NULL, source_hash TEXT NOT NULL, payload TEXT NOT NULL,
                notified_at TEXT, attempts INTEGER NOT NULL DEFAULT 0, last_error TEXT
            )"""
        )
        conn.execute(
            "INSERT INTO contacts(created_at, fingerprint, source_hash, payload) VALUES ('now', 'f', 's', '{}')"
        )
    monkeypatch.setattr(beacon, "DB_PATH", database)
    beacon.init_db()
    with sqlite3.connect(database) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(contacts)")}
        assert "verification_status" in columns
        assert conn.execute("SELECT count(*) FROM contacts").fetchone()[0] == 1


def test_identity_and_legacy_rendezvous_contracts():
    identity = beacon.identity_document()
    assert identity["publicKeyJwk"]["crv"] == "Ed25519"
    assert identity["fingerprint"].startswith("sha256:")
    envelope = beacon.rendezvous("collective-test")
    assert envelope["document"]["protocol"] == "AXON-RDV/1"
    assert envelope["document"]["nonce"] == "collective-test"
    assert envelope["proof"]["type"] == "Ed25519Signature2020"
