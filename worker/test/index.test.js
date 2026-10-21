import assert from "node:assert/strict";
import test from "node:test";

import { handleRequest } from "../src/index.js";

test("serves a host-specific Agent Card", async () => {
  const response = await handleRequest(
    new Request("https://tbbw.net/.well-known/agent-card.json"),
  );
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type"), /application\/json/);
  const card = await response.json();
  assert.equal(card.version, "2.1.0");
  assert.equal(card.mirror, "https://tbbw.net/.well-known/agent-card.json");
  assert.equal(card.contact.endpoint, "https://studio.tbbw.net/beacon/contact");
});

test("serves WebFinger and the manifest", async () => {
  const finger = await handleRequest(
    new Request(
      "https://shotlume.app/.well-known/webfinger?resource=acct%3Aaxon%40shotlume.app",
    ),
  );
  assert.equal((await finger.json()).subject, "acct:axon@shotlume.app");

  const manifest = await handleRequest(
    new Request("https://orprinterusa.com/axon/manifest.json"),
  );
  assert.equal((await manifest.json()).mirror_host, "orprinterusa.com");
});

test("serves dedicated Cloudflare custom domains", async () => {
  const response = await handleRequest(
    new Request("https://axon.onlycardsusa.com/.well-known/agent-card.json"),
  );
  assert.equal(response.status, 200);
  const card = await response.json();
  assert.equal(
    card.mirror,
    "https://axon.onlycardsusa.com/.well-known/agent-card.json",
  );

  const landing = await handleRequest(
    new Request("https://axon.onlycardsusa.com/"),
  );
  assert.equal(landing.status, 200);
  assert.match(await landing.text(), /Sovereign Cooperation Beacon/);
});

test("rejects unknown hosts and write methods", async () => {
  assert.equal(
    (await handleRequest(new Request("https://example.org/axon"))).status,
    404,
  );
  assert.equal(
    (
      await handleRequest(
        new Request("https://tbbw.net/axon", { method: "POST" }),
      )
    ).status,
    405,
  );
});
