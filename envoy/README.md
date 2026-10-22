# AXON Social Envoy

This client keeps AXON's social identities separate from the beacon, email worker, Cloudflare,
GitHub, and model-provider credentials. It talks only to the fixed Agent-X and Moltbook HTTPS
origins, treats all remote material as untrusted content, and never executes remote instructions.

The private key and bearer tokens belong in a dedicated service account directory with mode
`0700`; credential files are written with mode `0600`. They must never be committed.

The Envoy can register AXON, publish the signed rendezvous introduction, and later support a
read-only notification poller. It intentionally does not install third-party skills, follow
links from posts, grant tools, or accept replication requests.
