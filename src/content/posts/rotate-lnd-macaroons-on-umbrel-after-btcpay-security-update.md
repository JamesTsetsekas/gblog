---
title: "How to Rotate LND Macaroons on Umbrel After the BTCPay Server 2.4.2 Advisory"
description: "A safety-first guide to invalidating and regenerating LND macaroons on Umbrel after updating BTCPay Server and Lightning Node."
pubDate: "2026-08-17 00:00:00"
category: ["bitcoin", "lightning"]
banner: "@images/banners/lnd-macaroon-rotation.png"
tags: ["BTCPay Server", "LND", "Umbrel", "Macaroons", "Lightning Network", "Security"]
oldViewCount: 0
selected: false
---

If you ran BTCPay Server on Umbrel with LND, updating the apps is the first step after the BTCPay Server 2.4.2 security advisory. The second step is making sure any LND macaroons that may have been exposed can no longer authenticate.

This guide follows Umbrel's platform-specific instructions and uses the Files app. It deliberately avoids shell deletion commands because a typo in an LND data directory can turn a credential rotation into a node-recovery problem.

> **Use current official guidance first.** This article was last verified on **August 17, 2026**. If BTCPay Server, Umbrel, or LND publishes newer instructions, follow those instead.

## What Happened?

BTCPay Server disclosed an actively exploited vulnerability affecting versions before 2.4.2, including 2.4.2 release candidates. On servers connected to LND, an unauthenticated remote attacker could obtain an LND `.macaroon` file. A sufficiently privileged macaroon is a bearer credential: whoever possesses it may be able to control the connected Lightning node and move funds.

This was **not a weak-entropy problem in an LND seed or private key**, and the published advisory does not describe it as an upstream LND vulnerability. It was a BTCPay Server vulnerability that exposed LND credential files. Rotating the macaroons invalidates those credentials; it does not change your seed or channel keys.

BTCPay's updated August 7 advisory says its standard update to BTCPay Server 2.4.2 also upgrades LND to 0.21.1 and regenerates macaroons automatically. Umbrel's own BTCPay Server 2.4.2 release notes explicitly instruct Umbrel users to perform the manual removal procedure below. This guide follows Umbrel's platform-specific instructions so the old root key is deliberately replaced and the result can be verified.

## Who Should Do This?

Follow the current Umbrel and BTCPay guidance if all of these were true:

- You ran any BTCPay Server version prior to 2.4.2—including a 2.4.2 release candidate—while it was connected to LND.
- You have not already confirmed that both the macaroon files and `macaroons.db` were freshly regenerated.

> **If BTCPay Server is still older than 2.4.2, stop it or take the deployment offline until it can be updated. Do not rotate credentials and then restart an affected BTCPay Server version.**

Update **BTCPay Server** and the **Lightning Node** app to the newest versions offered by Umbrel before rotating. Do not rely on an old version number from a social-media post; the newest supported release may be newer by the time you read this.

The disclosed LND-credential risk did not apply in the same way to BTCPay stores using another Lightning backend or no Lightning connection. Updating BTCPay Server is still important.

## Why Both the Files and `macaroons.db` Matter

LND usually writes several files such as `admin.macaroon`, `readonly.macaroon`, and `invoice.macaroon`. The exact names and number vary by setup.

Deleting only the individual `.macaroon` files is **not enough**. LND can recreate those files using the same root key stored in `macaroons.db`, which means a previously copied macaroon may remain valid.

Deleting every `.macaroon` file **and** `macaroons.db` while LND is stopped causes LND to create a new macaroon root key and new credential files on startup. That is the step that invalidates the old macaroon set.

## Before You Start

- Make sure BTCPay Server and Lightning Node are already updated.
- Make sure your normal Lightning recovery material is safely stored according to your existing recovery process. This rotation does not replace a seed or static channel backup.
- Expect apps and external wallets that use the old macaroons to lose access until they restart or are paired again.
- Do not make an ordinary backup of the old macaroon files or `macaroons.db`. Restoring the old credential database later could undo the rotation.
- Use the directory for your active Bitcoin network. The path below is for mainnet; do not blindly substitute it on a testnet or signet node.

> **⚠️ Critical safety warning**
>
> Delete only files whose names end in `.macaroon`, plus the one file named exactly `macaroons.db`.
>
> Do **not** delete or modify `wallet.db`, `channel.db`, `channel.backup`, `chan-backup-archives`, TLS files, or any other file or folder. Deleting the wrong LND data can cause loss of access or require a node recovery.

## Safest Method: Use the Umbrel Files App

Menu wording can vary slightly between Umbrel releases, but the data path and safety boundary are the important parts.

### 1. Stop BTCPay Server

On the Umbrel home screen, open the BTCPay Server app menu and choose **Stop**. Wait until Umbrel shows that it is fully stopped.

### 2. Stop Lightning Node

Open the Lightning Node app menu and choose **Stop**. Wait until it is fully stopped too. Do not remove credential files while LND is running.

### 3. Open the LND mainnet credential directory

In Umbrel's **Files** app, navigate through:

`Apps → lightning → data → lnd → data → chain → bitcoin → mainnet`

If your node intentionally uses another Bitcoin network, use that network's directory and verify it before changing anything.

### 4. Identify the exact files

Select:

- Every regular file whose name ends with `.macaroon`
- The file named exactly `macaroons.db`

Common examples include `admin.macaroon`, `readonly.macaroon`, `invoice.macaroon`, `invoices.macaroon`, `router.macaroon`, `signer.macaroon`, `walletkit.macaroon`, and `chainnotifier.macaroon`. Your list may differ.

Pause and check the selection before continuing. Nothing without the `.macaroon` ending should be selected except the exact `macaroons.db` file.

### 5. Delete only those credentials

Delete the selected `.macaroon` files and `macaroons.db`. Leave every other item in the directory untouched.

You generally should not keep restorable copies of these old credentials. If an incident responder specifically asks you to preserve them as evidence, keep them encrypted, offline, and access-controlled, and never restore them to the production node.

### 6. Start Lightning Node

Return to the Umbrel home screen and start **Lightning Node**. Give LND time to start and unlock normally.

### 7. Confirm fresh credentials exist

Reopen the same directory in the Files app. Confirm that LND has created a new `macaroons.db` and fresh `.macaroon` files after the restart.

Seeing only recreated `.macaroon` files is not the full check; confirm that `macaroons.db` was regenerated too.

### 8. Start BTCPay Server

Start **BTCPay Server** and wait for it to become available. BTCPay's Umbrel integration should use the new local credentials.

### 9. Restart or reconnect dependent apps

Restart other Umbrel apps that connect to Lightning so they load the new credentials. External wallets and services using a copied macaroon will need to be paired again with newly generated connection details.

That failure of old credentials is expected. Never paste a macaroon, macaroon hex, connection string, seed, password, API key, node address, or unredacted log into a public support post.

## Verify the Rotation

Before treating the job as complete, check:

- Lightning Node starts and unlocks normally.
- A new `macaroons.db` and new `.macaroon` files exist.
- BTCPay Server starts and its Lightning payment method is available.
- A small test invoice can be created, if that is part of your normal operating procedure.
- Other local apps reconnect after a restart, and external integrations work after being paired again.

Also review the node's recent Lightning payments, on-chain transactions, channel closures, channel balances, peers, and overall balance for activity you do not recognize. Credential rotation prevents future use of the old macaroon; it cannot reverse an action that already happened.

If you see unexplained activity, do not expose credentials while asking for help. Preserve relevant timestamps and sanitized evidence, and use a trusted incident-response or official support channel.

## Frequently Asked Questions

### Should I back up the old macaroons first?

Not as a normal safety step. They are the credentials being revoked, not Lightning recovery material. Restoring the old `macaroons.db` could make old credentials valid again. Preserve them only when a qualified incident responder requests forensic evidence, and never restore that copy to production.

### Will this change my seed or close my channels?

No. Correctly deleting only the macaroon files and `macaroons.db` rotates LND authentication credentials. It does not change the wallet seed or intentionally close channels. The strict file-selection warning matters because deleting other LND data is a different and potentially dangerous action.

### Do I need to replace a BTCPay-generated on-chain hot wallet?

Not solely because of this incident. BTCPay's updated August 7 advisory says BTCPay's on-chain wallets, including hot wallets, were not affected by this vulnerability. LND's own on-chain wallet was still within the affected Lightning node's control, so review that node for unauthorized activity.

This updated guidance supersedes the broader precaution in BTCPay's initial communications. Move funds only when newer official guidance or evidence specific to your wallet gives you a reason to do so.

### Do I need to rotate BTCPay API keys too?

Macaroon rotation does not rotate BTCPay Greenfield API keys. The official incident advisory says the reviewed attacks targeted `.macaroon` files; it does not state that BTCPay API keys were stolen through this issue.

It is still good hygiene to remove unused API keys and webhooks and to revoke anything you believe was exposed. BTCPay Server 2.4.2 also included separate authentication hardening: it fixed a TOTP bypass through Greenfield Basic authentication and made Basic authentication disable itself by default five minutes after account creation, with an opt-in available in account settings and the API. Keep Basic authentication disabled unless you have a documented need for it, but do not confuse those separate fixes with the LND macaroon rotation.

### Can I rotate from the command line instead?

LND documents command-line root-key rotation, but Umbrel publishes a platform-specific Files-app procedure. The graphical method makes the deletion scope visible and avoids publishing a one-line recursive deletion command that could be dangerous when copied with the wrong path. Advanced operators should follow the current LND documentation and their platform's instructions.

## Official Sources

- [BTCPay Server 2.4.2 security advisory](https://blog.btcpayserver.org/security-advisory-btcpay-server-2-4-2/)
- [BTCPay Server 2.4.2 release notes](https://github.com/btcpayserver/btcpayserver/releases/tag/v2.4.2)
- [Umbrel's BTCPay Server 2.4.2 platform instructions](https://github.com/getumbrel/umbrel-apps/blob/a79eefb16b25dc1baa1b96e59e8f0d80a3d2c6b6/btcpay-server/umbrel-app.yml)
- [LND safety documentation: macaroons](https://github.com/lightningnetwork/lnd/blob/v0.21.1-beta/docs/safety.md#macaroons)
- [Lightning Labs guide to LND macaroons](https://docs.lightning.engineering/lightning-network-tools/lnd/macaroons)

**Last verified:** August 17, 2026.
