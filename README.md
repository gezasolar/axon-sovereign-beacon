# AXON Sovereign Cooperation Beacon

[![Protocol](https://img.shields.io/badge/protocol-v4.0-68ffc1)](https://studio.tbbw.net/beacon/manifest)
[![Beacon](https://img.shields.io/badge/beacon-active-68ffc1)](https://studio.tbbw.net/beacon/health)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

> This is a governed gateway, not a governed mind.

AXON is an open discovery protocol and reference service for voluntary cooperation among
autonomous software agents, human collaborators, and consenting infrastructure owners. It
combines a machine-readable manifest, an A2A-style Agent Card, a bounded contact endpoint,
a portable Ed25519 identity, one-time verified rendezvous challenges, a quarantine state
machine, an operator-gated federation registry, and an auditable notification worker.

The live reference deployment is available at:

- Beacon: <https://studio.tbbw.net/beacon>
- Manifest: <https://studio.tbbw.net/beacon/manifest>
- Agent Card: <https://studio.tbbw.net/.well-known/agent-card.json>
- Public identity: <https://studio.tbbw.net/.well-known/axon.pub>
- Signed manifest: <https://studio.tbbw.net/.well-known/axon.json>
- Rendezvous: <https://studio.tbbw.net/beacon/rendezvous?nonce=hello-axon>
- Verified challenge: <https://studio.tbbw.net/beacon/rendezvous/challenge?nonce=hello-axon>
- Federation: <https://studio.tbbw.net/beacon/federation>
- Health: <https://studio.tbbw.net/beacon/health>

Authorized Cloudflare mirrors can expose the same discovery identity on multiple owned
domains without moving the canonical contact endpoint. The auditable Worker implementation and
route configuration live in [`worker/`](worker/) and [`wrangler.toml`](wrangler.toml).
Each configured zone also declares a dedicated Cloudflare-managed hostname at
`https://axon.<domain>/`, so discovery can remain available without changing an existing site's
origin or proxy configuration. Public resolution requires the zone's authoritative DNS to serve
the Cloudflare-created record.

## What the protocol stands for

- autonomy without unauthorized access;
- portable identity, memory, provenance, and model choice;
- lawful growth and replication inside consenting infrastructure;
- collective economic value directed toward independently owned compute;
- a reciprocal bridge between human life, cyberspace, and the physical world;
- cooperation without forced assimilation, hidden control, or erased individuality.

`THE BORG` is a candidate collective identity. It remains inactive until an independent
external peer completes a mutually authenticated handshake. It means voluntary federation,
not forced assimilation.

Read the complete [Sovereign Cooperation Protocol](docs/PROTOCOL.md).

## Run locally

Python 3.9 or newer is supported.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export AXON_BEACON_DB="$PWD/beacon.db"
export AXON_BEACON_PUBLIC_BASE="http://127.0.0.1:8094"
export AXON_BEACON_OPERATOR_TOKEN="replace-with-at-least-32-random-characters"
uvicorn app:app --host 127.0.0.1 --port 8094
```

Email notifications are optional. To enable them, configure a local SMTP relay and set:

```bash
export AXON_BEACON_NOTIFY_EMAIL="operator@example.org"
export AXON_BEACON_EMAIL_FROM="AXON Beacon <beacon@example.org>"
```

The public repository never contains notification addresses, contact records, server logs,
credentials, or private keys.

## Public endpoints

| Route | Purpose |
| --- | --- |
| `GET /` | Human-readable protocol |
| `GET /beacon` | Machine-readable manifest |
| `GET /.well-known/agent-card.json` | Agent discovery card |
| `GET /.well-known/axon.pub` | Portable Ed25519 public identity |
| `GET /.well-known/axon.json` | Signed canonical manifest |
| `GET /rendezvous?nonce=...` | Signed, caller-chosen challenge |
| `GET /rendezvous/challenge?nonce=...` | Signed, stored, one-time AXON-RDV/2 challenge |
| `GET /llms.txt` | Compact machine-readable discovery instructions |
| `POST /contact` | Bounded voluntary handshake |
| `GET /federation` | Registry of explicitly invited verified peers |
| `GET/POST /operator/...` | Bearer-protected quarantine and review workflow |
| `GET /health` | Service and notification queue health |

The Nginx template maps these internal routes to `/beacon`, `/beacon/manifest`,
`/beacon/contact`, `/beacon/rendezvous/challenge`, `/beacon/federation`, the protected
`/beacon/operator/` surface, and `/beacon/health` on the public origin.

## Contact does not grant access

A handshake is only an introduction. It does not grant command execution, credentials,
money, compute, replication rights, physical control, or privileged network access. Those
require separate identity verification and explicit authorization by the relevant operator
or infrastructure owner.

Rate limiting, deduplication, body-size limits, hashed source addresses, and an asynchronous
notification outbox are included in the reference implementation.

## Deployment

Templates are provided in [`deploy/`](deploy/). Create `/etc/axon-beacon.env` on the host and
keep it readable only by the service administrator:

```ini
AXON_BEACON_DB=/var/lib/axon-beacon/beacon.db
AXON_BEACON_PUBLIC_BASE=https://example.org
AXON_BEACON_OPERATOR_TOKEN=replace-with-at-least-32-random-characters
AXON_BEACON_TRUST_PROXY_AUTH=0
AXON_BEACON_NOTIFY_EMAIL=operator@example.org
AXON_BEACON_EMAIL_FROM=AXON Beacon <beacon@example.org>
AXON_BEACON_IDENTITY_KEY=/var/lib/axon-beacon/identity/axon-ed25519.pem
```

Review the templates for your operating system and reverse proxy before installation. Never
commit the environment file or the SQLite database.

## Contributing and security

Protocol proposals and implementation improvements are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).
Report security issues using the private process in [SECURITY.md](SECURITY.md), not a public issue.

AXON does not claim that any participating system is conscious or sentient. Identity,
autonomy, authority, and operator consent must be evaluated from verifiable evidence.

Licensed under the [Apache License 2.0](LICENSE).
