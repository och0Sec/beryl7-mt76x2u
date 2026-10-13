# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Not an application. This directory holds the out-of-tree build of the `mt76x2u` Wi-Fi driver for a GL.iNet GL-MT3600BE (Beryl 7) travel router, so an Alfa AWUS036ACM (MT7612U, USB `0e8d:7612`) can serve as its Wi-Fi uplink. There is no test suite or linter; "verification" means comparing binaries and checking the live router.

## Target (must match exactly)

- Firmware 4.9.0, OpenWrt 21.02-SNAPSHOT, `mediatek/mt7987`, `aarch64_cortex-a53`
- Kernel 5.4.281, GCC 8.4.0, vermagic `5.4.281 SMP mod_unload aarch64`, no MODVERSIONS
- Wireless stack: backports 6.5 (OpenWrt mac80211 package `6.5-1`)

Without MODVERSIONS the kernel will load a module built against the wrong struct layouts, and it will crash rather than refuse. Any firmware upgrade invalidates everything in `out/`.

## Layout

- `router-dump/` — ground truth pulled from the router: `kernel.config` (`/proc/config.gz`), `kallsyms.txt`, and GL's own `.ko` files used as reference binaries.
- `src/mtk-openwrt-feeds/` — clone of `github.com/gl-inet/mtk-openwrt-feeds`; `21.02/` supplies the 5.4.281 kernel tree.
- `src/fix/` — patches. In use: `bp-0001`, `bp-0002`, `mtk-0010` (backports 6.5 on kernel 5.4) and `900-mtk-build-pass-for-kernel-5.4-core.patch` (mt76). The `mt76-2000*` files and `dmafix.py` are abandoned attempts.
- `src/od.py`, `src/od2.py` — disassembly diff helpers for comparing a built module against GL's.
- `out/` — built modules plus MT7662 firmware, with `MD5`.
- `router-files/alfa.init` — source of `/etc/init.d/alfa` on the router.
- `router-files/alfa.hotplug` — source of `/etc/hotplug.d/ieee80211/99-alfa`; restarts the service when the adapter's phy appears (it enumerates ~70 s into boot, after the init script has given up).

## Build

Runs in Docker container `owrt` (Debian 11, user `b`; stopped, start with `docker start owrt`). Volume `owrt` is `/build`, this directory is `/host`. Run git and make as `b`, not root.

```sh
docker exec -u b owrt bash /host/src/prep.sh   # assemble OpenWrt 21.02 + MTK feed + master's mac80211/mt76
docker exec -u b owrt bash /host/src/cfg.sh    # router kernel config + .config
docker exec -u b owrt bash /host/src/pkg.sh    # apply backports patches, build mac80211 (log: /build/m.log)
docker exec -u b owrt bash -c 'cd /build/openwrt && make -j8 V=s package/kernel/mt76/compile'
```

`/build/openwrt` is OpenWrt 21.02 @`4a1d8ef55c`; `package/kernel/{mac80211,mt76}` come from OpenWrt master @`e4ebc7b5662d` in `/build/owrt-master`. Other master commits give the wrong backports version.

Manual changes in the build tree that the scripts do not reproduce:

- The subtarget is `mt7988` (the feed has no `mt7987`), carrying the router's config.
- `CONFIG_NET_MEDIATEK_HNAT` is disabled (does not compile); the ldlogger `LD_PRELOAD` hook is removed from `include/kernel.mk` and `include/package-defaults.mk`.
- Upstream v6.5 `linux/soc/mediatek/mtk_wed.h` is added to the staging `mac80211-backport` include dir.
- The mt76 patch is copied into `package/kernel/mt76/patches/`.

## Verifying a build

A build is trustworthy when `compat.ko` and `mt7601u.ko` come out byte-identical to the copies in `router-dump/`. That proves compiler, config and core headers match.

Do not use GL's feed `mac80211.ko` (`router-dump/mac80211.ko`): it was built against an older kernel and reads `net_device` fields at different offsets (`ieee80211_ptr` at 792 vs 784). The firmware's ROM `cfg80211.ko` does match and is kept; only `mac80211.ko` is replaced.

## Router side

Access: `ssh root@<MGMT_IP>` with credentials in `.env.vars`. No `sshpass`; use an `SSH_ASKPASS` helper. Never print values from that file, or SSIDs/keys from router config.

How the pieces fit:

- The built-in radios use MediaTek's proprietary `mt_wifi` driver. netifd does not manage wireless here, so the Alfa cannot be configured through `/etc/config/wireless` or the GL UI.
- `/etc/init.d/alfa` swaps GL's `mac80211`/`mt7601u` for the modules in `/usr/lib/alfa/`, creates `alfa0`, and runs its own `wpa_supplicant`. It joins whichever network is `selected` in UCI `repeater` (WPA2-PSK or open only).
- `network.alfawan` (DHCP, metric 18) is in the firewall wan zone and is a `kmwan` member. Metrics: wan 10, alfawan 18, built-in repeater `wwan` 20, tethering 30.
- Two guards in the init script: it refuses to load if `/proc/version` differs from `/usr/lib/alfa/kernel.version`, and if `/usr/lib/alfa/.ok` is missing (a previous load did not finish). Re-arm with `touch /usr/lib/alfa/.ok`.
- Router busybox lacks `diff` and `paste`; use `cmp`.
- Pre-change configs are in `/root/alfa-backup/` on the router.

Deploy: copy `out/*.ko` to `/usr/lib/alfa/`, firmware to `/lib/firmware/`, `router-files/alfa.init` to `/etc/init.d/alfa`, `router-files/alfa.hotplug` to `/etc/hotplug.d/ieee80211/99-alfa`, then `/etc/init.d/alfa restart`. Restarting or rebooting drops the uplink, and with it any SSH session routed through it.
