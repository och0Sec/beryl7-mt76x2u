#!/bin/bash
set -e
cd /build/openwrt
cp /host/router-dump/kernel.config target/linux/mediatek/mt7988/config-5.4
sed -i 's/ +wifi-scripts//' package/kernel/mac80211/Makefile
cat > .config <<'E'
CONFIG_TARGET_mediatek=y
CONFIG_TARGET_mediatek_mt7988=y
CONFIG_PACKAGE_kmod-cfg80211=m
CONFIG_PACKAGE_kmod-mac80211=m
CONFIG_PACKAGE_kmod-mt7601u=m
CONFIG_PACKAGE_kmod-mt76x2u=m
E
make defconfig 2>&1 | grep -vE '^(WARNING|tmp/)' | tail -15
grep -E 'CONFIG_TARGET_(BOARD|SUBTARGET|ARCH_PACKAGES)=|CONFIG_GCC_VERSION=|CONFIG_PACKAGE_kmod-(mt76|mac80211|cfg80211|mt7601u)|CONFIG_PACKAGE_(MAC80211|CFG80211)' .config
