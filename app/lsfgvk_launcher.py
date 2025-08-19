#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Adw, Gio, GLib, Gdk

APP_ID = "io.reaven.LSFGVKLauncher"

# --- i18n minimal -------------------------------------------------------------

LANG_FILE = None  # set during load/save
CURRENT_LANG = "fr"

I18N = {
    "fr": {
        # Basics / Titles
        "app_title": "LSFG-VK Launcher",
        "tab_flatpak": "Flatpak",
        "tab_host": "Host",
        "tab_help": "Aide",

        # Flatpak page
        "flatpak_group": "Cible Flatpak",
        "flatpak_app": "Application",
        "flatpak_choose": "Choisir un Flatpak installé",
        "flatpak_args": "Arguments supplémentaires",
        "flatpak_args_tip": "Arguments passés à l’app (ex: --fullscreen).",
        "note": "Note",
        "note_text": "Cible Vulkan (ou OpenGL via Zink) pour que lsfg-vk s’applique.",

        # Host page
        "host_group": "Cible système (host)",
        "host_cmd": "Exécutable (host)",
        "host_cmd_tip": "Nom/chemin d’un binaire système (vlc, mpv, retroarch, /usr/bin/…).",
        "host_args": "Arguments supplémentaires",
        "host_args_tip": "Arguments passés au binaire système.",

        # Options block
        "opt_group": "LSFG-vk & MangoHud",
        "multiplier": "Multiplicateur (X)",
        "flow": "Flow Scale",
        "flow_tip": "LSFG_FLOW_SCALE — recalage/échelle des flux optiques.",
        "perf": "Mode Performance",
        "perf_tip": "LSFG_PERFORMANCE_MODE — favorise la performance.",
        "hdr": "HDR",
        "hdr_tip": "LSFG_HDR_MODE — force/annonce le HDR si supporté.",
        "present": "Present mode",
        "present_tip": "LSFG_PRESENT_MODE — mode de présentation Vulkan.",
        "process": "LSFG_PROCESS (optionnel)",
        "process_tip": "Limiter au nom du processus cible (laisser vide = global).",
        "mangohud": "Afficher FPS (MangoHud)",
        "mangohud_tip": "Active l’overlay MangoHud (FPS, frametime…)",

        # Presets
        "fav_group": "Favoris",
        "fav_combo": "Favoris",
        "fav_save": "Enregistrer",
        "fav_load": "Charger",
        "fav_run": "Lancer",
        "fav_delete": "Supprimer",
        "fav_default_name": "Preset {name} X{mult}",
        "ask_name": "Nom du favori",
        "ask_name_body": "Choisis un nom pour ce preset",
        "ok": "OK",
        "cancel": "Annuler",

        # Bottom actions
        "preview": "Preview",
        "launch": "Lancer",
        "check": "Check injection",

        # Toasts / errors
        "select_flatpak": "Choisis une application Flatpak.",
        "host_need_exe": "Renseigne un exécutable système (ex: vlc).",
        "mangohud_missing_host": "MangoHud non trouvé sur l’hôte (installe 'mangohud').",
        "mangohud_missing_flatpak": "Extension MangoHud absente pour Flatpak (installe la version 23.08/24.08).",
        "build_err": "Erreur de construction",
        "launch_fail": "Échec de lancement",
        "saved": "Enregistré",
        "deleted": "Supprimé",
        "import_ok": "Import réussi",
        "export_ok": "Exporté dans {path}",
        "reset_ok": "Réglages réinitialisés",

        # Check/injection texts
        "host_check_title": "== HOST INJECTION CHECK ==",
        "fp_check_title": "== FLATPAK INJECTION CHECK ==",
        "env_to_inject": "[ENV à injecter]",
        "env_inside": "[ENV dans le sandbox]",
        "layer_host": "[Layer JSON sur l’hôte]",
        "layer_flatpak": "[Layer JSON dans le sandbox]",
        "layer_missing_host": "lsfg-vk JSON introuvable sur host",
        "layer_missing_fp": "lsfg-vk JSON introuvable dans le sandbox",
        "mangohud_host": "[MangoHud sur l’hôte]",
        "mangohud_ok": "OK: mangohud présent",
        "mangohud_no": "mangohud non trouvé",
        "mangohud_fp": "[Extension MangoHud]",
        "mangohud_req": "MANGOHUD demandé",

        # Help page
        "help_group": "Aide",
        "help_tip1": "Installe l’extension Flatpak lsfg-vk et MangoHud (23.08/24.08 selon le runtime).",
        "help_tip2": "Utilise Preview/Check pour diagnostiquer et copier les lignes utiles.",
        "integrations": "Intégrations",
        "copy_steam": "Copier pour Steam",
        "copy_heroic": "Copier pour Heroic",
        "copy_lutris": "Copier pour Lutris",
        "copied": "Copié dans le presse-papier",

        # Menu (header)
        "menu": "Options",
        "about": "À propos",
        "links": "Liens utiles",
        "open_cfg": "Ouvrir dossier de config",
        "export": "Exporter réglages",
        "import": "Importer réglages",
        "reset": "Réinitialiser",
        "lang": "Langue",
        "fr": "Français",
        "en": "English",

        # About dialog
        "about_title": "À propos",
        "about_desc": "Lance des applications Flatpak et système avec lsfg-vk, MangoHud et options pratiques.",
        "devs": ["reaven"],
        "website": "https://0xreaven.github.io/lsfgvk-launcher/",
        "issues": "https://github.com/0xREAVEN/lsfgvk-launcher/issues",

        # Links
        "link_lsfg": "Wiki lsfg-vk (installation)",
        "link_mh": "MangoHud (projet)",
        "link_mh_flatpak": "MangoHud (extension Flathub)",
        "link_goverlay": "GOverlay (UI overlays)",
    },
    "en": {
        "app_title": "LSFG-VK Launcher",
        "tab_flatpak": "Flatpak",
        "tab_host": "Host",
        "tab_help": "Help",

        "flatpak_group": "Flatpak target",
        "flatpak_app": "Application",
        "flatpak_choose": "Choose an installed Flatpak",
        "flatpak_args": "Extra arguments",
        "flatpak_args_tip": "Arguments passed to the app (e.g. --fullscreen).",
        "note": "Note",
        "note_text": "Target must be Vulkan (or OpenGL via Zink) for lsfg-vk to apply.",

        "host_group": "System target (host)",
        "host_cmd": "Executable (host)",
        "host_cmd_tip": "Binary name/path (vlc, mpv, retroarch, /usr/bin/…).",
        "host_args": "Extra arguments",
        "host_args_tip": "Arguments passed to the system binary.",

        "opt_group": "LSFG-vk & MangoHud",
        "multiplier": "Multiplier (X)",
        "flow": "Flow Scale",
        "flow_tip": "LSFG_FLOW_SCALE — optical flow scaling/alignment.",
        "perf": "Performance mode",
        "perf_tip": "LSFG_PERFORMANCE_MODE — favor performance.",
        "hdr": "HDR",
        "hdr_tip": "LSFG_HDR_MODE — force/advertise HDR if supported.",
        "present": "Present mode",
        "present_tip": "LSFG_PRESENT_MODE — Vulkan present mode.",
        "process": "LSFG_PROCESS (optional)",
        "process_tip": "Restrict to a given process name (leave empty = global).",
        "mangohud": "Show FPS (MangoHud)",
        "mangohud_tip": "Enable MangoHud overlay (FPS, frametime…)",

        "fav_group": "Favorites",
        "fav_combo": "Favorites",
        "fav_save": "Save",
        "fav_load": "Load",
        "fav_run": "Run",
        "fav_delete": "Delete",
        "fav_default_name": "Preset {name} X{mult}",
        "ask_name": "Preset name",
        "ask_name_body": "Choose a name for this preset",
        "ok": "OK",
        "cancel": "Cancel",

        "preview": "Preview",
        "launch": "Launch",
        "check": "Check injection",

        "select_flatpak": "Select a Flatpak application.",
        "host_need_exe": "Enter a system executable (e.g. vlc).",
        "mangohud_missing_host": "MangoHud not found on host (install 'mangohud').",
        "mangohud_missing_flatpak": "MangoHud Flatpak extension missing (install 23.08/24.08).",
        "build_err": "Build error",
        "launch_fail": "Launch failed",
        "saved": "Saved",
        "deleted": "Deleted",
        "import_ok": "Import OK",
        "export_ok": "Exported to {path}",
        "reset_ok": "Settings reset",

        "host_check_title": "== HOST INJECTION CHECK ==",
        "fp_check_title": "== FLATPAK INJECTION CHECK ==",
        "env_to_inject": "[ENV to inject]",
        "env_inside": "[ENV inside sandbox]",
        "layer_host": "[Layer JSON on host]",
        "layer_flatpak": "[Layer JSON inside sandbox]",
        "layer_missing_host": "lsfg-vk JSON not found on host",
        "layer_missing_fp": "lsfg-vk JSON not found inside sandbox",
        "mangohud_host": "[MangoHud on host]",
        "mangohud_ok": "OK: mangohud present",
        "mangohud_no": "mangohud not found",
        "mangohud_fp": "[MangoHud extension]",
        "mangohud_req": "MANGOHUD requested",

        "help_group": "Help",
        "help_tip1": "Install lsfg-vk and MangoHud Flatpak extensions (23.08/24.08 as per runtime).",
        "help_tip2": "Use Preview/Check to diagnose and copy the useful lines.",
        "integrations": "Integrations",
        "copy_steam": "Copy for Steam",
        "copy_heroic": "Copy for Heroic",
        "copy_lutris": "Copy for Lutris",
        "copied": "Copied to clipboard",

        "menu": "Options",
        "about": "About",
        "links": "Useful links",
        "open_cfg": "Open config folder",
        "export": "Export settings",
        "import": "Import settings",
        "reset": "Reset settings",
        "lang": "Language",
        "fr": "French",
        "en": "English",

        "about_title": "About",
        "about_desc": "Launch Flatpak and system apps with lsfg-vk, MangoHud and handy options.",
        "devs": ["reaven"],
        "website": "https://0xreaven.github.io/lsfgvk-launcher/",
        "issues": "https://github.com/0xREAVEN/lsfgvk-launcher/issues",

        "link_lsfg": "lsfg-vk Wiki (install)",
        "link_mh": "MangoHud (project)",
        "link_mh_flatpak": "MangoHud (Flathub extension)",
        "link_goverlay": "GOverlay (overlay UI)",
    },
}

def t(key: str) -> str:
    return I18N.get(CURRENT_LANG, I18N["fr"]).get(key, key)

# --- helpers / host calls -----------------------------------------------------

def run_host(args: List[str]) -> Tuple[int, str, str]:
    """Always use host for flatpak or system checks."""
    cmd = ["flatpak-spawn", "--host"] + args
    try:
        p = subprocess.run(cmd, text=True, capture_output=True, check=False)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def join_shell(parts: List[str]) -> str:
    return " ".join(shlex.quote(p) for p in parts)

def list_flatpaks() -> List[str]:
    code, out, _ = run_host(["flatpak", "list", "--app", "--columns=application"])
    if code != 0:
        return []
    apps, seen = [], set()
    for line in out.splitlines():
        s = line.strip()
        if s and s not in seen:
            apps.append(s); seen.add(s)
    return apps

def open_uri(uri: str):
    Gio.AppInfo.launch_default_for_uri(uri, None)

# --- persistence --------------------------------------------------------------

def cfg_dir() -> str:
    base = os.path.join(GLib.get_user_config_dir(), APP_ID)
    os.makedirs(base, exist_ok=True)
    return base

def cfg_file() -> str:
    global LANG_FILE
    f = os.path.join(cfg_dir(), "settings.json")
    LANG_FILE = f
    return f

def load_json(default: dict) -> dict:
    try:
        with open(cfg_file(), "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                # merge shallow
                merged = default.copy()
                for k, v in data.items():
                    merged[k] = v
                return merged
    except Exception:
        pass
    return default

def save_json(data: dict) -> None:
    try:
        with open(cfg_file(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

# --- model --------------------------------------------------------------------

@dataclass
class LSFGShared:
    multiplier: str = "2"     # "2","3","4","6","8"
    flow_scale: bool = False
    performance: bool = False
    hdr: bool = False
    present_mode: str = "auto" # auto/fifo/mailbox/immediate
    lsfg_process: str = ""
    mangohud: bool = True

@dataclass
class PresetFlatpak:
    name: str = ""
    appid: str = ""
    args: str = ""
    shared: LSFGShared = field(default_factory=LSFGShared)

@dataclass
class PresetHost:
    name: str = ""
    cmd: str = ""
    args: str = ""
    shared: LSFGShared = field(default_factory=LSFGShared)

@dataclass
class Settings:
    language: str = "fr"
    shared: LSFGShared = field(default_factory=LSFGShared)
    flatpak_app: str = ""
    flatpak_args: str = ""
    host_cmd: str = ""
    host_args: str = ""
    presets_flatpak: List[PresetFlatpak] = field(default_factory=list)
    presets_host: List[PresetHost] = field(default_factory=list)

    @staticmethod
    def from_dict(d: dict) -> "Settings":
        s = Settings()
        s.language = d.get("language", "fr")
        s.shared = LSFGShared(**d.get("shared", {}))
        s.flatpak_app = d.get("flatpak_app", "")
        s.flatpak_args = d.get("flatpak_args", "")
        s.host_cmd = d.get("host_cmd", "")
        s.host_args = d.get("host_args", "")
        # presets
        s.presets_flatpak = []
        for it in d.get("presets_flatpak", []):
            s.presets_flatpak.append(PresetFlatpak(
                name=it.get("name",""),
                appid=it.get("appid",""),
                args=it.get("args",""),
                shared=LSFGShared(**it.get("shared", {}))
            ))
        s.presets_host = []
        for it in d.get("presets_host", []):
            s.presets_host.append(PresetHost(
                name=it.get("name",""),
                cmd=it.get("cmd",""),
                args=it.get("args",""),
                shared=LSFGShared(**it.get("shared", {}))
            ))
        return s

    def to_dict(self) -> dict:
        return {
            "language": self.language,
            "shared": asdict(self.shared),
            "flatpak_app": self.flatpak_app,
            "flatpak_args": self.flatpak_args,
            "host_cmd": self.host_cmd,
            "host_args": self.host_args,
            "presets_flatpak": [ {"name":p.name,"appid":p.appid,"args":p.args,"shared":asdict(p.shared)} for p in self.presets_flatpak ],
            "presets_host": [ {"name":p.name,"cmd":p.cmd,"args":p.args,"shared":asdict(p.shared)} for p in self.presets_host ],
        }

def load_settings() -> Settings:
    global CURRENT_LANG
    default = Settings().to_dict()
    data = load_json(default)
    s = Settings.from_dict(data)
    CURRENT_LANG = s.language if s.language in I18N else "fr"
    return s

def save_settings(s: Settings):
    save_json(s.to_dict())

# --- option controls ----------------------------------------------------------

class OptionControls:
    def __init__(self, shared_init: LSFGShared):
        self.box = Adw.PreferencesGroup(title=t("opt_group"))

        # Multiplier (toggle buttons)
        row_mult = Adw.ActionRow(title=t("multiplier"))
        self._mult = shared_init.multiplier or "2"
        mult_box = Gtk.Box(spacing=6)
        self._mult_buttons: List[Gtk.ToggleButton] = []
        for label in ["2","3","4","6","8"]:
            b = Gtk.ToggleButton(label=label)
            b.set_active(label == self._mult)
            b.connect("toggled", self._on_mult_toggled, label)
            self._mult_buttons.append(b)
            mult_box.append(b)
        row_mult.add_suffix(mult_box)

        # Flow
        self.row_flow = Adw.SwitchRow(title=t("flow"))
        self.row_flow.set_active(bool(shared_init.flow_scale))
        self.row_flow.add_suffix(self._info_btn(t("flow_tip")))

        # Perf
        self.row_perf = Adw.SwitchRow(title=t("perf"))
        self.row_perf.set_active(bool(shared_init.performance))
        self.row_perf.add_suffix(self._info_btn(t("perf_tip")))

        # HDR
        self.row_hdr = Adw.SwitchRow(title=t("hdr"))
        self.row_hdr.set_active(bool(shared_init.hdr))
        self.row_hdr.add_suffix(self._info_btn(t("hdr_tip")))

        # Present
        pm_model = Gtk.StringList.new(["auto","fifo","mailbox","immediate"])
        self.row_present = Adw.ComboRow(title=t("present"), model=pm_model)
        sel = 0
        for i in range(pm_model.get_n_items()):
            if pm_model.get_string(i) == (shared_init.present_mode or "auto"):
                sel = i; break
        self.row_present.set_selected(sel)
        self.row_present.add_suffix(self._info_btn(t("present_tip")))

        # LSFG_PROCESS
        self.row_process = Adw.EntryRow(title=t("process"))
        self.row_process.set_text(shared_init.lsfg_process or "")
        self.row_process.add_suffix(self._info_btn(t("process_tip")))

        # MangoHud
        self.row_mh = Adw.SwitchRow(title=t("mangohud"))
        self.row_mh.set_active(bool(shared_init.mangohud))
        self.row_mh.add_suffix(self._info_btn(t("mangohud_tip")))

        self.box.add(row_mult)
        self.box.add(self.row_flow)
        self.box.add(self.row_perf)
        self.box.add(self.row_hdr)
        self.box.add(self.row_present)
        self.box.add(self.row_process)
        self.box.add(self.row_mh)

    def _info_btn(self, tooltip: str):
        btn = Gtk.Button.new_from_icon_name("dialog-information-symbolic")
        btn.set_valign(Gtk.Align.CENTER)
        btn.set_tooltip_text(tooltip)
        btn.connect("clicked", lambda *a: self._info_dialog(tooltip))
        return btn

    def _info_dialog(self, text: str):
        dlg = Adw.MessageDialog.new(None, "Info", text)
        dlg.add_response("ok", t("ok"))
        dlg.set_close_response("ok")
        dlg.present()

    def _on_mult_toggled(self, btn: Gtk.ToggleButton, label: str):
        if not btn.get_active():
            return
        self._mult = label
        for b in self._mult_buttons:
            if b is not btn and b.get_active():
                b.set_active(False)

    def to_shared(self) -> LSFGShared:
        model = self.row_present.get_model()
        idx = self.row_present.get_selected()
        present = model.get_string(idx) if 0 <= idx < model.get_n_items() else "auto"
        return LSFGShared(
            multiplier=self._mult or "2",
            flow_scale=self.row_flow.get_active(),
            performance=self.row_perf.get_active(),
            hdr=self.row_hdr.get_active(),
            present_mode=present,
            lsfg_process=self.row_process.get_text().strip(),
            mangohud=self.row_mh.get_active()
        )

    def set_from_shared(self, s: LSFGShared):
        # multiplier
        for b in self._mult_buttons:
            b.set_active(b.get_label() == (s.multiplier or "2"))
        self._mult = s.multiplier or "2"
        # switches
        self.row_flow.set_active(bool(s.flow_scale))
        self.row_perf.set_active(bool(s.performance))
        self.row_hdr.set_active(bool(s.hdr))
        # present
        model = self.row_present.get_model()
        sel = 0
        for i in range(model.get_n_items()):
            if model.get_string(i) == (s.present_mode or "auto"):
                sel = i; break
        self.row_present.set_selected(sel)
        # process + mh
        self.row_process.set_text(s.lsfg_process or "")
        self.row_mh.set_active(bool(s.mangohud))

# --- main window --------------------------------------------------------------

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application, settings: Settings):
        super().__init__(application=app)
        self.set_default_size(980, 700)
        self.set_title(t("app_title"))
        self.settings = settings

        self.toasts = Adw.ToastOverlay()

        # Stack
        self.stack = Adw.ViewStack()

        # Flatpak page
        self.page_flatpak = self._build_flatpak_page()
        self.stack.add_titled(self.page_flatpak, "flatpak", t("tab_flatpak"))

        # Host page
        self.page_host = self._build_host_page()
        self.stack.add_titled(self.page_host, "host", t("tab_host"))

        # Help page
        self.page_help = self._build_help_page()
        self.stack.add_titled(self.page_help, "help", t("tab_help"))

        # Toolbar + header
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()

        switch_title = Adw.ViewSwitcherTitle()
        switch_title.props.stack = self.stack
        header.set_title_widget(switch_title)

        # Menu button (☰)
        header.pack_end(self._build_menu_button())

        toolbar.add_top_bar(header)

        switch_bar = Adw.ViewSwitcherBar()
        switch_bar.props.stack = self.stack
        toolbar.add_bottom_bar(switch_bar)

        # Bottom actions
        bottom = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                         margin_top=8, margin_bottom=8, margin_start=12, margin_end=12)
        hb = Gtk.Box(spacing=8)
        self.btn_preview = Gtk.Button(label=t("preview"))
        self.btn_launch = Gtk.Button(label=t("launch"))
        self.btn_check = Gtk.Button(label=t("check"))
        self.btn_preview.connect("clicked", self.on_preview)
        self.btn_launch.connect("clicked", self.on_launch)
        self.btn_check.connect("clicked", self.on_check)
        hb.append(self.btn_preview); hb.append(self.btn_launch); hb.append(self.btn_check)

        self.preview = Gtk.TextView(editable=False, wrap_mode=Gtk.WrapMode.CHAR)
        try: self.preview.set_monospace(True)
        except Exception: pass
        self.preview.set_size_request(-1, 160)
        sw = Gtk.ScrolledWindow()
        sw.set_child(self.preview)

        bottom.append(hb)
        bottom.append(sw)

        # Root
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root.append(self.stack)
        root.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        root.append(bottom)

        toolbar.set_content(root)
        self.toasts.set_child(toolbar)
        self.set_content(self.toasts)

        GLib.idle_add(self._reload_flatpak_list)

    # --- menu "☰" ---

    def _build_menu_button(self) -> Gtk.Widget:
        menu = Gio.Menu()

        # Language
        sec_lang = Gio.Menu()
        sec_lang.append(t("fr"), "app.set-language::fr")
        sec_lang.append(t("en"), "app.set-language::en")
        menu.append_section(t("lang"), sec_lang)

        # Links
        sec_links = Gio.Menu()
        sec_links.append(t("link_lsfg"), "app.open-link::https://github.com/PancakeTAS/lsfg-vk/wiki")
        sec_links.append(t("link_mh"), "app.open-link::https://github.com/flightlessmango/MangoHud")
        sec_links.append(t("link_mh_flatpak"), "app.open-link::https://flathub.org/apps/details/org.freedesktop.Platform.VulkanLayer.MangoHud")
        sec_links.append(t("link_goverlay"), "app.open-link::https://github.com/benjamimgois/goverlay")
        menu.append_section(t("links"), sec_links)

        # Config actions
        sec_cfg = Gio.Menu()
        sec_cfg.append(t("open_cfg"), "app.open-config")
        sec_cfg.append(t("export"), "app.export")
        sec_cfg.append(t("import"), "app.import")
        sec_cfg.append(t("reset"), "app.reset")
        menu.append_section("Config", sec_cfg)

        # About
        about_sec = Gio.Menu()
        about_sec.append(t("about"), "app.about")
        menu.append_section(None, about_sec)

        # Button
        btn = Adw.MenuButton()
        btn.set_icon_name("open-menu-symbolic")
        btn.set_menu_model(menu)
        btn.set_tooltip_text(t("menu"))
        return btn

    # --- Flatpak page ---

    def _build_flatpak_page(self) -> Adw.PreferencesPage:
        page = Adw.PreferencesPage()

        # Favorites (flatpak)
        fav_grp = Adw.PreferencesGroup(title=t("fav_group"))
        self.fp_preset_model = Gtk.StringList.new([])
        self.fp_preset_combo = Adw.ComboRow(title=t("fav_combo"), model=self.fp_preset_model)
        fav_btns = Gtk.Box(spacing=6)
        b_save = Gtk.Button(label=t("fav_save"))
        b_load = Gtk.Button(label=t("fav_load"))
        b_run  = Gtk.Button(label=t("fav_run"))
        b_del  = Gtk.Button(label=t("fav_delete"))
        b_save.connect("clicked", self._fp_preset_save)
        b_load.connect("clicked", self._fp_preset_load)
        b_run.connect("clicked", self._fp_preset_run)
        b_del.connect("clicked", self._fp_preset_delete)
        for b in (b_save,b_load,b_run,b_del): fav_btns.append(b)
        self.fp_preset_combo.add_suffix(fav_btns)
        fav_grp.add(self.fp_preset_combo)

        # Target group
        grp = Adw.PreferencesGroup(title=t("flatpak_group"))

        self.flatpak_model = Gtk.StringList.new([])
        self.flatpak_combo = Adw.ComboRow(title=t("flatpak_app"), subtitle=t("flatpak_choose"),
                                          model=self.flatpak_model)
        try: self.flatpak_combo.set_use_subtitle(True)
        except Exception: pass

        self.flatpak_icon = Gtk.Image.new_from_icon_name("application-x-executable-symbolic")
        self.flatpak_icon.set_pixel_size(24)
        self.flatpak_combo.add_suffix(self.flatpak_icon)

        btn_refresh = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        btn_refresh.set_tooltip_text("Refresh")
        btn_refresh.connect("clicked", lambda *_: self._reload_flatpak_list())
        self.flatpak_combo.add_suffix(btn_refresh)
        self.flatpak_combo.connect("notify::selected", self._on_flatpak_selected)

        self.flatpak_args = Adw.EntryRow(title=t("flatpak_args"),
                                         text=self.settings.flatpak_args or "")
        self.flatpak_args.add_suffix(self._info_btn(t("flatpak_args_tip")))

        hint = Adw.ActionRow(title=t("note"), subtitle=t("note_text"))

        grp.add(self.flatpak_combo)
        grp.add(self.flatpak_args)
        grp.add(hint)

        # Options (shared)
        self.ctrl_flatpak = OptionControls(self.settings.shared)

        # Build page
        page.add(fav_grp)
        page.add(grp)
        page.add(self.ctrl_flatpak.box)

        # Fill favorites
        self._refresh_fp_presets()
        return page

    # --- Host page ---

    def _build_host_page(self) -> Adw.PreferencesPage:
        page = Adw.PreferencesPage()

        # Favorites (host)
        fav_grp = Adw.PreferencesGroup(title=t("fav_group"))
        self.h_preset_model = Gtk.StringList.new([])
        self.h_preset_combo = Adw.ComboRow(title=t("fav_combo"), model=self.h_preset_model)
        fav_btns = Gtk.Box(spacing=6)
        b_save = Gtk.Button(label=t("fav_save"))
        b_load = Gtk.Button(label=t("fav_load"))
        b_run  = Gtk.Button(label=t("fav_run"))
        b_del  = Gtk.Button(label=t("fav_delete"))
        b_save.connect("clicked", self._h_preset_save)
        b_load.connect("clicked", self._h_preset_load)
        b_run.connect("clicked", self._h_preset_run)
        b_del.connect("clicked", self._h_preset_delete)
        for b in (b_save,b_load,b_run,b_del): fav_btns.append(b)
        self.h_preset_combo.add_suffix(fav_btns)
        fav_grp.add(self.h_preset_combo)

        # Target group
        grp = Adw.PreferencesGroup(title=t("host_group"))

        self.host_cmd = Adw.EntryRow(title=t("host_cmd"),
                                     text=self.settings.host_cmd or "")
        self.host_cmd.add_suffix(self._info_btn(t("host_cmd_tip")))

        self.host_args = Adw.EntryRow(title=t("host_args"),
                                      text=self.settings.host_args or "")
        self.host_args.add_suffix(self._info_btn(t("host_args_tip")))

        grp.add(self.host_cmd)
        grp.add(self.host_args)

        self.ctrl_host = OptionControls(self.settings.shared)

        page.add(fav_grp)
        page.add(grp)
        page.add(self.ctrl_host.box)

        self._refresh_h_presets()
        return page

    # --- Help page with integrations ---

    def _build_help_page(self) -> Adw.PreferencesPage:
        page = Adw.PreferencesPage()

        grp = Adw.PreferencesGroup(title=t("help_group"))
        grp.add(Adw.ActionRow(title=t("help_tip1")))
        grp.add(Adw.ActionRow(title=t("help_tip2")))

        integ = Adw.PreferencesGroup(title=t("integrations"))
        b1 = Gtk.Button(label=t("copy_steam"));  b1.connect("clicked", self._copy_steam)
        b2 = Gtk.Button(label=t("copy_heroic")); b2.connect("clicked", self._copy_heroic)
        b3 = Gtk.Button(label=t("copy_lutris")); b3.connect("clicked", self._copy_lutris)

        hb = Gtk.Box(spacing=6)
        hb.append(b1); hb.append(b2); hb.append(b3)
        row = Adw.ActionRow(title="")
        row.add_suffix(hb)
        integ.add(row)

        page.add(grp)
        page.add(integ)
        return page

    # --- small helpers ---

    def _info_btn(self, tooltip: str):
        btn = Gtk.Button.new_from_icon_name("dialog-information-symbolic")
        btn.set_valign(Gtk.Align.CENTER)
        btn.set_tooltip_text(tooltip)
        btn.connect("clicked", lambda *a: self._dialog_info(tooltip))
        return btn

    def _dialog_info(self, text: str):
        dlg = Adw.MessageDialog.new(self.get_root(), "Info", text)
        dlg.add_response("ok", t("ok"))
        dlg.set_close_response("ok")
        dlg.present()

    def _set_preview(self, text: str):
        self.preview.get_buffer().set_text(text)

    def _toast(self, text: str):
        self.toasts.add_toast(Adw.Toast.new(text))

    def _copy_text(self, text: str):
        disp = Gdk.Display.get_default()
        if disp:
            cb = disp.get_clipboard()
            cb.set_text(text)
            self._toast(t("copied"))

    # --- Flatpak list & icon ---

    def _reload_flatpak_list(self):
        apps = list_flatpaks()
        self.flatpak_model.splice(0, self.flatpak_model.get_n_items(), apps)
        if self.settings.flatpak_app and self.settings.flatpak_app in apps:
            self.flatpak_combo.set_selected(apps.index(self.settings.flatpak_app))
        elif apps:
            self.flatpak_combo.set_selected(0)
        self._update_flatpak_icon()

    def _on_flatpak_selected(self, *_):
        self._update_flatpak_icon()
        idx = self.flatpak_combo.get_selected()
        if 0 <= idx < self.flatpak_model.get_n_items():
            self.settings.flatpak_app = self.flatpak_model.get_string(idx)
            save_settings(self.settings)

    def _update_flatpak_icon(self):
        idx = self.flatpak_combo.get_selected()
        name = ""
        if 0 <= idx < self.flatpak_model.get_n_items():
            name = self.flatpak_model.get_string(idx)
        # Essayons l’icône AppID, sinon fallback
        self.flatpak_icon.set_from_icon_name(name or "application-x-executable-symbolic")

    # --- Collect options / build env ---

    def _collect_shared(self) -> LSFGShared:
        # on considère la section Flatpak comme source
        s = self.ctrl_flatpak.to_shared()
        # synchronise Host
        self.ctrl_host.set_from_shared(s)
        return s

    def _env_kv(self, s: LSFGShared) -> List[str]:
        env = [
            f"LSFG_MULTIPLIER={s.multiplier or '2'}",
            f"LSFG_FLOW_SCALE={'1' if s.flow_scale else '0'}",
            f"LSFG_PERFORMANCE_MODE={'1' if s.performance else '0'}",
            f"LSFG_HDR_MODE={'1' if s.hdr else '0'}",
            "VK_INSTANCE_LAYERS=lsfg_vk",
        ]
        if s.present_mode and s.present_mode != "auto":
            env.append(f"LSFG_PRESENT_MODE={s.present_mode}")
        if s.lsfg_process:
            env.append(f"LSFG_PROCESS={s.lsfg_process}")
        if s.mangohud:
            env.append("MANGOHUD=1")
        return env

    def _as_flatpak_env_flags(self, env_kv: List[str]) -> List[str]:
        return [f"--env={kv}" for kv in env_kv]

    # --- Commands builders ---

    def _cmd_flatpak(self) -> List[str]:
        s = self._collect_shared()
        self.settings.shared = s
        self.settings.flatpak_args = (self.flatpak_args.get_text() or "").strip()
        idx = self.flatpak_combo.get_selected()
        if idx < 0 or idx >= self.flatpak_model.get_n_items():
            raise RuntimeError(t("select_flatpak"))
        appid = self.flatpak_model.get_string(idx)
        self.settings.flatpak_app = appid

        env = self._env_kv(s)
        args = shlex.split(self.settings.flatpak_args) if self.settings.flatpak_args else []

        cmd = ["flatpak-spawn", "--host", "flatpak", "run"]
        cmd += self._as_flatpak_env_flags(env)  # IMPORTANT: avant l’AppID
        cmd.append(appid)
        cmd += args
        return cmd

    def _cmd_host(self) -> List[str]:
        s = self._collect_shared()
        self.settings.shared = s

        self.settings.host_cmd  = (self.host_cmd.get_text() or "").strip()
        self.settings.host_args = (self.host_args.get_text() or "").strip()
        if not self.settings.host_cmd:
            raise RuntimeError(t("host_need_exe"))

        env = self._env_kv(s)
        args = shlex.split(self.settings.host_args) if self.settings.host_args else []
        return ["flatpak-spawn", "--host", "env", *env, self.settings.host_cmd, *args]

    # --- Preview / Launch / Check ---

    def on_preview(self, *_):
        try:
            cmd = self._cmd_host() if self.stack.get_visible_child_name() == "host" else self._cmd_flatpak()
            save_settings(self.settings)
            self._set_preview(join_shell(cmd))
        except Exception as e:
            self._set_preview(f"# ERROR: {e}")

    def on_launch(self, *_):
        s = self._collect_shared()
        # MangoHud presence hints
        if s.mangohud:
            if self.stack.get_visible_child_name() == "host":
                if not self._check_mangohud_host():
                    self._toast(t("mangohud_missing_host"))
            else:
                if not self._check_mangohud_flatpak():
                    self._toast(t("mangohud_missing_flatpak"))
        # Build & run
        try:
            cmd = self._cmd_host() if self.stack.get_visible_child_name() == "host" else self._cmd_flatpak()
            save_settings(self.settings)
        except Exception as e:
            self._show_error(t("build_err"), str(e))
            self.on_preview()
            return
        try:
            Gio.Subprocess.new(cmd, Gio.SubprocessFlags.NONE)
            self.on_preview()
        except Exception as e:
            self._show_error(t("launch_fail"), str(e))
            self.on_preview()

    def on_check(self, *_):
        try:
            is_host = (self.stack.get_visible_child_name() == "host")
            s = self._collect_shared()
            env = self._env_kv(s)

            if is_host:
                # Host check
                script = f"""
echo '{t("host_check_title")}'
echo '{t("env_to_inject")}'
printf '%s\\n' {" ".join(shlex.quote(e) for e in env)}

echo
echo '{t("layer_host")}'
for d in /usr/share/vulkan/explicit_layer.d /usr/local/share/vulkan/explicit_layer.d /etc/vulkan/explicit_layer.d; do
  ls "$d"/*lsfg*json 2>/dev/null && echo "OK: $d" && FOUND=1 && break
done
[ -n "$FOUND" ] || echo '{t("layer_missing_host")}'

echo
echo '{t("mangohud_host")}'
command -v mangohud >/dev/null && echo '{t("mangohud_ok")}' || echo '{t("mangohud_no")}'
"""
                code, out, err = run_host(["sh","-lc", script])
                txt = (out + ("\n[stderr]\n"+err if err else "")).strip()

            else:
                # Flatpak check
                idx = self.flatpak_combo.get_selected()
                if idx < 0 or idx >= self.flatpak_model.get_n_items():
                    raise RuntimeError(t("select_flatpak"))
                appid = self.flatpak_model.get_string(idx)

                # Runtime info (best-effort)
                rcode, rtext, _ = run_host(["flatpak","info","--show-runtime",appid])
                runtime_line = rtext.strip() if rcode == 0 else ""

                env_flags = [f"--env={kv}" for kv in env]
                script = f"""
echo '{t("fp_check_title")}'
echo '{t("env_inside")}'
env | grep -E '^(LSFG_|VK_INSTANCE_LAYERS|MANGOHUD)'

echo
echo 'Runtime: {runtime_line}'

echo
echo '{t("layer_flatpak")}'
for d in /usr/share/vulkan/explicit_layer.d /usr/etc/vulkan/explicit_layer.d /etc/vulkan/explicit_layer.d; do
  ls "$d"/*lsfg*json 2>/dev/null && echo "OK: $d" && FOUND=1 && break
done
[ -n "$FOUND" ] || echo '{t("layer_missing_fp")}'

echo
echo '{t("mangohud_fp")}'
env | grep -q '^MANGOHUD=1' && echo '{t("mangohud_req")}'
"""
                code, out, err = run_host(["flatpak","run", *env_flags, "--command=sh", appid, "-lc", script])
                txt = (out + ("\n[stderr]\n"+err if err else "")).strip()

            self._set_preview(txt)
        except Exception as e:
            self._set_preview(f"# CHECK ERROR: {e}")

    # --- MangoHud presence checks ---

    def _check_mangohud_host(self) -> bool:
        code, out, _ = run_host(["sh", "-lc", "command -v mangohud || true"])
        return bool(out.strip())

    def _check_mangohud_flatpak(self) -> bool:
        code, out, _ = run_host(["flatpak", "list", "--columns=application,branch"])
        if code != 0:
            return False
        for line in out.splitlines():
            if line.startswith("org.freedesktop.Platform.VulkanLayer.MangoHud"):
                return True
        return False

    # --- Presets: Flatpak ---

    def _refresh_fp_presets(self):
        names = [p.name or f"{p.appid}" for p in self.settings.presets_flatpak]
        self.fp_preset_model.splice(0, self.fp_preset_model.get_n_items(), names)

    def _fp_preset_save(self, *_):
        idx = self.flatpak_combo.get_selected()
        if idx < 0 or idx >= self.flatpak_model.get_n_items():
            self._show_error("Preset", t("select_flatpak")); return
        appid = self.flatpak_model.get_string(idx)
        args = (self.flatpak_args.get_text() or "").strip()
        shared = self.ctrl_flatpak.to_shared()

        # Ask name
        name = self._ask_text(t("ask_name"), t("ask_name_body"),
                              default=t("fav_default_name").format(name=appid, mult=shared.multiplier))
        if not name:
            return
        self.settings.presets_flatpak.append(PresetFlatpak(name=name, appid=appid, args=args, shared=shared))
        save_settings(self.settings)
        self._refresh_fp_presets()
        self._toast(t("saved"))

    def _fp_preset_load(self, *_):
        i = self.fp_preset_combo.get_selected()
        if 0 <= i < len(self.settings.presets_flatpak):
            p = self.settings.presets_flatpak[i]
            # set fields
            apps = [self.flatpak_model.get_string(k) for k in range(self.flatpak_model.get_n_items())]
            if p.appid in apps:
                self.flatpak_combo.set_selected(apps.index(p.appid))
            self.flatpak_args.set_text(p.args or "")
            self.ctrl_flatpak.set_from_shared(p.shared)
            # sync host controls too
            self.ctrl_host.set_from_shared(p.shared)
            self._toast(t("saved"))

    def _fp_preset_run(self, *_):
        self._fp_preset_load()
        self.on_launch()

    def _fp_preset_delete(self, *_):
        i = self.fp_preset_combo.get_selected()
        if 0 <= i < len(self.settings.presets_flatpak):
            del self.settings.presets_flatpak[i]
            save_settings(self.settings)
            self._refresh_fp_presets()
            self._toast(t("deleted"))

    # --- Presets: Host ---

    def _refresh_h_presets(self):
        names = [p.name or f"{p.cmd}" for p in self.settings.presets_host]
        self.h_preset_model.splice(0, self.h_preset_model.get_n_items(), names)

    def _h_preset_save(self, *_):
        cmd = (self.host_cmd.get_text() or "").strip()
        if not cmd:
            self._show_error("Preset", t("host_need_exe")); return
        args = (self.host_args.get_text() or "").strip()
        shared = self.ctrl_host.to_shared()
        name = self._ask_text(t("ask_name"), t("ask_name_body"),
                              default=t("fav_default_name").format(name=os.path.basename(cmd), mult=shared.multiplier))
        if not name:
            return
        self.settings.presets_host.append(PresetHost(name=name, cmd=cmd, args=args, shared=shared))
        save_settings(self.settings)
        self._refresh_h_presets()
        self._toast(t("saved"))

    def _h_preset_load(self, *_):
        i = self.h_preset_combo.get_selected()
        if 0 <= i < len(self.settings.presets_host):
            p = self.settings.presets_host[i]
            self.host_cmd.set_text(p.cmd or "")
            self.host_args.set_text(p.args or "")
            self.ctrl_host.set_from_shared(p.shared)
            self.ctrl_flatpak.set_from_shared(p.shared)
            self._toast(t("saved"))

    def _h_preset_run(self, *_):
        self._h_preset_load()
        self.on_launch()

    def _h_preset_delete(self, *_):
        i = self.h_preset_combo.get_selected()
        if 0 <= i < len(self.settings.presets_host):
            del self.settings.presets_host[i]
            save_settings(self.settings)
            self._refresh_h_presets()
            self._toast(t("deleted"))

    # --- Ask text helper ---

    def _ask_text(self, title: str, body: str, default: str="") -> Optional[str]:
        dlg = Adw.MessageDialog.new(self.get_root(), title, body)
        entry = Gtk.Entry()
        entry.set_text(default)
        entry.set_activates_default(True)
        box = Gtk.Box()
        box.append(entry)
        dlg.set_extra_child(box)
        dlg.add_response("ok", t("ok"))
        dlg.add_response("cancel", t("cancel"))
        dlg.set_close_response("cancel")
        dlg.set_default_response("ok")
        dlg.present()

        done = GLib.MainLoop()
        result = {"text": None}

        def on_response(d, resp):
            if resp == "ok":
                result["text"] = entry.get_text().strip()
            done.quit()

        dlg.connect("response", on_response)
        done.run()
        return result["text"]

    # --- Generators: Steam/Heroic/Lutris ---

    def _gen_env_lines(self) -> Tuple[str,str,str]:
        s = self._collect_shared()
        env = self._env_kv(s)
        # Steam expects env before %command%
        steam = " ".join(env + ["%command%"])
        heroic = "\n".join(env)  # to paste in UI
        lutris = "\n".join(env)  # env block
        return steam, heroic, lutris

    def _copy_steam(self, *_):
        steam, _, _ = self._gen_env_lines()
        self._copy_text(steam)

    def _copy_heroic(self, *_):
        _, heroic, _ = self._gen_env_lines()
        self._copy_text(heroic)

    def _copy_lutris(self, *_):
        _, _, lutris = self._gen_env_lines()
        self._copy_text(lutris)

    # --- Errors ---

    def _show_error(self, title: str, body: str):
        dlg = Adw.MessageDialog.new(self.get_root(), title, body)
        dlg.add_response("ok", t("ok"))
        dlg.set_close_response("ok")
        dlg.present()

# --- Application with actions (menu) ------------------------------------------

class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.settings = load_settings()
        self.connect("activate", self._on_activate)
        self._install_actions()

    def _on_activate(self, *_):
        global CURRENT_LANG
        CURRENT_LANG = self.settings.language if self.settings.language in I18N else "fr"
        if self.props.active_window:
            self.props.active_window.present(); return
        self.win = MainWindow(self, self.settings)
        self.win.present()

    def _install_actions(self):
        # open-link::<uri>
        act_open_link = Gio.SimpleAction.new_stateful("open-link", GLib.VariantType.new("s"), None)
        act_open_link.connect("activate", self._on_open_link)
        self.add_action(act_open_link)

        # set-language::fr/en
        act_lang = Gio.SimpleAction.new_stateful("set-language", GLib.VariantType.new("s"), None)
        act_lang.connect("activate", self._on_set_language)
        self.add_action(act_lang)

        # open-config
        act_open_cfg = Gio.SimpleAction.new("open-config", None)
        act_open_cfg.connect("activate", self._on_open_config)
        self.add_action(act_open_cfg)

        # export/import/reset
        act_export = Gio.SimpleAction.new("export", None)
        act_export.connect("activate", self._on_export)
        self.add_action(act_export)

        act_import = Gio.SimpleAction.new("import", None)
        act_import.connect("activate", self._on_import)
        self.add_action(act_import)

        act_reset = Gio.SimpleAction.new("reset", None)
        act_reset.connect("activate", self._on_reset)
        self.add_action(act_reset)

        # about
        act_about = Gio.SimpleAction.new("about", None)
        act_about.connect("activate", self._on_about)
        self.add_action(act_about)

    # --- actions impl ---

    def _on_open_link(self, action, param):
        uri = param.get_string() if param else ""
        if uri:
            open_uri(uri)

    def _on_set_language(self, action, param):
        global CURRENT_LANG
        lang = param.get_string() if param else "fr"
        if lang not in I18N:
            lang = "fr"
        self.settings.language = lang
        save_settings(self.settings)
        CURRENT_LANG = lang
        # rebuild window
        if self.props.active_window:
            self.props.active_window.destroy()
        self.win = MainWindow(self, self.settings)
        self.win.present()

    def _on_open_config(self, *_):
        uri = GLib.filename_to_uri(cfg_dir())
        open_uri(uri)

    def _on_export(self, *_):
        outp = os.path.join(cfg_dir(), f"settings-export-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.json")
        try:
            with open(outp, "w", encoding="utf-8") as f:
                json.dump(self.settings.to_dict(), f, indent=2)
            self._toast(t("export_ok").format(path=outp))
        except Exception as e:
            self._error("Export", str(e))

    def _on_import(self, *_):
        # Simple: charger le dernier export s’il existe
        base = cfg_dir()
        cand = sorted([p for p in os.listdir(base) if p.startswith("settings-export-") and p.endswith(".json")])
        if not cand:
            self._error("Import", "Aucun fichier settings-export-*.json dans le dossier config."); return
        path = os.path.join(base, cand[-1])
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.settings = Settings.from_dict(data)
            save_settings(self.settings)
            # rebuild
            if self.props.active_window:
                self.props.active_window.destroy()
            self.win = MainWindow(self, self.settings)
            self.win.present()
            self._toast(t("import_ok"))
        except Exception as e:
            self._error("Import", str(e))

    def _on_reset(self, *_):
        self.settings = Settings()  # defaults
        save_settings(self.settings)
        if self.props.active_window:
            self.props.active_window.destroy()
        self.win = MainWindow(self, self.settings)
        self.win.present()
        self._toast(t("reset_ok"))

    def _on_about(self, *_):
        dlg = Adw.AboutWindow.new()
        dlg.set_application_name(t("app_title"))
        dlg.set_developers(I18N[CURRENT_LANG]["devs"])
        dlg.set_comments(t("about_desc"))
        dlg.set_website(I18N[CURRENT_LANG]["website"])
        dlg.set_issue_url(I18N[CURRENT_LANG]["issues"])
        dlg.set_license_type(Gtk.License.MIT_X11)
        dlg.present()

    # small helpers
    def _toast(self, text: str):
        if self.props.active_window:
            self.props.active_window.toasts.add_toast(Adw.Toast.new(text))

    def _error(self, title: str, body: str):
        if self.props.active_window:
            dlg = Adw.MessageDialog.new(self.props.active_window.get_root(), title, body)
            dlg.add_response("ok", t("ok"))
            dlg.set_close_response("ok")
            dlg.present()

# --- main ---------------------------------------------------------------------

def main(argv):
    Adw.init()
    app = App()
    return app.run(argv)

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))