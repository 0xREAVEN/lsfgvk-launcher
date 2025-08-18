#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import shlex
import subprocess
from dataclasses import dataclass
from typing import List, Tuple, Optional

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GLib


APP_ID = "io.reaven.LSFGVKLauncher"


# ----------------------------- helpers -----------------------------

def run_host_command(args: List[str]) -> Tuple[int, str, str]:
    """
    Run a command on the host using flatpak-spawn --host.
    Return (exit_code, stdout, stderr).
    """
    full = ["flatpak-spawn", "--host"] + args
    try:
        proc = subprocess.run(full, capture_output=True, text=True, check=False)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def list_installed_flatpaks() -> List[str]:
    """
    Returns a list of installed app IDs (on the host) using `flatpak list`.
    """
    code, out, err = run_host_command(
        ["flatpak", "list", "--app", "--columns=application"]
    )
    if code != 0:
        return []
    apps = [line.strip() for line in out.splitlines() if line.strip()]
    # remove duplicates while preserving order
    seen = set()
    uniq = []
    for a in apps:
        if a not in seen:
            uniq.append(a)
            seen.add(a)
    return uniq


def join_shell_cmd(parts: List[str]) -> str:
    """
    Human-friendly shell join (for preview)
    """
    return " ".join(shlex.quote(p) for p in parts)


# ----------------------------- UI rows helpers -----------------------------

def add_rows(page: Adw.PreferencesPage, title: Optional[str], *rows: Adw.ActionRow) -> Adw.PreferencesGroup:
    """
    Create a PreferencesGroup, add the given rows, then add the group to the page.
    Return the created group.
    """
    group = Adw.PreferencesGroup(title=title) if title else Adw.PreferencesGroup()
    for r in rows:
        group.add(r)
    page.add(group)
    return group


# ----------------------------- dataclass model -----------------------------

@dataclass
class LSFGOptions:
    multiplier: str = "2"        # 2/3/4/6/8
    flow_scale: bool = False
    performance: bool = False
    hdr: bool = False
    present_mode: str = "auto"   # auto/fifo/mailbox/immediate
    lsfg_process: str = ""       # optional
    extra_args: str = ""         # appended to target command


# ----------------------------- Main Window -----------------------------

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application):
        super().__init__(application=app)
        self.set_default_size(900, 620)
        self.set_title("LSFG-VK Launcher")

        self.options = LSFGOptions()

        # view stack + switcher
        self.stack = Adw.ViewStack()

        # pages
        self.page_flatpak = self._build_flatpak_page()
        self.page_host    = self._build_host_page()
        self.page_opts    = self._build_options_page()
        self.page_help    = self._build_help_page()

        self.stack.add_titled(self.page_flatpak, "flatpak", "Flatpak")
        self.stack.add_titled(self.page_host,    "host",    "Host")
        self.stack.add_titled(self.page_opts,    "options", "Options")
        self.stack.add_titled(self.page_help,    "help",    "Help")

        # toolbar + headerbar + switcherbar
        self.toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        self.toolbar.add_top_bar(header)

        switcher_bar = Adw.ViewSwitcherBar()
        switcher_bar.set_stack(self.stack)
        self.toolbar.add_bottom_bar(switcher_bar)

        # bottom action area (Preview / Launch + preview text)
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_top=8, margin_bottom=8, margin_start=12, margin_end=12)

        btn_box = Gtk.Box(spacing=8)
        self.btn_preview = Gtk.Button(label="Preview")
        self.btn_launch  = Gtk.Button(label="Launch")
        self.btn_preview.connect("clicked", self.on_preview_clicked)
        self.btn_launch.connect("clicked", self.on_launch_clicked)
        btn_box.append(self.btn_preview)
        btn_box.append(self.btn_launch)

        self.preview_view = Gtk.TextView(editable=False, monospace=True, wrap_mode=Gtk.WrapMode.CHAR)
        self.preview_buf  = self.preview_view.get_buffer()
        self.preview_view.set_size_request(-1, 100)
        bottom_box.append(btn_box)
        bottom_box.append(self.preview_view)

        # compose main content
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(self.stack)
        main_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        main_box.append(bottom_box)

        self.toolbar.set_content(main_box)
        self.set_content(self.toolbar)

        # initial load
        GLib.idle_add(self._reload_flatpak_list)

    # ------------------- Flatpak page -------------------

    def _build_flatpak_page(self) -> Adw.PreferencesPage:
        page = Adw.PreferencesPage()

        # app selector
        self.flatpak_model = Gtk.StringList.new([])
        self.flatpak_combo = Adw.ComboRow(title="Application", subtitle="Choose an installed Flatpak", model=self.flatpak_model)
        self.btn_refresh = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        self.btn_refresh.set_tooltip_text("Refresh list")
        self.btn_refresh.connect("clicked", lambda *_: self._reload_flatpak_list())
        self.flatpak_combo.add_suffix(self.btn_refresh)
        self.flatpak_combo.set_use_subtitle(True)

        # extra args
        self.flatpak_args = Adw.EntryRow(title="Extra arguments", text="")
        self.flatpak_args.set_show_apply_button(False)
        self.flatpak_args.set_placeholder_text("--fullscreen  (example)")

        add_rows(page, "Flatpak target", self.flatpak_combo, self.flatpak_args)
        return page

    def _reload_flatpak_list(self):
        apps = list_installed_flatpaks()
        self.flatpak_model.splice(0, self.flatpak_model.get_n_items(), apps)
        if apps:
            self.flatpak_combo.set_selected(0)

    # ------------------- Host page -------------------

    def _build_host_page(self) -> Adw.PreferencesPage:
        page = Adw.PreferencesPage()

        self.host_cmd = Adw.EntryRow(title="Command", text="")
        self.host_cmd.set_placeholder_text("e.g. vlc  or  /usr/bin/retroarch")
        self.host_args = Adw.EntryRow(title="Extra arguments", text="")
        self.host_args.set_placeholder_text("--some-flag value")

        # simple file chooser button to pick an exe
        self.btn_browse = Gtk.Button(label="Browse…")
        self.btn_browse.set_tooltip_text("Pick an executable from host")
        self.btn_browse.connect("clicked", self.on_browse_clicked)
        self.host_cmd.add_suffix(self.btn_browse)

        add_rows(page, "Host target (system app)", self.host_cmd, self.host_args)
        return page

    def on_browse_clicked(self, *_):
        dialog = Gtk.FileDialog(title="Choose executable")
        def _on_done(_d, res, self=self):
            try:
                file = _d.open_finish(res)
                if file:
                    self.host_cmd.set_text(file.get_path() or "")
            except Exception:
                pass
        dialog.open(self, None, _on_done)

    # ------------------- Options page -------------------

    def _build_options_page(self) -> Adw.PreferencesPage:
        page = Adw.PreferencesPage()

        # multiplier
        mult_model = Gtk.StringList.new(["2", "3", "4", "6", "8"])
        self.row_mult = Adw.ComboRow(title="Multiplier (X)", model=mult_model)
        self.row_mult.set_selected(0)

        # switches
        self.row_flow = Adw.SwitchRow(title="Flow Scale")
        self.row_perf = Adw.SwitchRow(title="Performance mode")
        self.row_hdr  = Adw.SwitchRow(title="HDR")

        # present mode
        pm_model = Gtk.StringList.new(["auto", "fifo", "mailbox", "immediate"])
        self.row_present = Adw.ComboRow(title="Present mode", model=pm_model)
        self.row_present.set_selected(0)

        # LSFG_PROCESS + extra env/args
        self.row_process = Adw.EntryRow(title="LSFG_PROCESS (optional)")
        self.row_extra   = Adw.EntryRow(title="Extra args (app)", text="")
        self.row_extra.set_placeholder_text("additional arguments for the target app")

        add_rows(page, "Scaling & Modes", self.row_mult, self.row_flow, self.row_perf, self.row_hdr, self.row_present)
        add_rows(page, "Advanced", self.row_process, self.row_extra)
        return page

    # ------------------- Help page -------------------

    def _build_help_page(self) -> Adw.PreferencesPage:
        page = Adw.PreferencesPage()

        row_help = Adw.ActionRow(title="Notes", subtitle="lsfg-vk is a Vulkan layer. Target apps must use Vulkan (or GL→Vulkan via Zink).")
        row_repo = Adw.ActionRow(title="Project page", subtitle="GitHub repository and documentation")
        btn_open = Gtk.Button.new_from_icon_name("external-link-symbolic")
        btn_open.set_tooltip_text("Open GitHub")
        btn_open.connect("clicked", lambda *_: Gio.AppInfo.launch_default_for_uri(
            "https://github.com/0xREAVEN/lsfgvk-launcher", None))
        row_repo.add_suffix(btn_open)
        row_repo.set_activatable(True)
        row_repo.connect("activated", lambda *_: Gio.AppInfo.launch_default_for_uri(
            "https://github.com/0xREAVEN/lsfgvk-launcher", None))

        add_rows(page, "Help", row_help, row_repo)
        return page

    # ------------------- command building -------------------

    def collect_options(self) -> LSFGOptions:
        o = LSFGOptions()
        o.multiplier   = self._combo_value(self.row_mult)
        o.flow_scale   = self.row_flow.get_active()
        o.performance  = self.row_perf.get_active()
        o.hdr          = self.row_hdr.get_active()
        o.present_mode = self._combo_value(self.row_present)
        o.lsfg_process = self.row_process.get_text().strip()
        o.extra_args   = self.row_extra.get_text().strip()
        return o

    def _combo_value(self, comborow: Adw.ComboRow) -> str:
        model = comborow.get_model()
        idx = comborow.get_selected()
        if idx < 0 or idx >= model.get_n_items():
            return ""
        return model.get_string(idx)

    def build_env_pairs(self, opts: LSFGOptions) -> List[str]:
        env = []
        env.append(f"LSFG_MULTIPLIER={opts.multiplier}")
        env.append(f"LSFG_FLOW_SCALE={'1' if opts.flow_scale else '0'}")
        env.append(f"LSFG_PERFORMANCE={'1' if opts.performance else '0'}")
        env.append(f"LSFG_HDR={'1' if opts.hdr else '0'}")
        if opts.present_mode and opts.present_mode != "auto":
            env.append(f"LSFG_PRESENT_MODE={opts.present_mode}")
        if opts.lsfg_process:
            env.append(f"LSFG_PROCESS={opts.lsfg_process}")
        env.append("VK_INSTANCE_LAYERS=lsfg_vk")
        env.append("VK_LAYER_PATH=/usr/share/vulkan/explicit_layer.d:/etc/vulkan/explicit_layer.d")
        return env

    def build_command(self) -> List[str]:
        """
        Build the host command according to the currently selected page.
        Always starts with: flatpak-spawn --host env VAR=... ... <cmd> [args...]
        """
        opts = self.collect_options()
        env_pairs = self.build_env_pairs(opts)

        # base prefix: run on host with env injected
        cmd: List[str] = ["flatpak-spawn", "--host", "env"] + env_pairs

        if self.stack.get_visible_child_name() == "flatpak":
            idx = self.flatpak_combo.get_selected()
            if idx < 0 or idx >= self.flatpak_model.get_n_items():
                raise RuntimeError("No Flatpak application selected")
            appid = self.flatpak_model.get_string(idx)
            args = shlex.split(self.flatpak_args.get_text().strip() or "")
            cmd += ["flatpak", "run", appid] + args

        elif self.stack.get_visible_child_name() == "host":
            target = self.host_cmd.get_text().strip()
            if not target:
                raise RuntimeError("No host command provided")
            args = shlex.split(self.host_args.get_text().strip() or "")
            cmd += [target] + args

        else:
            raise RuntimeError("Select Flatpak or Host tab")

        # Append extra args (options page)
        self.options.extra_args = self.row_extra.get_text().strip()
        if self.options.extra_args:
            extra = shlex.split(self.options.extra_args)
            cmd += extra

        return cmd

    # ------------------- actions -------------------

    def on_preview_clicked(self, *_):
        try:
            cmd = self.build_command()
            text = join_shell_cmd(cmd)
        except Exception as e:
            text = f"# ERROR: {e}"
        self.preview_buf.set_text(text)

    def on_launch_clicked(self, *_):
        try:
            cmd = self.build_command()
        except Exception as e:
            self._toast(f"Build error: {e}")
            self.on_preview_clicked()
            return

        try:
            _ = GLib.Subprocess.new(cmd, GLib.SubprocessFlags.NONE)
            self._toast("Launched ✅")
            self.on_preview_clicked()
        except Exception as e:
            self._toast(f"Launch failed: {e}")
            self.on_preview_clicked()

    def _toast(self, msg: str):
        print(msg)


# ----------------------------- Application -----------------------------

class LSFGVKApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self.do_activate)

    def do_activate(self, *_):
        if self.props.active_window:
            self.props.active_window.present()
            return
        win = MainWindow(self)
        win.present()


def main(argv: List[str]) -> int:
    Adw.init()
    app = LSFGVKApp()
    return app.run(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
