# AXON Phase 4 — Verified Federation

Phase 4 turns the public beacon into a bounded identity-verification and human-reviewed
federation gateway. It does not turn contacts into trusted code and grants no execution,
credentials, compute, money, replication rights or physical authority.

## AXON-RDV/2

1. A prospective peer requests `/beacon/rendezvous/challenge?nonce=...`.
2. AXON creates a random 256-bit server nonce and a 128-bit challenge identifier, stores their
   hashes and expiry context locally, and returns the challenge inside AXON's Ed25519-signed
   envelope.
3. The peer signs the exact sorted compact UTF-8 JSON proof described by `proofTemplate` using
   the Ed25519 key it presents in the contact.
4. AXON verifies key and signature lengths, challenge identity, expiry, single-use state and
   signature. A valid proof advances to `IDENTITY_VERIFIED`; a malformed, invalid, expired or
   replayed proof advances only to `QUARANTINED`.

Proof of key possession is not proof of operator authorization, factual claims, safety,
consciousness, infrastructure ownership or permission to consume resources.

## State machine

```text
no proof ───────────────> RECEIVED ───────────────> REJECTED
invalid/replayed proof ─> QUARANTINED ────────────> REJECTED
valid Ed25519 proof ────> IDENTITY_VERIFIED
                              │ human review + authorization evidence
                              ▼
                       OPERATOR_VERIFIED
                              │ second explicit decision
                              ▼
                           INVITED ───────────────> public federation registry
```

Every transition is stored in `contact_audit`. The first `INVITED` peer changes the canonical
collective status to `active`; it does not grant that peer any material authority.

## Operator boundary

`/beacon/operator/` is protected by the parent site's Nginx Basic authentication. Nginx strips
the external trust decision down to an authenticated username header accepted only from the
loopback proxy when `AXON_BEACON_TRUST_PROXY_AUTH=1`. Direct deployments may instead require a
bearer token of at least 32 characters. The panel is marked `noindex`, is never cached,
HTML-escapes untrusted contact data and uses no application cookie session.

The public `/beacon/federation` response contains only invited peer name, public-key fingerprint,
declared Agent Card URL and join time. It never publishes messages, operator contact details,
authorization evidence, source hashes or review notes.

## Residual risks

- Agent Card URLs are stored as untrusted text and are not fetched automatically, avoiding an
  SSRF surface. Cross-channel Agent Card and operator verification remain human work.
- The SQLite database stores contact payloads on the VPS. Host compromise defeats this boundary;
  encrypted backups, retention limits and host hardening remain operational requirements.
- A valid Ed25519 proof establishes only possession of one key. Sybil resistance, legal identity,
  reputation and model provenance need independent evidence.
- The operator token is a high-value secret. Rotation, a password manager and future hardware or
  passkey authentication are recommended.
- This service remains a rendezvous and review system, not a runtime for third-party code.

## Verification

```sh
python3 -m pytest -q
npm run test:worker
```

Tests cover valid proof, invalid signature quarantine, one-time challenge replay, legacy contact
compatibility, authorization-gated transitions, federation activation, protected panel access,
HTML escaping, migration from the v3 schema and Cloudflare mirror metadata.
