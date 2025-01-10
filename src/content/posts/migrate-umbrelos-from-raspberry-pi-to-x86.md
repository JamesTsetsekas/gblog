---
title: "Migrate Umbrel os from raspberry pi to x86"
description: "A step-by-step guide on migrating UmbrelOS from a Raspberry Pi to an x86 PC, ensuring data preservation and minimal downtime."
pubDate: "2025-01-10 00:00:00"
category: ["bitcoin","lightning","linux","technology"]
banner: "@images/banners/umbrel-migration.png"
tags: ["UmbrelOS", "Raspberry Pi", "x86", "Bitcoin", "Lightning"]
oldViewCount: 0
selected: true
oldKeywords: ["UmbrelOS migration", "Raspberry Pi to x86", "blockchain data preservation"]
---
I was running UmbrelOS on Raspberry Pi, with an external 1TB SSD disk. The machine is obviously underpowered and started to show weakness. So I decided to migrate to a Dell mini-PC, Wyse 5070.

I need to re-use the same SSD disk because the Wyse 5070 doesn’t have enough storage by itself (500GB). Ideally, I can keep all the blockchain data and setup, so that I don’t have to re-sync everything and re-setup everything.

While this may sound like a common question, I did not find many answers on the internet. The closest one is [this one](https://community.umbrel.com/t/transfer-node-from-pi-to-ubuntu-linux-desktop-re-using-the-external-ssd/15179/2). However, UmbrelOS is currently at v1.x. A lot of it doesn’t apply anymore.

Below is how I did it.

### Prepare SSD disk
1. Upgrade Raspberry Pi to the latest UmbrelOS v1.3.
2. Shut it down via Umbrel Settings and unplug SSD disk.

### Prepare PC
1. Follow the instruction to install UmbrelOS on PC. You can find the detailed steps [here](https://github.com/getumbrel/umbrel/wiki/Install-umbrelOS-on-x86-Systems).
2. Don’t install any apps.

### Migrate SSD disk over
1. Plug SSD disk into PC. Permanently mount it at `/mnt/umbrel-ssd`.
    ```bash
    sudo blkid  # Find the UUID of the SSD
    sudo nano /etc/fstab  # Edit fstab to add the mount entry
    ```
    Add the following line to `/etc/fstab` (replace `UUID=e9ae3217-6a06-4721-b725-78e6524b4272` with the actual UUID of your SSD from blkid command):
    ```bash
    UUID=e9ae3217-6a06-4721-b725-78e6524b4272 /mnt/umbrel-ssd ext4 defaults 0 0
    ```
    Then, mount the SSD:
    ```bash
    sudo mount -a
    ```
2. Run the following commands:
    ```bash
    sudo systemctl stop umbrel
    cd /home/umbrel; mv umbrel umbrel.bak; ln -s /mnt/umbrel-ssd/umbrel umbrel
    sudo systemctl start umbrel
    ```

It will take a long time to re-start Umbrel since it will fetch various containers, etc. But it will use the same blockchain and other app-specific settings you had before on the SSD disk. After a couple of coffee breaks, you will be all set!
