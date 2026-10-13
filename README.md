# mt76x2u for the GL.iNet GL-MT3600BE (Beryl 7)

An out-of-tree build of the `mt76x2u` Wi-Fi driver for the GL.iNet GL-MT3600BE travel router, so an Alfa AWUS036ACM (MT7612U, USB `0e8d:7612`) can serve as its Wi-Fi uplink.

> **Warning.** The stock kernel has no MODVERSIONS. A module built against the wrong struct layouts will load and then crash the router instead of being refused. The prebuilt modules in `out/` are only valid for the exact firmware below. Any firmware upgrade invalidates them.

## Target

| | |
|---|---|
| Firmware | GL.iNet 4.9.0, OpenWrt 21.02-SNAPSHOT |
| Platform | `mediatek/mt7987`, `aarch64_cortex-a53` |
| Kernel | 5.4.281, GCC 8.4.0 |
| vermagic | `5.4.281 SMP mod_unload aarch64` |
| Wireless stack | backports 6.5 (OpenWrt mac80211 package `6.5-1`) |

## Layout

- `out/` — built modules plus MT7662 firmware, with `MD5`, and `kernel.version` (the `/proc/version` of the kernel they were built for).
- `router-files/alfa.init` — the `/etc/init.d/alfa` service.
- `router-dump/` — ground truth pulled from the router: `kernel.config` (`/proc/config.gz`), `kallsyms.txt`, and GL's own `.ko` files used as reference binaries.
- `src/prep.sh`, `src/cfg.sh`, `src/pkg.sh` — build steps.
- `src/fix/` — patches. In use: `bp-0001`, `bp-0002`, `mtk-0010` (backports 6.5 on kernel 5.4) and `900-mtk-build-pass-for-kernel-5.4-core.patch` (mt76). The `mt76-0999*`, `mt76-2000*` files and `dmafix.py` are abandoned attempts, kept for reference.
- `src/od.py`, `src/od2.py` — disassembly diff helpers for comparing a built module against GL's.

## Build

The kernel tree comes from GL's MediaTek feed, which is not vendored here:

```sh
git clone https://github.com/gl-inet/mtk-openwrt-feeds src/mtk-openwrt-feeds
git -C src/mtk-openwrt-feeds checkout 35a658aa
```

The build runs in a Debian 11 Docker container named `owrt`, as an unprivileged user `b`, with a volume mounted at `/build` and this directory at `/host`. It expects:

- `/build/openwrt` — OpenWrt 21.02 at `4a1d8ef55c`
- `/build/owrt-master` — OpenWrt master at `e4ebc7b5662d` (supplies `package/kernel/{mac80211,mt76}`; other commits give the wrong backports version)

```sh
docker exec -u b owrt bash /host/src/prep.sh   # assemble OpenWrt 21.02 + MTK feed + master's mac80211/mt76
docker exec -u b owrt bash /host/src/cfg.sh    # router kernel config + .config
docker exec -u b owrt bash /host/src/pkg.sh    # apply backports patches, build mac80211 (log: /build/m.log)
docker exec -u b owrt bash -c 'cd /build/openwrt && make -j8 V=s package/kernel/mt76/compile'
```

Manual changes in the build tree that the scripts do not reproduce:

- The subtarget is `mt7988` (the feed has no `mt7987`), carrying the router's config.
- `CONFIG_NET_MEDIATEK_HNAT` is disabled (does not compile); the ldlogger `LD_PRELOAD` hook is removed from `include/kernel.mk` and `include/package-defaults.mk`.
- Upstream v6.5 `linux/soc/mediatek/mtk_wed.h` is added to the staging `mac80211-backport` include dir.
- The mt76 patch is copied into `package/kernel/mt76/patches/`.

## Verifying a build

A build is trustworthy when `compat.ko` and `mt7601u.ko` come out byte-identical to the copies in `router-dump/`. That proves compiler, config and core headers match.

GL's own `mac80211.ko` (`router-dump/mac80211.ko`) is not usable: it was built against an older kernel and reads `net_device` fields at different offsets (`ieee80211_ptr` at 792 vs 784). The firmware's `cfg80211.ko` does match and is kept; only `mac80211.ko` is replaced.

## Install

Router access details live in `.env.vars` in the repo root, which is gitignored:

```sh
MGMT_IP=192.0.2.1
USER=root
PASSWORD=changeme
```

On the router:

1. Copy `out/*.ko` and `out/kernel.version` to `/usr/lib/alfa/`, and `out/mt7662*.bin` to `/lib/firmware/`.
2. Run `cmp /proc/version /usr/lib/alfa/kernel.version`. If it reports a difference, stop: your kernel is not the one these modules were built for, and the service will refuse to load them. Do not overwrite `kernel.version` to get past this. If it is silent, `touch /usr/lib/alfa/.ok`.
3. Copy `router-files/alfa.init` to `/etc/init.d/alfa`, make it executable, then `/etc/init.d/alfa enable && /etc/init.d/alfa restart`.
4. Add a DHCP interface on `alfa0` (here `network.alfawan`, metric 18) and put it in the firewall wan zone.

Restarting the service or rebooting drops the uplink, and with it any SSH session routed through it.

## How it works

- The built-in radios use MediaTek's proprietary `mt_wifi` driver. netifd does not manage wireless on this firmware, so the Alfa cannot be configured through `/etc/config/wireless` or the GL UI.
- `/etc/init.d/alfa` swaps GL's `mac80211`/`mt7601u` for the modules in `/usr/lib/alfa/`, creates `alfa0`, and runs its own `wpa_supplicant`. It joins whichever network is `selected` in UCI `repeater` (WPA2-PSK or open only).
- Two guards: the script refuses to load modules if `/proc/version` differs from `/usr/lib/alfa/kernel.version`, and if `/usr/lib/alfa/.ok` is missing (a previous load did not finish). Re-arm with `touch /usr/lib/alfa/.ok`.

## License

GPL-2.0, see `LICENSE`. The patches and modules derive from the Linux kernel, the backports project and mt76. `out/mt7662*.bin` is MediaTek firmware under its own redistribution terms.
