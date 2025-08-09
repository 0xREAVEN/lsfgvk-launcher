#!/usr/bin/env bash
set -euo pipefail

APP_ID=${APP_ID:-io.reaven.LSFGVKLauncher}
BRANCH=${BRANCH:-stable}
MANIFEST=${MANIFEST:-flatpak/io.reaven.LSFGVKLauncher.yml}
BUILD_DIR=${BUILD_DIR:-build}
REPO_DIR=${REPO_DIR:-repo}
TITLE=${TITLE:-"Reaven Flatpak Repo"}

flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo || true

flatpak-builder --force-clean \
  --install-deps-from=flathub \
  --repo="${REPO_DIR}" \
  "${BUILD_DIR}" "${MANIFEST}"

flatpak build-update-repo "${REPO_DIR}" \
  --generate-static-deltas \
  --prune \
  --title "${TITLE}"

echo "Exported ${APP_ID} to ${REPO_DIR}/"
