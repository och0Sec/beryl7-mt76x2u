#!/bin/bash
# Assemble OpenWrt 21.02 + MTK 5.4.281 kernel + backports 6.5 mac80211/mt76 packages
set -e
F=/host/src/mtk-openwrt-feeds
cd /build/openwrt
git log -1 --format="21.02: %h %cd %s"
(cd /build/owrt-master && git log -1 --format="master: %h %cd %s" && grep -E "^PKG_(VERSION|RELEASE)" package/kernel/mac80211/Makefile && grep -E "^PKG_SOURCE_(DATE|VERSION)" package/kernel/mt76/Makefile)
for p in $(find $F/21.02/patches-base -name '*.patch' | sort); do patch -f -p1 -i $p >/dev/null || echo "PATCH FAIL $p"; done
cp -fpR $F/21.02/files/* ./
cp -fpR $F/tools ./
for a in $(cat $F/21.02/remove_list-mtwifi.txt); do rm -rf ./$a; done
rm -rf package/kernel/mac80211 package/kernel/mt76
cp -a /build/owrt-master/package/kernel/mac80211 /build/owrt-master/package/kernel/mt76 package/kernel/
cat include/kernel-5.4 2>/dev/null || grep -n '5.4' include/kernel-version.mk
ls target/linux/mediatek/
