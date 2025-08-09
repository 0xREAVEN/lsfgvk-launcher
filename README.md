# LSFG‑VK Launcher (GTK4/Libadwaita)

**English | Français**

A minimal GTK4 app that launches **Flatpak and host (system) apps** with [lsfg‑vk](https://github.com/PancakeTAS/lsfg-vk): set **X2/X3/X4** multiplier, Flow Scale, Performance mode, HDR, Present mode, and optional `LSFG_PROCESS`. Packaged as a Flatpak; uses `flatpak-spawn --host` under the hood.

- **App ID:** `io.reaven.LSFGVKLauncher`
- **Status:** Prototype v0.2
- **License:** MIT

## ✨ Features
- Flatpak tab: pick any installed Flatpak and launch with lsfg‑vk env vars.
- Host tab: search executables from the host (`compgen -c`) and launch them with lsfg‑vk.
- Options: Multiplier (2/3/4/6/8), Flow Scale, Performance, HDR, Present mode, `LSFG_PROCESS`, extra args.

> **Note:** lsfg‑vk is a **Vulkan layer**. Target apps must use Vulkan (or OpenGL via Zink) for frame generation to apply.

## 🚀 Install (one‑click via .flatpakref)
Once published to GitHub Pages, you can install via:
```bash
flatpak install https://0xREAVEN.github.io/lsfgvk-launcher/io.reaven.LSFGVKLauncher.flatpakref
```
Or download the file from the project page and double‑click it.

## 🧰 Build from source
Requirements: Flatpak tooling, GNOME Sdk/Platform 46.
```bash
flatpak-builder --user --install --force-clean build flatpak/io.reaven.LSFGVKLauncher.yml
flatpak run io.reaven.LSFGVKLauncher
```

### Flatpak lsfg‑vk runtime extension
For Flatpak apps to see lsfg‑vk, install the Vulkan layer extension matching your runtime (23.08 / 24.08). See the upstream wiki for exact commands.

## 🛠 Development
- Code: `app/lsfgvk_launcher.py` (PyGObject, GTK4/Libadwaita)
- Packaging: see `flatpak/`, `.desktop`, and icon set in `icons/`
- Distribution: GitHub Action publishes a Flatpak repo to GitHub Pages and generates a `.flatpakref`

## 🙏 Credits
- **lsfg‑vk** by PancakeTAS and contributors
- GNOME/Libadwaita team

---

## 🇫🇷 Présentation
Une application GTK4 minimaliste pour lancer des **applications Flatpak et hôte (système)** avec **lsfg‑vk** : choisissez **X2/X3/X4**, Flow Scale, mode Performance, HDR, Present mode, et facultatif `LSFG_PROCESS`. L’appli est empaquetée en Flatpak et utilise `flatpak-spawn --host`.

## ✨ Fonctionnalités
- Onglet Flatpak : sélectionner une appli installée et la lancer avec les variables lsfg‑vk.
- Onglet Host : rechercher les exécutables du système (`compgen -c`) et les lancer avec lsfg‑vk.
- Options : Multiplicateur (2/3/4/6/8), Flow Scale, Performance, HDR, Present mode, `LSFG_PROCESS`, arguments supplémentaires.

> **Note :** lsfg‑vk est une **Vulkan layer**. L’application cible doit utiliser Vulkan (ou OpenGL via Zink) pour que la génération d’images s’applique.

## 🚀 Installation (clic unique via .flatpakref)
Une fois publié sur GitHub Pages :
```bash
flatpak install https://0xREAVEN.github.io/lsfgvk-launcher/io.reaven.LSFGVKLauncher.flatpakref
```
Ou téléchargez le fichier et double‑cliquez‑le.

## 🧰 Compilation
Pré‑requis : Flatpak, GNOME Sdk/Platform 46.
```bash
flatpak-builder --user --install --force-clean build flatpak/io.reaven.LSFGVKLauncher.yml
flatpak run io.reaven.LSFGVKLauncher
```

### Extension runtime lsfg‑vk pour Flatpak
Pour que les applis Flatpak voient lsfg‑vk, installez l’extension Vulkan correspondant au runtime (23.08 / 24.08). Voir la documentation amont.

## 🛠 Développement
- Code : `app/lsfgvk_launcher.py` (PyGObject, GTK4/Libadwaita)
- Packaging : `flatpak/`, `.desktop`, et icônes `icons/`
- Distribution : l’Action GitHub publie le dépôt Flatpak sur GitHub Pages et génère le `.flatpakref`

## 🙏 Remerciements
- **lsfg‑vk** par PancakeTAS et les contributeurs
- Équipe GNOME/Libadwaita

## 📜 Licence
MIT
