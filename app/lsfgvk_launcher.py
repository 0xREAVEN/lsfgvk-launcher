#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
#
# LSFG-VK Launcher — GTK4/Libadwaita
# - Flatpak + Host launchers with lsfg-vk and optional MangoHud
# - Uses flatpak-spawn --host for all host interactions
# - Options inline per page, persistence in ~/.var/app/<APPID>/config/settings.json
#
# Note: no 'List'/'Tuple' from typing to avoid NameError: use built-in generics.

import os
import json
import shlex
import subprocess
from dataclasses import dataclass, asdict, field
from pathlib import Path

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GLib

APP_ID = "io.reaven.LSFGVKLauncher"

CONFIG_DIR = Path(GLib.get_user_config_dir()) / "lsfgvk-launcher"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = CONFIG_DIR / "settings.json"

# ---------------- i18n (very lightweight) ----------------

_STRINGS = {
    "en": {
        "app_title": "LSFG-VK Launcher",
        "tab_flatpak": "Flatpak",
        "tab_host": "Host",
        "target_app": "Application",
        "target_host_cmd": "Host command",
        "target_extra_args": "Extra arguments",
        "options": "Options",
        "multiplier": "Multiplier",
        "flow_scale": "Flow scale",
        "performance": "Performance mode",
        "hdr": "HDR mode",
        "lsfg_process": "LSFG_PROCESS (optional)",
        "mangohud": "Enable MangoHud",
        "present_mode": "Present mode",
        "none": "None",
        "preview": "Preview",
        "launch": "Launch",
        "check": "Check injection",
        "favorites": "Favorites / Presets",
        "fav_save": "Save current as favorite",
        "fav_name": "Preset name",
        "fav_load": "Load",
        "fav_run": "Run",
        "fav_delete": "Delete",
        "menu": "Menu",
        "about": "About",
        "open_config": "Open config folder",
        "export_settings": "Export settings",
        "import_settings": "Import settings",
        "reset_settings": "Reset settings",
        "language": "Language",
        "lang_en": "English",
        "lang_fr": "French",
        "links": "Useful links",
        "link_lsfg": "lsfg-vk wiki",
        "link_mangohud": "MangoHud",
        "link_goverlay": "GOverlay",
        "pick_flatpak": "Pick a Flatpak app",
        "host_cmd_placeholder": "e.g. vlc, mpv, retroarch…",
        "args_placeholder": "--fullscreen (example)",
        "injection_result": "Injection / Layer check",
        "copied": "Copied to clipboard",
        "error": "Error",
        "ok": "OK",
        "cancel": "Cancel",
        "close": "Close",
        "no_flatpak_cli": "flatpak CLI not available on host.",
        "no_selection": "No Flatpak application selected.",
        "export_done": "Settings exported.",
        "import_done": "Settings imported.",
        "reset_done": "Settings reset.",
        "fav_saved": "Favorite saved.",
        "fav_exists": "Preset already exists (overwritten).",
    },
    "fr": {
        "app_title": "LSFG-VK Launcher",
        "tab_flatpak": "Flatpak",
        "tab_host": "Système",
        "target_app": "Application",
        "target_host_cmd": "Commande système",
        "target_extra_args": "Arguments supplémentaires",
        "options": "Options",
        "multiplier": "Multiplicateur",
        "flow_scale": "Flow scale",
        "performance": "Mode performance",
        "hdr": "Mode HDR",
        "lsfg_process": "LSFG_PROCESS (optionnel)",
        "mangohud": "Activer MangoHud",
        "present_mode": "Present mode",
        "none": "Aucun",
        "preview": "Prévisualiser",
        "launch": "Lancer",
        "check": "Vérifier l’injection",
        "favorites": "Favoris / Presets",
        "fav_save": "Enregistrer le preset",
        "fav_name": "Nom du preset",
        "fav_load": "Charger",
        "fav_run": "Lancer",
        "fav_delete": "Supprimer",
        "menu": "Menu",
        "about": "À propos",
        "open_config": "Ouvrir le dossier de config",
        "export_settings": "Exporter les réglages",
        "import_settings": "Importer les réglages",
        "reset_settings": "Réinitialiser",
        "language": "Langue",
        "lang_en": "Anglais",
        "lang_fr": "Français",
        "links": "Liens utiles",
        "link_lsfg": "Wiki lsfg-vk",
        "link_mangohud": "MangoHud",
        "link_goverlay": "GOverlay",
        "pick_flatpak": "Choisir une application Flatpak",
        "host_cmd_placeholder": "ex: vlc, mpv, retroarch…",
        "args_placeholder": "--fullscreen (exemple)",
        "injection_result": "Vérification injection / couche",
        "copied": "Copié dans le presse-papiers",
        "error": "Erreur",
        "ok": "OK",
        "cancel": "Annuler",
        "close": "Fermer",
        "no_flatpak_cli": "La commande flatpak n’est pas disponible sur l’hôte.",
        "no_selection": "Aucune application Flatpak sélectionnée.",
        "export_done": "Réglages exportés.",
        "import_done": "Réglages importés.",
        "reset_done": "Réglages réinitialisés.",
        "fav_saved": "Preset enregistré.",
        "fav_exists": "Preset existant (écrasé).",
    },
}

def tr(lang: str, key: str) -> str:
    return _STRINGS.get(lang, _STRINGS["en"]).get(key, key)

# ---------------- Settings model ----------------

@dataclass
class Options:
    multiplier: int = 2
    flow_scale: int = 0
    performance: bool = False
    hdr: bool = False
    present_mode: str = ""          # "" (none) or custom
    lsfg_process: str = ""
    extra_args: str = ""
    mangohud: bool = False
    extra_layers: str = ""          # additional layers tokens (':'-separated)

@dataclass
class Settings:
    lang: str = "fr"
    last_flatpak: str = ""
    last_host_cmd: str = ""
    favorites: list[dict] = field(default_factory=list)   # list of {"name":..., "mode":"flatpak|host", "target":"...", "options":{...}}
    options: Options = field(default_factory=Options)

def load_settings() -> Settings:
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            # nested dataclass rebuild
            opts = Options(**data.get("options", {}))
            s = Settings(
                lang=data.get("lang", "fr"),
                last_flatpak=data.get("last_flatpak", ""),
                last_host_cmd=data.get("last_host_cmd", ""),
                favorites=data.get("favorites", []),
                options=opts,
            )
            return s
        except Exception:
            pass
    return Settings()

def save_settings(s: Settings) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = asdict(s)
    CONFIG_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

# ---------------- Host helpers (flatpak-spawn) ----------------

def run_host(args: list[str]) -> tuple[int, str, str]:
    """
    Run a command on the host through flatpak-spawn --host.
    Returns (code, stdout, stderr).
    """
    proc = subprocess.run(
        ["flatpak-spawn", "--host"] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr

def host_has_flatpak() -> bool:
    code, _, _ = run_host(["sh", "-lc", "command -v flatpak >/dev/null 2>&1"])
    return code == 0

def list_flatpaks() -> list[tuple[str, str]]:
    """
    Returns list of (appid, title). Uses host flatpak CLI.
    """
    if not host_has_flatpak():
        return []
    # columns: application,title are widely available
    code, out, _ = run_host(["flatpak", "list", "--app", "--columns=application,title"])
    if code != 0:
        return []
    rows = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        appid = parts[0].strip()
        title = parts[1].strip() if len(parts) > 1 else appid
        rows.append((appid, title))
    # sort by title
    rows.sort(key=lambda x: x[1].lower())
    return rows

# ---------------- UI ----------------

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application, settings: Settings):
        super().__init__(application=app)
        self.set_title(self._t("app_title"))
        self.set_default_size(880, 640)

        self.settings = settings
        self.opts = settings.options

        self._flatpaks: list[tuple[str, str]] = []  # (appid, title)

        self.header = Adw.HeaderBar()
        self.set_titlebar(self.header)

        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)

        # Tabs
        self.page_flatpak = self._build_flatpak_page()
        self.page_host = self._build_host_page()

        self.stack.add_titled(self.page_flatpak, "flatpak", self._t("tab_flatpak"))
        self.stack.add_titled(self.page_host, "host", self._t("tab_host"))

        # Switcher
        switcher = Adw.ViewSwitcher(stack=self.stack, policy=Adw.ViewSwitcherPolicy.WIDE)
        self.header.pack_start(switcher)

        # Menu button
        self.header.pack_end(self._build_menu())

        # Root
        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        root_box.append(self.stack)
        self.set_content(root_box)

        # Load list
        self._refresh_flatpak_list_async()

    # ------------- i18n helper
    def _t(self, key: str) -> str:
        return tr(self.settings.lang, key)

    # ------------- Menu
    def _build_menu(self) -> Gtk.MenuButton:
        menu = Gio.Menu()
        # Language sub-menu
        lang_menu = Gio.Menu()
        lang_menu.append(self._t("lang_en"), "app.lang_en")
        lang_menu.append(self._t("lang_fr"), "app.lang_fr")

        # Links sub-menu
        links = Gio.Menu()
        links.append(self._t("link_lsfg"), "app.link_lsfg")
        links.append(self._t("link_mangohud"), "app.link_mangohud")
        links.append(self._t("link_goverlay"), "app.link_goverlay")

        menu.append_section(self._t("language"), lang_menu)
        menu.append_section(self._t("links"), links)

        actions = Gio.Menu()
        actions.append(self._t("open_config"), "app.open_config")
        actions.append(self._t("export_settings"), "app.export_settings")
        actions.append(self._t("import_settings"), "app.import_settings")
        actions.append(self._t("reset_settings"), "app.reset_settings")
        menu.append_section(self._t("menu"), actions)

        btn = Gtk.MenuButton()
        btn.set_icon_name("open-menu-symbolic")
        btn.set_menu_model(menu)
        return btn

    # ------------- Page: Flatpak
    def _build_flatpak_page(self) -> Adw.PreferencesPage:
        page = Adw.PreferencesPage()

        # Target group
        grp_target = Adw.PreferencesGroup(title=self._t("target_app"))

        # App selector (DropDown)
        self.flatpak_string_list = Gtk.StringList.new([])
        self.dd_flatpak = Gtk.DropDown(model=self.flatpak_string_list, enable_search=True)
        self.dd_flatpak.set_hexpand(True)
        self._flatpak_ids: list[str] = []

        row_app = Adw.ActionRow(title=self._t("pick_flatpak"))
        row_app.add_suffix(self.dd_flatpak)
        row_app.set_activatable_widget(self.dd_flatpak)
        grp_target.add(row_app)

        # Extra args
        self.row_flatpak_args = Adw.EntryRow(title=self._t("target_extra_args"))
        self.row_flatpak_args.set_text(self.opts.extra_args or "")
        grp_target.add(self.row_flatpak_args)

        # Options group (shared widgets)
        grp_opts = self._build_options_group()

        # Favorites group
        grp_fav = self._build_favorites_group(mode="flatpak")

        # Actions
        grp_actions = Adw.PreferencesGroup()
        box_btn = Gtk.Box(spacing=8)
        self.btn_preview_f = Gtk.Button(label=self._t("preview"))
        self.btn_check_f = Gtk.Button(label=self._t("check"))
        self.btn_launch_f = Gtk.Button(label=self._t("launch"))
        box_btn.append(self.btn_preview_f)
        box_btn.append(self.btn_check_f)
        box_btn.append(self.btn_launch_f)
        grp_actions.add(box_btn)

        # Connect callbacks
        self.btn_preview_f.connect("clicked", self._on_preview_flatpak)
        self.btn_check_f.connect("clicked", self._on_check_flatpak)
        self.btn_launch_f.connect("clicked", self._on_launch_flatpak)

        page.add(grp_target)
        page.add(grp_opts)
        page.add(grp_fav)
        page.add(grp_actions)
        return page

    # ------------- Page: Host
    def _build_host_page(self) -> Adw.PreferencesPage:
        page = Adw.PreferencesPage()

        grp_target = Adw.PreferencesGroup(title=self._t("target_host_cmd"))
        self.row_host_cmd = Adw.EntryRow(title=self._t("target_host_cmd"))
        self.row_host_cmd.set_text(self.settings.last_host_cmd or "")
        self.row_host_cmd.set_show_apply_button(False)
        self.row_host_cmd.set_input_purpose(Gtk.InputPurpose.FREE_FORM)
        self.row_host_cmd.set_attributes([Gtk.Attribute.new("placeholder-text", self._t("host_cmd_placeholder"))])  # visual hint
        grp_target.add(self.row_host_cmd)

        self.row_host_args = Adw.EntryRow(title=self._t("target_extra_args"))
        self.row_host_args.set_text(self.opts.extra_args or "")
        grp_target.add(self.row_host_args)

        grp_opts = self._build_options_group()

        grp_fav = self._build_favorites_group(mode="host")

        grp_actions = Adw.PreferencesGroup()
        box_btn = Gtk.Box(spacing=8)
        self.btn_preview_h = Gtk.Button(label=self._t("preview"))
        self.btn_check_h = Gtk.Button(label=self._t("check"))
        self.btn_launch_h = Gtk.Button(label=self._t("launch"))
        box_btn.append(self.btn_preview_h)
        box_btn.append(self.btn_check_h)
        box_btn.append(self.btn_launch_h)
        grp_actions.add(box_btn)

        self.btn_preview_h.connect("clicked", self._on_preview_host)
        self.btn_check_h.connect("clicked", self._on_check_host)
        self.btn_launch_h.connect("clicked", self._on_launch_host)

        page.add(grp_target)
        page.add(grp_opts)
        page.add(grp_fav)
        page.add(grp_actions)
        return page

    # ------------- Shared Options group
    def _build_options_group(self) -> Adw.PreferencesGroup:
        grp = Adw.PreferencesGroup(title=self._t("options"))

        # Multiplier
        self.row_mult = Adw.ComboRow(title=self._t("multiplier"))
        mults = ["2", "3", "4", "6", "8"]
        self._mult_list = Gtk.StringList.new(mults)
        self.row_mult.set_model(self._mult_list)
        try:
            idx = mults.index(str(self.opts.multiplier))
        except ValueError:
            idx = 0
        self.row_mult.set_selected(idx)
        grp.add(self.row_mult)

        # Flow scale (0..3)
        adj = Gtk.Adjustment(lower=0, upper=8, step_increment=1, page_increment=1, page_size=0)
        self.row_flow = Adw.SpinRow(title=self._t("flow_scale"), adjustment=adj)
        self.row_flow.set_value(float(self.opts.flow_scale))
        grp.add(self.row_flow)

        # Performance
        self.row_perf = Adw.SwitchRow(title=self._t("performance"))
        self.row_perf.set_active(self.opts.performance)
        grp.add(self.row_perf)

        # HDR
        self.row_hdr = Adw.SwitchRow(title=self._t("hdr"))
        self.row_hdr.set_active(self.opts.hdr)
        grp.add(self.row_hdr)

        # Present mode (free text for now; empty=none)
        self.row_present = Adw.EntryRow(title=self._t("present_mode"))
        self.row_present.set_text(self.opts.present_mode or "")
        grp.add(self.row_present)

        # LSFG_PROCESS
        self.row_lsfg_proc = Adw.EntryRow(title=self._t("lsfg_process"))
        self.row_lsfg_proc.set_text(self.opts.lsfg_process or "")
        grp.add(self.row_lsfg_proc)

        # Extra layers (append to VK_INSTANCE_LAYERS)
        self.row_extra_layers = Adw.EntryRow(title="Extra Vulkan layers (':' separated)")
        self.row_extra_layers.set_text(self.opts.extra_layers or "")
        grp.add(self.row_extra_layers)

        # MangoHud
        self.row_mangohud = Adw.SwitchRow(title=self._t("mangohud"))
        self.row_mangohud.set_active(self.opts.mangohud)
        grp.add(self.row_mangohud)

        # Extra args (shared default) — NOTE: per-page also exists; we keep this as "default"
        # (Kept minimal to avoid duplicate UI; pages have their own "args" entry.)

        return grp

    # ------------- Favorites group
    def _build_favorites_group(self, mode: str) -> Adw.PreferencesGroup:
        grp = Adw.PreferencesGroup(title=self._t("favorites"))

        row = Adw.ActionRow(title=self._t("fav_name"))
        self.fav_name_entry = Gtk.Entry()
        self.fav_name_entry.set_hexpand(True)
        row.add_suffix(self.fav_name_entry)
        grp.add(row)

        box_btn = Gtk.Box(spacing=6)
        self.btn_fav_save = Gtk.Button(label=self._t("fav_save"))
        self.btn_fav_load = Gtk.Button(label=self._t("fav_load"))
        self.btn_fav_run = Gtk.Button(label=self._t("fav_run"))
        self.btn_fav_del = Gtk.Button(label=self._t("fav_delete"))
        for b in (self.btn_fav_save, self.btn_fav_load, self.btn_fav_run, self.btn_fav_del):
            box_btn.append(b)

        # Fav list dropdown
        self.fav_list = Gtk.StringList.new([f["name"] for f in self.settings.favorites if f.get("mode") == mode])
        self.dd_fav = Gtk.DropDown(model=self.fav_list, enable_search=True)
        self.dd_fav.set_hexpand(True)

        row2 = Adw.ActionRow()
        row2.add_suffix(self.dd_fav)
        row2.add_suffix(box_btn)
        grp.add(row2)

        # callbacks (use lambda capture of mode)
        self.btn_fav_save.connect("clicked", lambda *_: self._on_fav_save(mode))
        self.btn_fav_load.connect("clicked", lambda *_: self._on_fav_load(mode))
        self.btn_fav_run.connect("clicked", lambda *_: self._on_fav_run(mode))
        self.btn_fav_del.connect("clicked", lambda *_: self._on_fav_delete(mode))
        return grp

    # ------------- Flatpak list loading
    def _refresh_flatpak_list_async(self):
        def work(_task, _src, _data, _cancellable):
            return list_flatpaks()

        def done(_obj, res, _data):
            try:
                rows = res.propagate_value()
            except Exception:
                rows = []
            self._flatpaks = rows
            self.flatpak_string_list.splice(0, self.flatpak_string_list.get_n_items(), [])
            self._flatpak_ids = []
            for appid, title in rows:
                self.flatpak_string_list.append(f"{title}  ⟂  {appid}")
                self._flatpak_ids.append(appid)
            # restore last selected
            if self.settings.last_flatpak and self._flatpak_ids:
                try:
                    idx = self._flatpak_ids.index(self.settings.last_flatpak)
                    self.dd_flatpak.set_selected(idx)
                except ValueError:
                    pass

        GLib.Task.new(None, None, done).run_in_thread(work, None)

    # ------------- Env builder
    def _build_env(self) -> dict[str, str]:
        env: dict[str, str] = {}
        # read current UI
        mult = int(["2","3","4","6","8"][self.row_mult.get_selected()])
        flow = int(self.row_flow.get_value())
        perf = self.row_perf.get_active()
        hdr  = self.row_hdr.get_active()
        present = self.row_present.get_text().strip()
        lsfg_proc = self.row_lsfg_proc.get_text().strip()
        extra_layers = self.row_extra_layers.get_text().strip()
        mangohud = self.row_mangohud.get_active()

        env["LSFG_MULTIPLIER"] = str(mult)
        env["LSFG_FLOW_SCALE"] = str(flow)
        env["LSFG_PERFORMANCE_MODE"] = "1" if perf else "0"
        env["LSFG_HDR_MODE"] = "1" if hdr else "0"
        if present:
            env["LSFG_PRESENT_MODE"] = present
        if lsfg_proc:
            env["LSFG_PROCESS"] = lsfg_proc

        layers = ["lsfg_vk"]
        if mangohud:
            layers.append("VK_LAYER_MANGOHUD_overlay")
            env["MANGOHUD"] = "1"
        if extra_layers:
            layers.extend([tok for tok in extra_layers.split(":") if tok])

        env["VK_INSTANCE_LAYERS"] = ":".join(layers)
        return env

    # ------------- Helpers for command construction
    @staticmethod
    def _env_to_flatpak_args(env: dict[str, str]) -> list[str]:
        args: list[str] = []
        for k, v in env.items():
            args += ["--env", f"{k}={v}"]
        return args

    @staticmethod
    def _env_prefix_shell(env: dict[str, str]) -> str:
        return " ".join(f"{k}={shlex.quote(v)}" for k, v in env.items())

    # ------------- Dialog helpers
    def _message(self, title: str, body: str):
        dlg = Adw.MessageDialog.new(self, title, body)
        dlg.add_response("ok", self._t("ok"))
        dlg.set_close_response("ok")
        dlg.present()

    # ------------- Flatpak actions
    def _on_preview_flatpak(self, _btn):
        if not host_has_flatpak():
            self._message(self._t("error"), self._t("no_flatpak_cli"))
            return
        idx = int(self.dd_flatpak.get_selected())
        if idx < 0 or idx >= len(self._flatpak_ids):
            self._message(self._t("error"), self._t("no_selection"))
            return
        appid = self._flatpak_ids[idx]
        env = self._build_env()
        extra = shlex.split(self.row_flatpak_args.get_text().strip()) if self.row_flatpak_args.get_text() else []
        cmd = ["flatpak-spawn","--host","flatpak","run"] + self._env_to_flatpak_args(env) + [appid] + extra
        self._message("Preview", " ".join(shlex.quote(x) for x in cmd))

    def _on_check_flatpak(self, _btn):
        if not host_has_flatpak():
            self._message(self._t("error"), self._t("no_flatpak_cli"))
            return
        idx = int(self.dd_flatpak.get_selected())
        if idx < 0 or idx >= len(self._flatpak_ids):
            self._message(self._t("error"), self._t("no_selection"))
            return
        appid = self._flatpak_ids[idx]
        env = self._build_env()
        extra = ""  # we just check
        env_args = self._env_to_flatpak_args(env)
        # Run a shell inside the app sandbox to inspect env and layers
        shell = (
            "set -e; "
            "echo '=== ENV (partial) ==='; "
            "env | grep -E '^(LSFG_|MANGOHUD=|VK_INSTANCE_LAYERS=)'; "
            "echo; echo '=== Layer JSON search ==='; "
            "for d in /usr/share/vulkan/explicit_layer.d /app/share/vulkan/explicit_layer.d; do "
            "  test -d \"$d\" && grep -l -i lsfg \"$d\"/*.json 2>/dev/null || true; "
            "done; "
            "echo; echo 'OK'; "
        )
        cmd = ["flatpak-spawn","--host","flatpak","run"] + env_args + ["--command=sh", appid, "-lc", shell]
        code, out, err = run_host(cmd[2:])  # skip first two since run_host re-adds --host
        self._message(self._t("injection_result"), (out or "") + ("\n" + err if err else ""))

    def _on_launch_flatpak(self, _btn):
        if not host_has_flatpak():
            self._message(self._t("error"), self._t("no_flatpak_cli"))
            return
        idx = int(self.dd_flatpak.get_selected())
        if idx < 0 or idx >= len(self._flatpak_ids):
            self._message(self._t("error"), self._t("no_selection"))
            return
        appid = self._flatpak_ids[idx]
        self.settings.last_flatpak = appid
        save_settings(self.settings)

        env = self._build_env()
        extra = shlex.split(self.row_flatpak_args.get_text().strip()) if self.row_flatpak_args.get_text() else []
        cmd = ["flatpak-spawn","--host","flatpak","run"] + self._env_to_flatpak_args(env) + [appid] + extra
        # detach
        subprocess.Popen(cmd)

    # ------------- Host actions
    def _on_preview_host(self, _btn):
        target = self.row_host_cmd.get_text().strip()
        if not target:
            self._message(self._t("error"), self._t("host_cmd_placeholder"))
            return
        env = self._build_env()
        extra = shlex.split(self.row_host_args.get_text().strip()) if self.row_host_args.get_text() else []
        env_prefix = self._env_prefix_shell(env)
        shell = f"{env_prefix} {shlex.quote(target)} {' '.join(shlex.quote(x) for x in extra)}"
        cmd = ["flatpak-spawn","--host","sh","-lc", shell]
        self._message("Preview", " ".join(shlex.quote(x) for x in cmd))

    def _on_check_host(self, _btn):
        target = self.row_host_cmd.get_text().strip()
        if not target:
            self._message(self._t("error"), self._t("host_cmd_placeholder"))
            return
        env = self._build_env()
        env_prefix = self._env_prefix_shell(env)
        shell = (
            f"{env_prefix} env | grep -E '^(LSFG_|MANGOHUD=|VK_INSTANCE_LAYERS=)'; "
            "echo; echo '=== Layer JSON on host ==='; "
            "for d in /usr/share/vulkan/explicit_layer.d /etc/vulkan/explicit_layer.d; do "
            "  test -d \"$d\" && grep -l -i lsfg \"$d\"/*.json 2>/dev/null || true; "
            "done; echo OK;"
        )
        code, out, err = run_host(["sh","-lc", shell])
        self._message(self._t("injection_result"), (out or "") + ("\n" + err if err else ""))

    def _on_launch_host(self, _btn):
        target = self.row_host_cmd.get_text().strip()
        if not target:
            self._message(self._t("error"), self._t("host_cmd_placeholder"))
            return
        self.settings.last_host_cmd = target
        save_settings(self.settings)

        env = self._build_env()
        extra = shlex.split(self.row_host_args.get_text().strip()) if self.row_host_args.get_text() else []
        env_prefix = self._env_prefix_shell(env)
        shell = f"{env_prefix} exec {shlex.quote(target)} {' '.join(shlex.quote(x) for x in extra)}"
        subprocess.Popen(["flatpak-spawn","--host","sh","-lc", shell])

    # ------------- Favorites (save/load/run/delete)
    def _collect_options_snapshot(self) -> dict:
        return {
            "multiplier": int(["2","3","4","6","8"][self.row_mult.get_selected()]),
            "flow_scale": int(self.row_flow.get_value()),
            "performance": self.row_perf.get_active(),
            "hdr": self.row_hdr.get_active(),
            "present_mode": self.row_present.get_text().strip(),
            "lsfg_process": self.row_lsfg_proc.get_text().strip(),
            "extra_layers": self.row_extra_layers.get_text().strip(),
            "mangohud": self.row_mangohud.get_active(),
            "extra_args": "",  # page-specific args handled separately
        }

    def _apply_options_snapshot(self, snap: dict):
        mults = ["2","3","4","6","8"]
        try:
            self.row_mult.set_selected(mults.index(str(snap.get("multiplier", 2))))
        except ValueError:
            self.row_mult.set_selected(0)
        self.row_flow.set_value(float(snap.get("flow_scale", 0)))
        self.row_perf.set_active(bool(snap.get("performance", False)))
        self.row_hdr.set_active(bool(snap.get("hdr", False)))
        self.row_present.set_text(str(snap.get("present_mode", "")))
        self.row_lsfg_proc.set_text(str(snap.get("lsfg_process", "")))
        self.row_extra_layers.set_text(str(snap.get("extra_layers", "")))
        self.row_mangohud.set_active(bool(snap.get("mangohud", False)))

    def _on_fav_save(self, mode: str):
        name = self.fav_name_entry.get_text().strip() or "Preset"
        entry: dict = {"name": name, "mode": mode, "target": "", "options": self._collect_options_snapshot()}
        if mode == "flatpak":
            idx = int(self.dd_flatpak.get_selected())
            entry["target"] = self._flatpak_ids[idx] if (0 <= idx < len(self._flatpak_ids)) else ""
            entry["options"]["extra_args"] = self.row_flatpak_args.get_text().strip()
        else:
            entry["target"] = self.row_host_cmd.get_text().strip()
            entry["options"]["extra_args"] = self.row_host_args.get_text().strip()

        # overwrite if name+mode exists
        replaced = False
        for i, f in enumerate(self.settings.favorites):
            if f.get("name")==name and f.get("mode")==mode:
                self.settings.favorites[i] = entry
                replaced = True
                break
        if not replaced:
            self.settings.favorites.append(entry)
            self.fav_list.append(name)

        save_settings(self.settings)
        self._message("OK", tr(self.settings.lang, "fav_exists") if replaced else tr(self.settings.lang, "fav_saved"))

    def _selected_fav_entry(self, mode: str) -> dict | None:
        idx = int(self.dd_fav.get_selected())
        if idx < 0:
            return None
        # filter by mode
        names = [f["name"] for f in self.settings.favorites if f.get("mode")==mode]
        if idx >= len(names):
            return None
        name = names[idx]
        for f in self.settings.favorites:
            if f.get("mode")==mode and f.get("name")==name:
                return f
        return None

    def _on_fav_load(self, mode: str):
        fav = self._selected_fav_entry(mode)
        if not fav:
            return
        self._apply_options_snapshot(fav.get("options", {}))
        if mode == "flatpak":
            target = fav.get("target","")
            if target and target in self._flatpak_ids:
                self.dd_flatpak.set_selected(self._flatpak_ids.index(target))
            self.row_flatpak_args.set_text(fav.get("options",{}).get("extra_args",""))
        else:
            self.row_host_cmd.set_text(fav.get("target",""))
            self.row_host_args.set_text(fav.get("options",{}).get("extra_args",""))

    def _on_fav_run(self, mode: str):
        self._on_fav_load(mode)
        if mode == "flatpak":
            self._on_launch_flatpak(None)
        else:
            self._on_launch_host(None)

    def _on_fav_delete(self, mode: str):
        fav = self._selected_fav_entry(mode)
        if not fav:
            return
        name = fav["name"]
        self.settings.favorites = [f for f in self.settings.favorites if not (f.get("mode")==mode and f.get("name")==name)]
        save_settings(self.settings)
        # rebuild dropdown model
        new_names = [f["name"] for f in self.settings.favorites if f.get("mode")==mode]
        self.fav_list.splice(0, self.fav_list.get_n_items(), [])
        for n in new_names:
            self.fav_list.append(n)

# ---------------- Application ----------------

class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        Adw.init()

        # Actions for menu
        self._add_action("lang_en", lambda *_: self._set_lang("en"))
        self._add_action("lang_fr", lambda *_: self._set_lang("fr"))
        self._add_action("open_config", self._open_config)
        self._add_action("export_settings", self._export_settings)
        self._add_action("import_settings", self._import_settings)
        self._add_action("reset_settings", self._reset_settings)
        self._add_action("link_lsfg", lambda *_: self._open_url("https://github.com/PancakeTAS/lsfg-vk"))
        self._add_action("link_mangohud", lambda *_: self._open_url("https://github.com/flightlessmango/MangoHud"))
        self._add_action("link_goverlay", lambda *_: self._open_url("https://github.com/benjamimgois/goverlay"))

        self.settings = load_settings()
        self.win: MainWindow | None = None

    def _add_action(self, name: str, cb):
        act = Gio.SimpleAction.new(name, None)
        act.connect("activate", cb)
        self.add_action(act)

    def _set_lang(self, lang: str):
        self.settings.lang = lang
        save_settings(self.settings)
        # Rebuild window with new language (simple approach)
        if self.win:
            self.win.destroy()
        self.do_activate()

    def _open_config(self, *_):
        Gio.AppInfo.launch_default_for_uri(f"file://{CONFIG_DIR}", None)

    def _export_settings(self, *_):
        try:
            out = CONFIG_DIR / "settings.export.json"
            out.write_text(json.dumps(asdict(self.settings), indent=2, ensure_ascii=False), encoding="utf-8")
            self._info(tr(self.settings.lang, "export_done") + f"\n{out}")
        except Exception as e:
            self._error(str(e))

    def _import_settings(self, *_):
        try:
            imp = CONFIG_DIR / "settings.export.json"
            data = json.loads(imp.read_text(encoding="utf-8"))
            self.settings = Settings(
                lang=data.get("lang","fr"),
                last_flatpak=data.get("last_flatpak",""),
                last_host_cmd=data.get("last_host_cmd",""),
                favorites=data.get("favorites",[]),
                options=Options(**data.get("options",{})),
            )
            save_settings(self.settings)
            self._info(tr(self.settings.lang, "import_done"))
            # Re-open window to refresh UI
            if self.win:
                self.win.destroy()
            self.do_activate()
        except Exception as e:
            self._error(str(e))

    def _reset_settings(self, *_):
        try:
            if CONFIG_FILE.exists():
                CONFIG_FILE.unlink()
            self.settings = Settings()
            save_settings(self.settings)
            self._info(tr(self.settings.lang, "reset_done"))
            if self.win:
                self.win.destroy()
            self.do_activate()
        except Exception as e:
            self._error(str(e))

    def _open_url(self, url: str):
        Gio.AppInfo.launch_default_for_uri(url, None)

    def _info(self, text: str):
        dlg = Adw.MessageDialog.new(self.get_active_window(), "Info", text)
        dlg.add_response("ok", tr(self.settings.lang, "ok"))
        dlg.set_close_response("ok")
        dlg.present()

    def _error(self, text: str):
        dlg = Adw.MessageDialog.new(self.get_active_window(), tr(self.settings.lang,"error"), text)
        dlg.add_response("ok", tr(self.settings.lang, "ok"))
        dlg.set_close_response("ok")
        dlg.present()

    # ---- Application Lifecycle
    def do_activate(self):
        if not self.win:
            self.win = MainWindow(self, self.settings)
        self.win.present()

def main():
    app = App()
    app.run([])

if __name__ == "__main__":
    main()
