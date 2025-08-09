#!/usr/bin/env bash
set -euo pipefail
APP_ID=${APP_ID:-io.reaven.LSFGVKLauncher}
BRANCH=${BRANCH:-stable}
TITLE=${TITLE:-"LSFG-VK Launcher"}
COMMENT=${COMMENT:-"Launch Flatpak & host apps with lsfg-vk frame generation"}
DESC=${DESC:-"GTK4/Libadwaita launcher for running applications with Lossless Scaling Frame Generation (lsfg-vk)."}
HOMEPAGE=${HOMEPAGE:-"https://0xREAVEN.github.io/lsfgvk-launcher"}
ICON_URL=${ICON_URL:-"https://0xREAVEN.github.io/lsfgvk-launcher/icons/io.reaven.LSFGVKLauncher.png"}
REPO_URL=${REPO_URL:-"https://0xREAVEN.github.io/lsfgvk-launcher/repo"}
OUT=${OUT:-web/${APP_ID}.flatpakref}

mkdir -p "$(dirname "$OUT")"
cat >"$OUT" <<EOF
[Flatpak Ref]
Name=${APP_ID}
Branch=${BRANCH}
Title=${TITLE}
Comment=${COMMENT}
Description=${DESC}
Homepage=${HOMEPAGE}
Icon=${ICON_URL}
IsRuntime=false
Url=${REPO_URL}
RuntimeRepo=https://flathub.org/repo/flathub.flatpakrepo
EOF

echo "Wrote $OUT"
