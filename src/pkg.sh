#!/bin/bash
set -e
cd /build/owrt-master && git checkout -q ${1:-e4ebc7b5662d} && git log -1 --format="%h %cs %s"
cd /build/openwrt
rm -rf package/kernel/mac80211 package/kernel/mt76
cp -a /build/owrt-master/package/kernel/mac80211 /build/owrt-master/package/kernel/mt76 package/kernel/
grep -E "^PKG_(VERSION|RELEASE)" package/kernel/mac80211/Makefile; grep -E "^PKG_SOURCE_(DATE|VERSION)" package/kernel/mt76/Makefile
sed -i 's/ +wifi-scripts//' package/kernel/mac80211/Makefile
cp /host/src/fix/bp-0001.patch package/kernel/mac80211/patches/subsys/990-bp-0001.patch
cp /host/src/fix/bp-0002.patch package/kernel/mac80211/patches/subsys/991-bp-0002.patch
cp /host/src/fix/mtk-0010.patch package/kernel/mac80211/patches/subsys/992-mtk-0010.patch
make defconfig >/dev/null 2>&1
make package/kernel/mac80211/clean >/dev/null 2>&1 || true
{ time make -j8 V=s package/kernel/mac80211/compile; echo "MAC_RC=$?"; } > /build/m.log 2>&1 || true
grep -E "MAC_RC=|^real" /build/m.log; grep -n -E "error:|Error [0-9]|No rule|FAILED|rejects|can.t find file" /build/m.log | head -20
