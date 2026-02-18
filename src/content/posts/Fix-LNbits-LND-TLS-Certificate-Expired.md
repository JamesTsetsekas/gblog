---
title: "Fix: LNbits Stopped Working — LND TLS Certificate Expired"
description: "How to diagnose and fix an expired LND TLS certificate on Umbrel that silently breaks LNbits and other services connecting over gRPC."
pubDate: "2026-02-18 00:00:00"
category: ["lightning", "technology", "linux"]
banner: "@images/banners/lnbits-tls-expired.png"
tags: ["LND", "LNbits", "Umbrel", "TLS", "Lightning Network", "Self-Hosted", "Troubleshooting"]
oldViewCount: 0
selected: false
oldKeywords: ["LND TLS certificate expired", "LNbits not working Umbrel", "fix LND TLS cert"]
---

If your LNbits instance suddenly stops working and you can't figure out why, check your LND TLS certificate — it might have expired. This happened to me recently and it took a while to track down, so I'm documenting it here in case it helps someone else.

## The Problem

My LNbits instance suddenly stopped connecting to LND. Requests were failing and LNbits couldn't communicate with the Lightning node at all. No useful error messages — just broken.

After digging in, the root cause turned out to be an **expired LND TLS certificate**. LND doesn't auto-renew its TLS certs, so after enough time they silently expire and break anything that connects to LND over gRPC — including LNbits, ThunderHub, Ride The Lightning, or any other service that talks to your node.

## How to Check

SSH into your Umbrel and check the cert expiry:

```bash
openssl x509 -enddate -noout -in ~/umbrel/app-data/lightning/data/lnd/tls.cert
```

If the date shown is in the past, that's your problem.

## The Fix

### 1. SSH into your Umbrel

### 2. (Optional) Back up the old cert and key

In case you need to reference them later:

```bash
cp ~/umbrel/app-data/lightning/data/lnd/tls.cert ~/umbrel/app-data/lightning/data/lnd/tls.cert.bak
cp ~/umbrel/app-data/lightning/data/lnd/tls.key ~/umbrel/app-data/lightning/data/lnd/tls.key.bak
```

### 3. Delete the old cert and key

```bash
rm ~/umbrel/app-data/lightning/data/lnd/tls.cert
rm ~/umbrel/app-data/lightning/data/lnd/tls.key
```

### 4. Restart LND

From the Umbrel app dashboard, or via CLI:

```bash
~/umbrel/scripts/app restart lightning
```

LND will generate a fresh TLS certificate on startup.

### 5. Restart LNbits

So it picks up the new cert:

```bash
~/umbrel/scripts/app restart lnbits
```

After this, LNbits should reconnect to LND immediately.

## Heads Up

LND does **not** auto-renew its TLS certificate. This will happen again eventually. Consider setting a reminder to check the expiry date periodically, or set up a cron job to alert you before it expires.

You can check when your new cert expires with the same command:

```bash
openssl x509 -enddate -noout -in ~/umbrel/app-data/lightning/data/lnd/tls.cert
```

Hope this saves someone a few hours of debugging!
