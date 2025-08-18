#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT

import os, sys, json, shlex, subprocess
from dataclasses import dataclass, asdict, field
from typing import List, Tuple

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GLib

APP_ID = "io.reaven.LSFGVKLauncher"

# -------------------- util --------------------

def run_host(args: List[str]) -> Tuple[int, str, str]:
    """Exécute une commande sur l’hôte via flatpak-spawn --host."""
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

def info_button(text: str, on_click):
    btn = Gtk.Button.new_from_icon_name("dialog-information-symbolic")
    btn.set_valign(Gtk.Align.CENTER)
    btn.set_tooltip_text(text)
    btn.connect("clicked", on_click, text)
    return btn

def show_dialog(parent: Gtk.Widget, title: str, body: str):
    dlg = Adw.MessageDialog.new(parent.get_root(), title, body)
    dlg.add_response("ok", "OK")
    dlg.set_close_response("ok")
    dlg.present()

# -------------------- persistence --------------------

def cfg_file() -> str:
    base = os.path.join(GLib.get_user_config_dir(), APP_ID)
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "settings.json")

def load_json(default: dict) -> dict:
    try:
        with open(cfg_file(), "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                d = default.copy()
                # merge shallow seulement sur les clés connues
                for k in d:
                    if k in data: d[k] = data[k]
                return d
    except Exception:
        pass
    return default

def save_json(data: dict) -> None:
    try:
        with open(cfg_file(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

# -------------------- modèle --------------------

@dataclass
class LSFGShared:
    multiplier: str = "2"            # 2/3/4/6/8
    flow_scale: bool = False
    performance: bool = False        # LSFG_PERFORMANCE_MODE
    hdr: bool = False                # LSFG_HDR_MODE
    present_mode: str = "auto"       # auto/fifo/mailbox/immediate
    lsfg_process: str = ""           # optionnel

@dataclass
class SessionState:
    shared: LSFGShared = field(default_factory=LSFGShared)
    flatpak_app: str = ""
    flatpak_args: str = ""
    host_cmd: str = ""
    host_args: str = ""

    @staticmethod
    def load() -> "SessionState":
        d = asdict(SessionState())       # default
        stored = load_json(d)
        shared = LSFGShared(**stored.get("shared", {}))
        return SessionState(shared=shared,
                            flatpak_app=stored.get("flatpak_app", ""),
                            flatpak_args=stored.get("flatpak_args", ""),
                            host_cmd=stored.get("host_cmd", ""),
                            host_args=stored.get("host_args", ""))

    def save(self):
        save_json(asdict(self))

# -------------------- bloc d’options réutilisable --------------------

class OptionControls:
    def __init__(self):
        self.box = Adw.PreferencesGroup(title="LSFG-vk options")

        # Multiplier
        self._mult = "2"
        row_mult = Adw.ActionRow(title="Multiplier (X)")
        mult_box = Gtk.Box(spacing=6)
        self._mult_buttons: List[Gtk.ToggleButton] = []
        for label in ["2","3","4","6","8"]:
            b = Gtk.ToggleButton(label=label)
            b.connect("toggled", self._on_mult_toggled, label)
            self._mult_buttons.append(b)
            mult_box.append(b)
        self._mult_buttons[0].set_active(True)
        row_mult.add_suffix(mult_box)
        row_mult.add_suffix(info_button(
            "LSFG_MULTIPLIER — facteur d’interpolation (2/3/4/6/8).",
            self._on_info))

        # Flow scale
        self.row_flow = Adw.SwitchRow(title="Flow Scale")
        self.row_flow.add_suffix(info_button(
            "LSFG_FLOW_SCALE — recalage/échelle des flux optiques.",
            self._on_info))

        # Performance
        self.row_perf = Adw.SwitchRow(title="Performance mode")
        self.row_perf.add_suffix(info_button(
            "LSFG_PERFORMANCE_MODE — favorise la performance.",
            self._on_info))

        # HDR
        self.row_hdr = Adw.SwitchRow(title="HDR")
        self.row_hdr.add_suffix(info_button(
            "LSFG_HDR_MODE — force/annonce le HDR si supporté.",
            self._on_info))

        # Present mode
        pm_model = Gtk.StringList.new(["auto","fifo","mailbox","immediate"])
        self.row_present = Adw.ComboRow(title="Present mode", model=pm_model)
        self.row_present.set_selected(0)
        self.row_present.add_suffix(info_button(
            "LSFG_PRESENT_MODE — mode de présentation Vulkan.",
            self._on_info))

        # LSFG_PROCESS
        self.row_process = Adw.EntryRow(title="LSFG_PROCESS (optional)")
        self.row_process.add_suffix(info_button(
            "Limiter au nom du processus cible (laisser vide = global).",
            self._on_info))

        self.box.add(row_mult)
        self.box.add(self.row_flow)
        self.box.add(self.row_perf)
        self.box.add(self.row_hdr)
        self.box.add(self.row_present)
        self.box.add(self.row_process)

    def _on_mult_toggled(self, btn: Gtk.ToggleButton, label: str):
        if not btn.get_active():
            return
        self._mult = label
        for b in self._mult_buttons:
            if b is not btn and b.get_active():
                b.set_active(False)

    def _on_info(self, _btn, text: str):
        show_dialog(self.box, "Information", text)

    def to_shared(self) -> LSFGShared:
        model = self.row_present.get_model()
        idx = self.row_present.get_selected()
        present = model.get_string(idx) if 0 <= idx < model.get_n_items() else "auto"
        return LSFGShared(
            multiplier=self._mult,
            flow_scale=self.row_flow.get_active(),
            performance=self.row_perf.get_active(),
            hdr=self.row_hdr.get_active(),
            present_mode=present,
            lsfg_process=self.row_process.get_text().strip()
        )

    def set_from_shared(self, s: LSFGShared):
        for b in self._mult_buttons:
            b.set_active(b.get_label() == s.multiplier)
        self._mult = s.multiplier
        self.row_flow.set_active(bool(s.flow_scale))
        self.row_perf.set_active(bool(s.performance))
        self.row_hdr.set_active(bool(s.hdr))

        model = self.row_present.get_model()
        sel = 0
        for i in range(model.get_n_items()):
            if model.get_string(i) == (s.present_mode or "auto"):
                sel = i; break
        self.row_present.set_selected(sel)
        self.row_process.set_text(s.lsfg_process or "")

# -------------------- fenêtre principale --------------------

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application):
        super().__init__(application=app)
        self.set_default_size(920, 640)
        self.set_title("LSFG-VK Launcher")

        self.state = SessionState.load()

        self.stack = Adw.ViewStack()

        # pages
        self.page_flatpak = self._build_flatpak_page()
        self.page_host    = self._build_host_page()
        self.page_help    = self._build_help_page()

        self.stack.add_titled(self.page_flatpak, "flatpak", "Flatpak")
        self.stack.add_titled(self.page_host,    "host",    "Host")
        self.stack.add_titled(self.page_help,    "help",    "Help")

        # chrome
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        switch_title = Adw.ViewSwitcherTitle()
        # éviter les méthodes dépréciées
        switch_title.props.stack = self.stack
        header.set_title_widget(switch_title)
        toolbar.add_top_bar(header)

        switch_bar = Adw.ViewSwitcherBar()
        switch_bar.props.stack = self.stack
        toolbar.add_bottom_bar(switch_bar)

        # bas : preview + boutons
        bottom = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                         margin_top=8, margin_bottom=8, margin_start=12, margin_end=12)
        btns = Gtk.Box(spacing=8)
        self.btn_prev = Gtk.Button(label="Preview")
        self.btn_run  = Gtk.Button(label="Launch")
        self.btn_prev.connect("clicked", self.on_preview)
        self.btn_run.connect("clicked", self.on_launch)
        btns.append(self.btn_prev); btns.append(self.btn_run)

        self.preview = Gtk.TextView(editable=False, wrap_mode=Gtk.WrapMode.CHAR)
        try: self.preview.set_monospace(True)
        except Exception: pass
        self.preview.set_size_request(-1, 110)

        bottom.append(btns)
        sc = Gtk.ScrolledWindow()
        sc.set_child(self.preview)
        bottom.append(sc)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root.append(self.stack)
        root.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        root.append(bottom)
        toolbar.set_content(root)
        self.set_content(toolbar)

        GLib.idle_add(self._reload_flatpak_list)

    # ---------- Flatpak ----------
    def _build_flatpak_page(self) -> Adw.PreferencesPage:
        page = Adw.PreferencesPage()

        self.flatpak_model = Gtk.StringList.new([])
        self.flatpak_combo = Adw.ComboRow(title="Application", subtitle="Choisir un Flatpak installé",
                                          model=self.flatpak_model)
        try: self.flatpak_combo.set_use_subtitle(True)
        except Exception: pass

        # icône (nom d’icône = app-id si dispo)
        self.flatpak_icon = Gtk.Image.new_from_icon_name("application-x-executable-symbolic")
        self.flatpak_icon.set_pixel_size(24)
        self.flatpak_combo.add_suffix(self.flatpak_icon)

        btn_refresh = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        btn_refresh.set_tooltip_text("Rafraîchir")
        btn_refresh.connect("clicked", lambda *_: self._reload_flatpak_list())
        self.flatpak_combo.add_suffix(btn_refresh)
        self.flatpak_combo.connect("notify::selected", self._on_flatpak_selected)

        self.flatpak_args = Adw.EntryRow(title="Arguments supplémentaires",
                                         text=self.state.flatpak_args or "")
        self.flatpak_args.add_suffix(info_button(
            "Arguments passés à l’app (ex: --fullscreen).",
            lambda b, t: show_dialog(self, "Information", t)
        ))

        self.ctrl_flatpak = OptionControls()
        self.ctrl_flatpak.set_from_shared(self.state.shared)

        hint = Adw.ActionRow(title="Note",
                             subtitle="Cible Vulkan (ou OpenGL via Zink) pour que lsfg-vk s’applique.")

        grp = Adw.PreferencesGroup(title="Cible Flatpak")
        grp.add(self.flatpak_combo)
        grp.add(self.flatpak_args)
        grp.add(hint)

        page.add(grp)
        page.add(self.ctrl_flatpak.box)
        return page

    def _reload_flatpak_list(self):
        apps = list_flatpaks()
        self.flatpak_model.splice(0, self.flatpak_model.get_n_items(), apps)
        if self.state.flatpak_app and self.state.flatpak_app in apps:
            self.flatpak_combo.set_selected(apps.index(self.state.flatpak_app))
        elif apps:
            self.flatpak_combo.set_selected(0)
        self._update_flatpak_icon()

    def _on_flatpak_selected(self, *_):
        self._update_flatpak_icon()
        idx = self.flatpak_combo.get_selected()
        if 0 <= idx < self.flatpak_model.get_n_items():
            self.state.flatpak_app = self.flatpak_model.get_string(idx)
            self.state.save()

    def _update_flatpak_icon(self):
        idx = self.flatpak_combo.get_selected()
        name = ""
        if 0 <= idx < self.flatpak_model.get_n_items():
            name = self.flatpak_model.get_string(idx)
        self.flatpak_icon.set_from_icon_name(name or "application-x-executable-symbolic")

    # ---------- Host ----------
    def _build_host_page(self) -> Adw.PreferencesPage:
        page = Adw.PreferencesPage()

        self.host_cmd = Adw.EntryRow(title="Exécutable (host)", text=self.state.host_cmd or "")
        self.host_cmd.add_suffix(info_button(
            "Nom/chemin d’un binaire système (vlc, mpv, retroarch, /usr/bin/…).",
            lambda b, t: show_dialog(self, "Information", t)
        ))

        self.host_args = Adw.EntryRow(title="Arguments supplémentaires",
                                      text=self.state.host_args or "")
        self.host_args.add_suffix(info_button(
            "Arguments passés au binaire système.",
            lambda b, t: show_dialog(self, "Information", t)
        ))

        self.ctrl_host = OptionControls()
        self.ctrl_host.set_from_shared(self.state.shared)

        grp = Adw.PreferencesGroup(title="Cible système (host)")
        grp.add(self.host_cmd)
        grp.add(self.host_args)

        page.add(grp)
        page.add(self.ctrl_host.box)
        return page

    # ---------- build & run ----------
    def _collect_shared(self) -> LSFGShared:
        # On lit depuis le bloc Flatpak (Host est synchronisé après Preview/Launch)
        return self.ctrl_flatpak.to_shared()

    def _sync_controls(self, s: LSFGShared):
        self.ctrl_flatpak.set_from_shared(s)
        self.ctrl_host.set_from_shared(s)

    def _env_kv(self, s: LSFGShared) -> List[str]:
        """Retourne une liste de 'KEY=VAL' pour env."""
        env = [
            f"LSFG_MULTIPLIER={s.multiplier}",
            f"LSFG_FLOW_SCALE={'1' if s.flow_scale else '0'}",
            f"LSFG_PERFORMANCE_MODE={'1' if s.performance else '0'}",
            f"LSFG_HDR_MODE={'1' if s.hdr else '0'}",
            "VK_INSTANCE_LAYERS=lsfg_vk",
        ]
        if s.present_mode and s.present_mode != "auto":
            env.append(f"LSFG_PRESENT_MODE={s.present_mode}")
        if s.lsfg_process:
            env.append(f"LSFG_PROCESS={s.lsfg_process}")
        return env

    def _cmd_flatpak(self) -> List[str]:
        s = self._collect_shared()
        self._sync_controls(s)
        self.state.shared = s

        # args utilisateur
        self.state.flatpak_args = self.flatpak_args.get_text().strip()

        idx = self.flatpak_combo.get_selected()
        if idx < 0 or idx >= self.flatpak_model.get_n_items():
            raise RuntimeError("Choisis une application Flatpak.")
        appid = self.flatpak_model.get_string(idx)
        self.state.flatpak_app = appid

        env = self._env_kv(s)
        args = shlex.split(self.state.flatpak_args) if self.state.flatpak_args else []

        # IMPORTANT : on passe par le host pour 'flatpak run' et on utilise --env=
        cmd = ["flatpak-spawn", "--host", "flatpak", "run"]
        for kv in env:
            cmd.append(f"--env={kv}")
        cmd.append(appid)
        cmd += args
        return cmd

    def _cmd_host(self) -> List[str]:
        s = self._collect_shared()
        self._sync_controls(s)
        self.state.shared = s

        self.state.host_cmd  = self.host_cmd.get_text().strip()
        self.state.host_args = self.host_args.get_text().strip()
        if not self.state.host_cmd:
            raise RuntimeError("Renseigne un exécutable système (ex: vlc).")

        env = self._env_kv(s)
        args = shlex.split(self.state.host_args) if self.state.host_args else []
        # On exécute le binaire côté host avec env injecté
        return ["flatpak-spawn", "--host", "env", *env, self.state.host_cmd, *args]

    def on_preview(self, *_):
        try:
            if self.stack.get_visible_child_name() == "host":
                cmd = self._cmd_host()
            else:
                cmd = self._cmd_flatpak()
            self.state.save()
            txt = join_shell(cmd)
        except Exception as e:
            txt = f"# ERROR: {e}"
        self.preview.get_buffer().set_text(txt)

    def on_launch(self, *_):
        try:
            if self.stack.get_visible_child_name() == "host":
                cmd = self._cmd_host()
            else:
                cmd = self._cmd_flatpak()
            self.state.save()
        except Exception as e:
            show_dialog(self, "Build error", str(e))
            self.on_preview()
            return
        try:
            Gio.Subprocess.new(cmd, Gio.SubprocessFlags.NONE)
            self.on_preview()
        except Exception as e:
            show_dialog(self, "Launch failed", str(e))
            self.on_preview()

    # ---------- help ----------
    def _build_help_page(self) -> Adw.PreferencesPage:
        page = Adw.PreferencesPage()
        row1 = Adw.ActionRow(title="Conseil",
                             subtitle="Installe l’extension Flatpak lsfg-vk correspondant au runtime (23.08/24.08).")
        row2 = Adw.ActionRow(title="Dépannage",
                             subtitle="Utilise Preview pour copier la ligne et tester dans un terminal avec VK_LOADER_DEBUG=all.")
        grp = Adw.PreferencesGroup(title="Aide")
        grp.add(row1); grp.add(row2)
        page.add(grp)
        return page

# -------------------- app --------------------

class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self._on_activate)

    def _on_activate(self, *_):
        if self.props.active_window:
            self.props.active_window.present(); return
        MainWindow(self).present()

def main(argv):
    Adw.init()
    app = App()
    return app.run(argv)

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
