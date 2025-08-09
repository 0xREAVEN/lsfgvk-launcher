#!/usr/bin/env bash
set -euo pipefail

GH_USER=${GH_USER:-0xREAVEN}
GH_REPO=${GH_REPO:-lsfgvk-launcher}
APP_ID=${APP_ID:-io.reaven.LSFGVKLauncher}
BRANCH=${BRANCH:-stable}
MANIFEST=${MANIFEST:-flatpak/io.reaven.LSFGVKLauncher.yml}

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing $1"; exit 1; }; }
need flatpak-builder
if ! command -v inkscape >/dev/null && ! command -v rsvg-convert >/dev/null; then
  echo "Install inkscape or librsvg (rsvg-convert)"; exit 1
fi
if ! command -v convert >/dev/null; then
  echo "(Optional) Install ImageMagick for multi-size PNGs)"
fi

mkdir -p icons/hicolor/{512x512,256x256,128x128,64x64,48x48,32x32,24x24,16x16}/apps
if command -v inkscape >/dev/null; then
  inkscape icons/io.reaven.LSFGVKLauncher.svg \
    --export-type=png \
    --export-filename=icons/hicolor/512x512/apps/${APP_ID}.png \
    --export-width=512 --export-height=512
else
  rsvg-convert -w 512 -h 512 -o icons/hicolor/512x512/apps/${APP_ID}.png icons/io.reaven.LSFGVKLauncher.svg
fi
if command -v convert >/dev/null; then
  convert icons/hicolor/512x512/apps/${APP_ID}.png -resize 256x256 icons/hicolor/256x256/apps/${APP_ID}.png
  convert icons/hicolor/512x512/apps/${APP_ID}.png -resize 128x128 icons/hicolor/128x128/apps/${APP_ID}.png
  convert icons/hicolor/512x512/apps/${APP_ID}.png -resize 64x64  icons/hicolor/64x64/apps/${APP_ID}.png
  convert icons/hicolor/512x512/apps/${APP_ID}.png -resize 48x48  icons/hicolor/48x48/apps/${APP_ID}.png
  convert icons/hicolor/512x512/apps/${APP_ID}.png -resize 32x32  icons/hicolor/32x32/apps/${APP_ID}.png
  convert icons/hicolor/512x512/apps/${APP_ID}.png -resize 24x24  icons/hicolor/24x24/apps/${APP_ID}.png
  convert icons/hicolor/512x512/apps/${APP_ID}.png -resize 16x16  icons/hicolor/16x16/apps/${APP_ID}.png
fi

bash scripts/build_and_export.sh
APP_ID=${APP_ID} \
HOMEPAGE="https://${GH_USER}.github.io/${GH_REPO}" \
ICON_URL="https://${GH_USER}.github.io/${GH_REPO}/icons/${APP_ID}.png" \
REPO_URL="https://${GH_USER}.github.io/${GH_REPO}/repo" \
  bash scripts/make_flatpakref.sh

mkdir -p web/repo web/icons
rsync -a repo/ web/repo/ || true
cp icons/hicolor/128x128/apps/${APP_ID}.png web/icons/${APP_ID}.png || true
echo "<html><body><h1>${GH_USER} Flatpak Repo</h1><p><a href=\"${APP_ID}.flatpakref\">Install ${APP_ID}</a></p></body></html>" > web/index.html

if [ ! -d .git ]; then
  git init
  git checkout -b main
  git add -A
  git commit -m "Initial import: ${APP_ID} + repo + flatpakref"
  git remote add origin "git@github.com:${GH_USER}/${GH_REPO}.git" || true
  echo "If remote add failed, set it manually: git remote set-url origin git@github.com:${GH_USER}/${GH_REPO}.git"
  git push -u origin main || true
else
  git add -A
  git commit -m "Update: build/export + flatpakref"
  git push
fi

echo "Done. Check GitHub → Actions for the Pages publish workflow."
