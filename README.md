# LSFG-VK Launcher (GTK4/Libadwaita)

[🇫🇷 Lire en Français](#français) · [🇬🇧 Read in English](#english)

---

## English

### 📦 One-click install (Flatpak)
- 👉 **[Download .flatpakref](https://0xreaven.github.io/lsfgvk-launcher/lsfgvk-launcher.flatpakref)**
```bash
flatpak install https://0xreaven.github.io/lsfgvk-launcher/lsfgvk-launcher.flatpakref
flatpak run io.reaven.LSFGVKLauncher
```
<small>Repository: `https://0xreaven.github.io/lsfgvk-launcher/repo`</small>

### What is it?
A minimal GTK4 app that launches **Flatpak and host (system) apps** with [lsfg-vk](https://github.com/PancakeTAS/lsfg-vk): set **X2/X3/X4** multiplier, Flow Scale, Performance mode, HDR, Present mode, and optional `LSFG_PROCESS`. Packaged as a Flatpak; uses `flatpak-spawn --host`.

- **App ID:** `io.reaven.LSFGVKLauncher`  
- **Status:** Prototype v0.2  
- **License:** MIT

## ✨ Features
- Flatpak tab: pick any installed Flatpak and launch with lsfg-vk env vars.
- Host tab: search executables from the host (`compgen -c`) and launch them with lsfg-vk.
- Options: Multiplier (2/3/4/6/8), Flow Scale, Performance, HDR, Present mode, `LSFG_PROCESS`, extra args.
- Preview button shows the exact launch command.

## ▶️ Quick start
1. Install via `.flatpakref` (above).  
2. Open **LSFG-VK Launcher**.  
3. Choose your target (tab **Flatpak** or **Host**).  
4. Set options → **Preview** → **Launch**.

## 🔧 Notes / Requirements
- **lsfg-vk is a Vulkan layer** → target apps must use **Vulkan** (or OpenGL via **Zink**).
- **Flatpak apps**: install the **lsfg-vk VulkanLayer extension** matching the runtime (e.g. 23.08 / 24.08) per upstream docs.
- **Host apps**: install lsfg-vk on your system (optionally `lsfg-vk-ui`).

## 🧰 Build from source
Requirements: Flatpak tooling, GNOME **Sdk/Platform 47**.
```bash
flatpak-builder --user --install --force-clean build flatpak/io.reaven.LSFGVKLauncher.yml
# In toolbox/distrobox, add: --disable-rofiles-fuse
flatpak run io.reaven.LSFGVKLauncher
```

## 🛠 Development
- Code: `app/lsfgvk_launcher.py` (PyGObject, GTK4/Libadwaita)  
- Packaging: see `flatpak/`, `.desktop`, and icon set in `icons/`  
- Distribution: GitHub Action builds/exports a Flatpak repo and publishes a `.flatpakref` to GitHub Pages.

## 🛟 Troubleshooting
- No effect? Ensure the target uses **Vulkan** (or try **Zink** for OpenGL).
- Flatpak doesn’t see the layer? Install the **VulkanLayer lsfg-vk** extension for that runtime.
- In containers (toolbox/distrobox), build with `--disable-rofiles-fuse`.

## 🙏 Credits
- **lsfg-vk** by PancakeTAS and contributors  
- GNOME/Libadwaita team

---

## Français

### 📦 Installation (1-clic)
- 👉 **[Télécharger .flatpakref](https://0xreaven.github.io/lsfgvk-launcher/lsfgvk-launcher.flatpakref)**
```bash
flatpak install https://0xreaven.github.io/lsfgvk-launcher/lsfgvk-launcher.flatpakref
flatpak run io.reaven.LSFGVKLauncher
```
<small>Dépôt : `https://0xreaven.github.io/lsfgvk-launcher/repo`</small>

### Présentation
Une application GTK4 minimaliste pour lancer des **applications Flatpak** et **hôte (système)** avec **lsfg-vk** : choisissez **X2/X3/X4**, Flow Scale, mode Performance, HDR, Present mode, et `LSFG_PROCESS`. Empaquetée en Flatpak, utilise `flatpak-spawn --host`.

- **App ID :** `io.reaven.LSFGVKLauncher`  
- **Statut :** Prototype v0.2  
- **Licence :** MIT

## ✨ Fonctionnalités
- Onglet Flatpak : sélectionner une appli installée et la lancer avec les variables lsfg-vk.
- Onglet Host : rechercher les exécutables du système (`compgen -c`) et les lancer avec lsfg-vk.
- Options : Multiplicateur (2/3/4/6/8), Flow Scale, Performance, HDR, Present mode, `LSFG_PROCESS`, arguments supplémentaires.
- Bouton Preview pour voir la commande exacte.

## ▶️ Démarrage rapide
1. Installez via `.flatpakref` (ci-dessus).  
2. Ouvrez **LSFG-VK Launcher**.  
3. Choisissez la cible (onglet **Flatpak** ou **Host**).  
4. Réglez les options → **Preview** → **Launch**.

## 🔧 Prérequis / Remarques
- **lsfg-vk est une couche Vulkan** → l’app cible doit utiliser **Vulkan** (ou OpenGL via **Zink**).
- **Applis Flatpak** : installez l’**extension VulkanLayer lsfg-vk** correspondant au runtime (23.08 / 24.08).
- **Applis hôte** : installez lsfg-vk sur le système (éventuellement `lsfg-vk-ui`).

## 🧰 Compilation
Pré-requis : Flatpak, GNOME **Sdk/Platform 47**.
```bash
flatpak-builder --user --install --force-clean build flatpak/io.reaven.LSFGVKLauncher.yml
# En toolbox/distrobox : ajouter --disable-rofiles-fuse
flatpak run io.reaven.LSFGVKLauncher
```

## 🛠 Développement
- Code : `app/lsfgvk_launcher.py` (PyGObject, GTK4/Libadwaita)  
- Packaging : `flatpak/`, `.desktop`, icônes `icons/`  
- Distribution : l’Action GitHub publie le dépôt Flatpak et la `.flatpakref` sur GitHub Pages.

## 🛟 Dépannage
- Pas d’injection ? Vérifiez **Vulkan** (ou essayez **Zink**).
- Flatpak ne voit pas la couche ? Installez l’**extension VulkanLayer lsfg-vk** du runtime.
- En container : utilisez `--disable-rofiles-fuse` pour `flatpak-builder`.

## 📜 Licence
MIT
