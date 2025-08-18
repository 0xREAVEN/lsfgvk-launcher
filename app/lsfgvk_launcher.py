#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os, json, shlex, subprocess
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GLib

APP_ID = "io.reaven.LSFGVKLauncher"

# -------------------- helpers --------------------

def run_host(args: List[str]) -> Tuple[int, str, str]:
    """Run a command on the host via flatpak-spawn --host."""
    cmd = ["flatpak-spawn", "--host"] + args
    try:
        p = subprocess.run(cmd, text=True, capture_output=True, check=False)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def list_flatpaks() -> List[str]:
    code, out, _ = run_host(["flatpak", "list", "--app", "--columns=application"])
    if code != 0:
        return []
    seen, apps = set(), []
    for line in out.splitlines():
        s = line.strip()
        if s and s not in seen:
            apps.append(s); seen.add(s)
    return apps

def join_shell(parts: List[str]) -> str:
    return " ".join(shlex.quote(p) for p in parts)

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

def cfg_path() -> str:
    base = os.path.join(GLib.get_user_config_dir(), APP_ID)
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "settings.json")

def load_json(default: dict) -> dict:
    try:
        with open(cfg_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                d = default.copy()
                d.update({k: v for k, v in data.items() if k in d})
                return d
    except Exception:
        pass
    return default

def save_json(data: dict) -> None:
    try:
        with open(cfg_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

# -------------------- model --------------------

@dataclass
class LSFGShared:
    multiplier: str = "2"        # 2/3/4/6/8
    flow_scale: bool = False
    performance: bool = False
    hdr: bool = False
    present_mode: str = "auto"   # auto/fifo/mailbox/immediate
    lsfg_process: str = ""

@dataclass
class SessionState:
    shared: LSFGShared = LSFGShared()
    flatpak_app: str = ""
    flatpak_args: str = ""
    host_cmd: str = ""
    host_args: str = ""

    @staticmethod
    def defaults() -> "SessionState":
        return SessionState()

    @staticmethod
    def from_store() -> "SessionState":
        d = asdict(SessionState.defaults())
        stored = load_json(d)
        # rebuild objects
        shared = LSFGShared(**stored.get("shared", {}))
        return SessionState(shared=shared,
                            flatpak_app=stored.get("flatpak_app", ""),
                            flatpak_args=stored.get("flatpak_args", ""),
                            host_cmd=stored.get("host_cmd", ""),
                            host_args=stored.get("host_args", ""))

    def save(self):
        save_json(asdict(self))

# -------------------- option controls (duplicated & synced) --------------------

class OptionControls:
    """A block of controls (multiplier+switches+present+process)."""
    def __init__(self):
        self.box = Adw.PreferencesGroup(title="LSFG-vk options")
        # Multiplier
        self._mult = "2"
        row_mult = Adw.ActionRow(title="Multiplier (X)")
        mult_box = Gtk.Box(spacing=6)
        self._mult_buttons: List[Gtk.ToggleButton] = []
        for label in ["2", "3", "4", "6", "8"]:
            b = Gtk.ToggleButton(label=label)
            b.connect("toggled", self._on_mult_toggled, label)
            self._mult_buttons.append(b)
            mult_box.append(b)
        self._mult_buttons[0].set_active(True)
        row_mult.add_suffix(mult_box)
        row_mult.add_suffix(info_button(
            "LSFG_MULTIPLIER — facteur d’interpolation (X2, X3, X4, X6, X8).",
            self._on_info))

        # Switches
        self.row_flow = Adw.SwitchRow(title="Flow Scale")
        self.row_flow.add_suffix(info_button(
            "LSFG_FLOW_SCALE — active la variation adaptative du flux.",
            self._on_info))
        self.row_perf = Adw.SwitchRow(title="Performance mode")
        self.row_perf.add_suffix(info_button(
            "LSFG_PERFORMANCE — privilégie la performance au détriment de la qualité.",
            self._on_info))
        self.row_hdr = Adw.SwitchRow(title="HDR")
        self.row_hdr.add_suffix(info_button(
            "LSFG_HDR — signale un rendu HDR au backend Vulkan.",
            self._on_info))

        # Present mode
        pm_model = Gtk.StringList.new(["auto", "fifo", "mailbox", "immediate"])
        self.row_present = Adw.ComboRow(title="Present mode", model=pm_model)
        self.row_present.set_selected(0)
        self.row_present.add_suffix(info_button(
            "LSFG_PRESENT_MODE — mode de présentation Vulkan (auto/fifo/mailbox/immediate).",
            self._on_info))

        # Process
        self.row_process = Adw.EntryRow(title="LSFG_PROCESS (optional)")
        self.row_process.add_suffix(info_button(
            "LSFG_PROCESS — filtre sur le nom du processus cible (laisser vide pour tous).",
            self._on_info))

        # Extra row (added by caller if besoin)
        self.box.add(row_mult)
        self.box.add(self.row_flow)
        self.box.add(self.row_perf)
        self.box.add(self.row_hdr)
        self.box.add(self.row_present)
        self.box.add(self.row_process)

    # internal
    def _on_mult_toggled(self, btn: Gtk.ToggleButton, label: str):
        if not btn.get_active():
            return
        self._mult = label
        for b in self._mult_buttons:
            if b is not btn and b.get_active():
                b.set_active(False)

    def _on_info(self, _btn, text: str):
        # parent window
        root = self.box.get_root()
        show_dialog(root, "Information", text)

    # external API
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
        # avoid signals loops by blocking notify where applicable
        for b in self._mult_buttons:
            b.set_active(b.get_label() == s.multiplier)
        self._mult = s.multiplier
        self.row_flow.set_active(bool(s.flow_scale))
        self.row_perf.set_active(bool(s.performance))
        self.row_hdr.set_active(bool(s.hdr))
        # select present
        model = self.row_present.get_model()
        found = 0
        for i in range(model.get_n_items()):
            if model.get_string(i) == (s.present_mode or "auto"):
                found = i; break
        self.row_present.set_selected(found)
        self.row_process.set_text(s.lsfg_process or "")

# -------------------- main window --------------------

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application):
        super().__init__(application=app)
        self.set_default_size(920, 640)
        self.set_title("LSFG-VK Launcher")

        self.state = SessionState.from_store()
        self._sync_guard = False  # prevent recursive sync

        self.stack = Adw.ViewStack()

        # build pages
        self.page_flatpak = self._build_flatpak_page()
        self.page_host    = self._build_host_page()
        self.page_help    = self._build_help_page()

        self.stack.add_titled(self.page_flatpak, "flatpak", "Flatpak")
        self.stack.add_titled(self.page_host,    "host",    "Host")
        self.stack.add_titled(self.page_help,    "help",    "Help")

        # Toolbar + view switchers (haut & bas)
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        switch_title = Adw.ViewSwitcherTitle()
        switch_title.set_stack(self.stack)
        switch_title.set_title("LSFG-VK Launcher")
        header.set_title_widget(switch_title)
        toolbar.add_top_bar(header)

        switch_bar = Adw.ViewSwitcherBar()
        switch_bar.set_stack(self.stack)
        toolbar.add_bottom_bar(switch_bar)

        # zone Preview/Launch
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                             margin_top=8, margin_bottom=8, margin_start=12, margin_end=12)
        btn_box = Gtk.Box(spacing=8)
        self.btn_preview = Gtk.Button(label="Preview")
        self.btn_launch  = Gtk.Button(label="Launch")
        self.btn_preview.connect("clicked", self.on_preview)
        self.btn_launch.connect("clicked", self.on_launch)
        btn_box.append(self.btn_preview); btn_box.append(self.btn_launch)

        self.preview = Gtk.TextView(editable=False, wrap_mode=Gtk.WrapMode.CHAR)
        try: self.preview.set_monospace(True)
        except Exception: pass
        self.preview.get_buffer().set_text("")
        self.preview.set_size_request(-1, 110)

        bottom_box.append(btn_box)
        bottom_box.append(self.preview)

        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root_box.append(self.stack)
        root_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        root_box.append(bottom_box)
        toolbar.set_content(root_box)
        self.set_content(toolbar)

        GLib.idle_add(self._reload_flatpak_list)

    # -------------- Flatpak page --------------

    def _build_flatpak_page(self) -> Adw.PreferencesPage:
        page = Adw.PreferencesPage()

        # selector with icon preview
        self.flatpak_model = Gtk.StringList.new([])
        self.flatpak_combo = Adw.ComboRow(title="Application", subtitle="Choose an installed Flatpak",
                                          model=self.flatpak_model)
        try: self.flatpak_combo.set_use_subtitle(True)
        except Exception: pass

        self.flatpak_icon = Gtk.Image.new_from_icon_name("application-x-executable-symbolic")
        self.flatpak_icon.set_pixel_size(24)
        self.flatpak_combo.add_suffix(self.flatpak_icon)

        btn_refresh = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        btn_refresh.set_tooltip_text("Refresh list")
        btn_refresh.connect("clicked", lambda *_: self._reload_flatpak_list())
        self.flatpak_combo.add_suffix(btn_refresh)

        self.flatpak_combo.connect("notify::selected", self._on_flatpak_selected)

        # per-target args
        self.flatpak_args = Adw.EntryRow(title="Extra arguments", text=self.state.flatpak_args or "")
        self.flatpak_args.add_suffix(info_button(
            "Arguments passés à l’application Flatpak (ex: --fullscreen).",
            lambda b, t: show_dialog(self, "Information", t)
        ))

        # options block (duplicated but synced)
        self.ctrl_flatpak = OptionControls()
        self.ctrl_flatpak.set_from_shared(self.state.shared)

        opt_hint = Adw.ActionRow(title="Hint", subtitle="Ensure the target uses Vulkan (or GL via Zink).")

        # assemble
        group_target = Adw.PreferencesGroup(title="Flatpak target")
        group_target.add(self.flatpak_combo)
        group_target.add(self.flatpak_args)
        group_target.add(opt_hint)

        page.add(group_target)
        page.add(self.ctrl_flatpak.box)

        return page

    def _reload_flatpak_list(self):
        apps = list_flatpaks()
        self.flatpak_model.splice(0, self.flatpak_model.get_n_items(), apps)
        # reselect last used if present
        if self.state.flatpak_app and self.state.flatpak_app in apps:
            idx = apps.index(self.state.flatpak_app)
            self.flatpak_combo.set_selected(idx)
        elif apps:
            self.flatpak_combo.set_selected(0)
        # update icon
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
        # best-effort: try themed icon = app-id, else generic
        if name:
            self.flatpak_icon.set_from_icon_name(name)
        else:
            self.flatpak_icon.set_from_icon_name("application-x-executable-symbolic")

    # -------------- Host page --------------

    def _build_host_page(self) -> Adw.PreferencesPage:
        page = Adw.PreferencesPage()

        self.host_cmd = Adw.EntryRow(title="Command", text=self.state.host_cmd or "")
        self.host_cmd.add_suffix(info_button(
            "Chemin ou nom d’exécutable (ex: vlc, retroarch, /usr/bin/mpv).",
            lambda b, t: show_dialog(self, "Information", t)
        ))
        self.host_args = Adw.EntryRow(title="Extra arguments", text=self.state.host_args or "")
        self.host_args.add_suffix(info_button(
            "Arguments passés au binaire système.",
            lambda b, t: show_dialog(self, "Information", t)
        ))

        btn_browse = Gtk.Button(label="Browse…")
        btn_browse.set_tooltip_text("Pick an executable from host")
        btn_browse.connect("clicked", self._on_browse_host)
        self.host_cmd.add_suffix(btn_browse)

        self.ctrl_host = OptionControls()
        self.ctrl_host.set_from_shared(self.state.shared)

        group_target = Adw.PreferencesGroup(title="Host target (system app)")
        group_target.add(self.host_cmd)
        group_target.add(self.host_args)

        page.add(group_target)
        page.add(self.ctrl_host.box)
        return page

    def _on_browse_host(self, *_):
        dlg = Gtk.FileDialog(title="Choose executable")
        def done(d, res):
            try:
                f = d.open_finish(res)
                if f:
                    self.host_cmd.set_text(f.get_path() or "")
                    self.state.host_cmd = self.host_cmd.get_text().strip()
                    self.state.save()
            except Exception:
                pass
        dlg.open(self, None, done)

    # -------------- Help page --------------

    def _build_help_page(self) -> Adw.PreferencesPage:
        page = Adw.PreferencesPage()
        row1 = Adw.ActionRow(title="Notes",
                             subtitle="lsfg-vk est une couche Vulkan. La cible doit utiliser Vulkan (ou GL→Zink).")
        row2 = Adw.ActionRow(title="Project", subtitle="Open repository on GitHub")
        btn = Gtk.Button.new_from_icon_name("external-link-symbolic")
        btn.set_tooltip_text("Open GitHub")
        btn.connect("clicked", lambda *_: Gio.AppInfo.launch_default_for_uri(
            "https://github.com/0xREAVEN/lsfgvk-launcher", None))
        row2.add_suffix(btn)
        row2.set_activatable(True)
        row2.connect("activated", lambda *_: Gio.AppInfo.launch_default_for_uri(
            "https://github.com/0xREAVEN/lsfgvk-launcher", None))
        grp = Adw.PreferencesGroup(title="Help")
        grp.add(row1); grp.add(row2)
        page.add(grp)
        return page

    # -------------- build + run --------------

    def _collect_shared(self) -> LSFGShared:
        # merge/sync from one control (they should be identical after sync)
        return self.ctrl_flatpak.to_shared()

    def _sync_controls(self, shared: LSFGShared):
        if self._sync_guard:
            return
        self._sync_guard = True
        self.ctrl_flatpak.set_from_shared(shared)
        self.ctrl_host.set_from_shared(shared)
        self._sync_guard = False

    def _env_from_shared(self, s: LSFGShared) -> List[str]:
        env = [
            f"LSFG_MULTIPLIER={s.multiplier}",
            f"LSFG_FLOW_SCALE={'1' if s.flow_scale else '0'}",
            f"LSFG_PERFORMANCE={'1' if s.performance else '0'}",
            f"LSFG_HDR={'1' if s.hdr else '0'}",
        ]
        if s.present_mode and s.present_mode != "auto":
            env.append(f"LSFG_PRESENT_MODE={s.present_mode}")
        if s.lsfg_process:
            env.append(f"LSFG_PROCESS={s.lsfg_process}")

        env.append("VK_INSTANCE_LAYERS=lsfg_vk")
        env.append("VK_LAYER_PATH=/usr/share/vulkan/explicit_layer.d:/etc/vulkan/explicit_layer.d")
        return env

    def _build_command(self) -> List[str]:
        # collect shared from whichever block, then sync both
        shared = self._collect_shared()
        self._sync_controls(shared)

        # keep last-used in store too
        self.state.shared = shared
        self.state.flatpak_args = self.flatpak_args.get_text().strip()
        self.state.host_cmd    = self.host_cmd.get_text().strip()
        self.state.host_args   = self.host_args.get_text().strip()

        env = self._env_from_shared(shared)
        cmd: List[str] = ["flatpak-spawn", "--host", "env"] + env

        visible = self.stack.get_visible_child_name()
        if visible == "flatpak":
            idx = self.flatpak_combo.get_selected()
            if idx < 0 or idx >= self.flatpak_model.get_n_items():
                raise RuntimeError("Select a Flatpak application")
            appid = self.flatpak_model.get_string(idx)
            self.state.flatpak_app = appid
            args = shlex.split(self.flatpak_args.get_text().strip() or "")
            cmd += ["flatpak", "run", appid] + args

        elif visible == "host":
            cmdline = self.host_cmd.get_text().strip()
            if not cmdline:
                raise RuntimeError("Enter a host command")
            args = shlex.split(self.host_args.get_text().strip() or "")
            cmd += [cmdline] + args

        else:
            raise RuntimeError("Select Flatpak or Host")

        return cmd

    # actions
    def on_preview(self, *_):
        try:
            cmd = self._build_command()
            self.state.save()
            txt = join_shell(cmd)
        except Exception as e:
            txt = f"# ERROR: {e}"
        self.preview.get_buffer().set_text(txt)

    def on_launch(self, *_):
        try:
            cmd = self._build_command()
            self.state.save()
        except Exception as e:
            show_dialog(self, "Build error", str(e))
            self.on_preview()
            return
        try:
            # Prefer Gio.Subprocess for GLib <-> introspection stability
            Gio.Subprocess.new(cmd, Gio.SubprocessFlags.NONE)
            self.on_preview()
        except Exception as e:
            show_dialog(self, "Launch failed", str(e))
            self.on_preview()

# -------------------- app --------------------

class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self._on_activate)

    def _on_activate(self, *_):
        if self.props.active_window:
            self.props.active_window.present()
            return
        w = MainWindow(self)
        w.present()

def main(argv):
    Adw.init()
    app = App()
    return app.run(argv)

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
