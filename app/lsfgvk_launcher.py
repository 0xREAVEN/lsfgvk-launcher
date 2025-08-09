#!/usr/bin/env python3
import gi, subprocess, shlex

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio

APP_ID = "io.reaven.LSFGVKLauncher"

class FlatpakApp:
    def __init__(self, app_id: str, name: str, branch: str):
        self.app_id = app_id
        self.name = name
        self.branch = branch

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("LSFG‑VK Launcher")
        self.set_default_size(920, 560)

        self.flatpaks = []
        self._filtered = []
        self.selected_app = None

        self._host_candidates = []
        self._filtered_host = []
        self.selected_host_cmd = None

        self._build_ui()
        self._load_flatpaks()

    # ---------- UI ----------
    def _build_ui(self):
        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)

        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(title="LSFG‑VK Launcher", subtitle="Run Flatpak & Host apps with frame‑gen"))

        self.btn_preview = Gtk.Button(label="Preview command")
        self.btn_preview.connect("clicked", self.on_preview)
        header.pack_start(self.btn_preview)

        self.btn_launch = Gtk.Button(label="Launch")
        self.btn_launch.add_css_class("suggested-action")
        self.btn_launch.connect("clicked", self.on_launch)
        header.pack_end(self.btn_launch)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        root.append(header)

        content = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        root.append(content)

        self.toast_overlay.set_child(root)

        # Left: target picker via a Notebook (Flatpak / Host)
        left_notebook = Adw.ViewStack()
        left_switcher = Adw.ViewSwitcherBar()
        left_switcher.set_stack(left_notebook)

        # --- Flatpak page ---
        vfp = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        self.search_fp = Gtk.SearchEntry(placeholder_text="Search installed Flatpaks…")
        self.search_fp.connect("search-changed", lambda *_: self._apply_filter_flatpak())
        vfp.append(self.search_fp)

        self.store_fp = Gtk.StringList()
        self.listview_fp = Gtk.ListView.new(Gtk.SingleSelection.new(self.store_fp), Gtk.SignalListItemFactory.new())

        def setup_fp(_factory, listitem):
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, margin_top=6, margin_bottom=6, margin_start=6, margin_end=6)
            title = Gtk.Label(xalign=0); title.add_css_class("title-4")
            subtitle = Gtk.Label(xalign=0); subtitle.add_css_class("dim-label"); subtitle.set_wrap(True)
            box.append(title); box.append(subtitle)
            listitem.set_child(box)

        def bind_fp(_factory, listitem):
            idx = listitem.get_position()
            if idx < 0 or idx >= len(self._filtered):
                return
            app = self._filtered[idx]
            box = listitem.get_child(); labels = box.get_children()
            labels[0].set_text(app.name or app.app_id)
            labels[1].set_text(f"{app.app_id} — {app.branch}")

        factory_fp = self.listview_fp.get_factory()
        factory_fp.connect("setup", setup_fp)
        factory_fp.connect("bind", bind_fp)
        self.listview_fp.connect("activate", self.on_pick_flatpak)
        vfp.append(self.listview_fp)

        # --- Host page ---
        vh = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        host_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.search_host = Gtk.SearchEntry(placeholder_text="Search host commands (type to fetch)…")
        self.search_host.connect("search-changed", self.on_host_search)
        host_bar.append(self.search_host)
        self.btn_fetch_host = Gtk.Button(label="Index host commands")
        self.btn_fetch_host.connect("clicked", lambda *_: self._load_host_cmds(force=True))
        host_bar.append(self.btn_fetch_host)
        vh.append(host_bar)

        self.store_host = Gtk.StringList()
        self.listview_host = Gtk.ListView.new(Gtk.SingleSelection.new(self.store_host), Gtk.SignalListItemFactory.new())

        def setup_h(_factory, listitem):
            listitem.set_child(Gtk.Label(xalign=0))
        def bind_h(_factory, listitem):
            idx = listitem.get_position()
            if 0 <= idx < len(self._filtered_host):
                listitem.get_child().set_text(self._filtered_host[idx])
        factory_h = self.listview_host.get_factory()
        factory_h.connect("setup", setup_h)
        factory_h.connect("bind", bind_h)
        self.listview_host.connect("activate", self.on_pick_host)
        vh.append(self.listview_host)

        left_notebook.add_titled(vfp, "flatpak", "Flatpak Apps")
        left_notebook.add_titled(vh, "host", "Host Apps")

        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        left_box.append(left_notebook)
        left_box.append(left_switcher)

        # Right: options
        right = Adw.PreferencesPage()

        sec_target = Adw.PreferencesGroup(title="Target")
        self.lbl_target = Gtk.Label(label="(no app selected)")
        row_target = Adw.ActionRow(title="Selected target")
        row_target.add_suffix(self.lbl_target)
        row_target.set_activatable(False)
        sec_target.add(row_target)

        sec_mult = Adw.PreferencesGroup(title="Frame Generation")
        self.cmb_mult = Gtk.DropDown.new_from_strings(["2", "3", "4", "6", "8"])
        self.cmb_mult.set_selected(0)
        row_mult = Adw.ActionRow(title="Multiplier (X)")
        row_mult.add_suffix(self.cmb_mult)
        sec_mult.add(row_mult)

        self.scale_flow = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.25, 1.0, 0.05)
        self.scale_flow.set_value(1.0)
        self.scale_flow.set_hexpand(True)
        row_flow = Adw.ActionRow(title="Flow scale")
        row_flow.add_suffix(self.scale_flow)
        sec_mult.add(row_flow)

        self.sw_perf = Gtk.Switch(active=False)
        row_perf = Adw.ActionRow(title="Performance mode")
        row_perf.add_suffix(self.sw_perf)
        row_perf.set_activatable_widget(self.sw_perf)
        sec_mult.add(row_perf)

        self.sw_hdr = Gtk.Switch(active=False)
        row_hdr = Adw.ActionRow(title="HDR mode")
        row_hdr.add_suffix(self.sw_hdr)
        row_hdr.set_activatable_widget(self.sw_hdr)
        sec_mult.add(row_hdr)

        self.cmb_present = Gtk.DropDown.new_from_strings(["(auto)", "fifo", "vsync", "mailbox", "immediate"])  # fifo==vsync alias
        self.cmb_present.set_selected(0)
        row_present = Adw.ActionRow(title="Present mode override")
        row_present.add_suffix(self.cmb_present)
        sec_mult.add(row_present)

        sec_adv = Adw.PreferencesGroup(title="Advanced")
        self.entry_proc = Gtk.Entry(placeholder_text="Optional: LSFG_PROCESS override")
        row_proc = Adw.ActionRow(title="Process name override")
        row_proc.add_suffix(self.entry_proc)
        sec_adv.add(row_proc)

        self.entry_args = Gtk.Entry(placeholder_text="Optional: extra args (file path, URL, etc.)")
        row_args = Adw.ActionRow(title="Extra launch args")
        row_args.add_suffix(self.entry_args)
        sec_adv.add(row_args)

        row_help = Adw.ActionRow(title="Docs")
        btn_help = Gtk.Button(label="Open Flatpak wiki page…")
        btn_help.connect("clicked", self.on_help)
        row_help.add_suffix(btn_help)

        right.add(sec_target)
        right.add(sec_mult)
        right.add(sec_adv)
        right.add(row_help)

        content.set_start_child(left_box)
        content.set_end_child(right)

    # ---------- Data loading ----------
    def _load_flatpaks(self):
        try:
            cmd = ["flatpak-spawn", "--host", "flatpak", "list", "--app", "--columns=application,name,branch"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            apps = []
            for line in res.stdout.splitlines():
                parts = [p for p in line.split('\t') if p]
                if len(parts) >= 3:
                    apps.append(FlatpakApp(parts[0], parts[1], parts[2]))
            self.flatpaks = sorted(apps, key=lambda a: (a.name or a.app_id).lower())
        except Exception as e:
            self.flatpaks = []
            self._toast(f"Failed to enumerate Flatpaks: {e}")
        self._apply_filter_flatpak()

    def _apply_filter_flatpak(self):
        q = (self.search_fp.get_text() or "").lower()
        self._filtered = [a for a in self.flatpaks if q in a.app_id.lower() or q in (a.name or "").lower()]
        self.store_fp.splice(0, self.store_fp.get_n_items(), [])
        for a in self._filtered:
            self.store_fp.append(a.name or a.app_id)

    def _load_host_cmds(self, force=False):
        if self._host_candidates and not force:
            self._apply_filter_host()
            return
        try:
            cmd = ["flatpak-spawn", "--host", "bash", "-lc", "compgen -c | sort -u"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self._host_candidates = [l.strip() for l in res.stdout.splitlines() if l.strip()]
        except Exception as e:
            self._host_candidates = []
            self._toast(f"Failed to enumerate host commands: {e}")
        self._apply_filter_host()

    def _apply_filter_host(self):
        q = (self.search_host.get_text() or "").lower()
        if not self._host_candidates:
            self.store_host.splice(0, self.store_host.get_n_items(), [])
            return
        self._filtered_host = [c for c in self._host_candidates if q in c.lower()][:500]
        self.store_host.splice(0, self.store_host.get_n_items(), [])
        for c in self._filtered_host:
            self.store_host.append(c)

    # ---------- Actions ----------
    def on_host_search(self, *_):
        if not self._host_candidates:
            self._load_host_cmds()
        else:
            self._apply_filter_host()

    def on_pick_flatpak(self, _listview, pos):
        if 0 <= pos < len(self._filtered):
            self.selected_app = self._filtered[pos]
            self.selected_host_cmd = None
            self.lbl_target.set_text(f"Flatpak: {self.selected_app.name} ({self.selected_app.app_id})")

    def on_pick_host(self, _listview, pos):
        if 0 <= pos < len(self._filtered_host):
            self.selected_host_cmd = self._filtered_host[pos]
            self.selected_app = None
            self.lbl_target.set_text(f"Host: {self.selected_host_cmd}")

    def _build_env(self):
        env = {"LSFG_LEGACY": "1", "LSFG_MULTIPLIER": self.cmb_mult.get_selected_item().get_string()}
        flow = round(self.scale_flow.get_value(), 2)
        if flow != 1.0:
            env["LSFG_FLOW_SCALE"] = str(flow)
        if self.sw_perf.get_active():
            env["LSFG_PERFORMANCE_MODE"] = "1"
        if self.sw_hdr.get_active():
            env["LSFG_HDR_MODE"] = "1"
        present = self.cmb_present.get_selected_item().get_string()
        if present and present != "(auto)":
            env["LSFG_EXPERIMENTAL_PRESENT_MODE"] = "fifo" if present == "vsync" else present
        proc = self.entry_proc.get_text().strip()
        if proc:
            env["LSFG_PROCESS"] = proc
        return env

    def _build_command(self):
        env = self._build_env()
        extra = shlex.split(self.entry_args.get_text() or "")

        if self.selected_app is not None:
            # Flatpak app
            cmd = ["flatpak-spawn", "--host", "flatpak", "run"]
            cmd += [f"--env={k}={v}" for k, v in env.items()]
            cmd += [self.selected_app.app_id]
            cmd += extra
            return cmd
        elif self.selected_host_cmd is not None:
            # Host app via shell for PATH/aliases
            env_assign = " ".join(f"{k}={shlex.quote(v)}" for k, v in env.items())
            tail = " ".join([shlex.quote(self.selected_host_cmd)] + [shlex.quote(x) for x in extra])
            shell_line = f"{env_assign} {tail}" if env_assign else tail
            return ["flatpak-spawn", "--host", "bash", "-lc", shell_line]
        else:
            raise RuntimeError("Pick a target app (Flatpak or Host)")

    def on_preview(self, *_):
        try:
            cmd = self._build_command()
            text = " ".join(shlex.quote(c) for c in cmd)
            self._toast(text, 6000)
        except Exception as e:
            self._toast(str(e))

    def on_launch(self, *_):
        try:
            subprocess.Popen(self._build_command())
            self._toast("Launching…")
        except Exception as e:
            self._toast(f"Launch failed: {e}")

    def on_help(self, *_):
        url = "https://github.com/PancakeTAS/lsfg-vk/wiki/Using-lsfg%E2%80%90vk-in-Flatpak"
        Gio.AppInfo.launch_default_for_uri(url, None)

    def _toast(self, text: str, timeout=3000):
        t = Adw.Toast.new(text)
        t.set_timeout(timeout)
        self.toast_overlay.add_toast(t)

class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
    def do_activate(self):
        MainWindow(self).present()

if __name__ == "__main__":
    App().run()
