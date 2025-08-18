#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import gi, os, shlex, subprocess, json, pathlib, configparser
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GObject

APP_ID = "io.reaven.LSFGVKLauncher"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".var/app", APP_ID, "config")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.ini")

def ensure_dir(p):
    pathlib.Path(p).mkdir(parents=True, exist_ok=True)

def show_info(parent, title, body):
    dlg = Adw.MessageDialog.new(parent.get_root(), title, body)
    dlg.add_response("ok", "OK")
    dlg.set_close_response("ok")
    dlg.present()

def _discover_vk_layer_paths():
    """Retourne une liste ‘:’ des dossiers explicit_layer.d visibles dans le sandbox."""
    from glob import glob
    candidates = [
        "/usr/share/vulkan/explicit_layer.d",
        "/etc/vulkan/explicit_layer.d",
        # Les extensions Flatpak sont souvent montées ici :
        *glob("/usr/lib/extensions/*/vulkan/explicit_layer.d"),
        # En dernier recours, tente d’accéder au host (pas garanti) :
        "/run/host/usr/share/vulkan/explicit_layer.d",
        "/run/host/etc/vulkan/explicit_layer.d",
    ]
    found = [p for p in candidates if os.path.isdir(p)]
    return ":".join(found)

class LSFGOptions(GObject.GObject):
    multiplier = GObject.Property(type=int, default=2)
    flow_scale = GObject.Property(type=bool, default=False)
    performance = GObject.Property(type=bool, default=False)
    hdr = GObject.Property(type=bool, default=False)
    present_mode = GObject.Property(type=str, default="auto")  # auto, fifo, mailbox, immediate
    lsfg_process = GObject.Property(type=str, default="")
    extra_args = GObject.Property(type=str, default="")

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="LSFG-VK Launcher")
        self.set_default_size(780, 520)
        self.options = LSFGOptions()
        self._load_settings()

        self.stack = Adw.ViewStack()
        header = Adw.HeaderBar()
        switch_title = Adw.ViewSwitcherTitle()
        switch = Adw.ViewSwitcher(stack=self.stack)

        header.set_title_widget(switch_title)
        switch_title.set_stack(self.stack)
        header.pack_start(switch)

        root = Adw.ToolbarView()
        root.add_top_bar(header)
        root.set_content(self.stack)
        self.set_content(root)

        self.page_flatpak = self._build_flatpak_page()
        self.page_host = self._build_host_page()
        self.page_help = self._build_help_page()
        self.stack.add_titled(self.page_flatpak, "flatpak", "Flatpak")
        self.stack.add_titled(self.page_host, "host", "Host")
        self.stack.add_titled(self.page_help, "help", "Help")

    # ---------- pages ----------
    def _build_flatpak_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)

        # sélection d’appli Flatpak
        self.flatpak_combo = Adw.ComboRow(title="Application")
        self.flatpak_combo.set_subtitle("org.gnome.Showtime, org.videolan.VLC, …")
        self._refresh_flatpak_list()
        btn_refresh = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        btn_refresh.connect("clicked", lambda *_: self._refresh_flatpak_list())
        self.flatpak_combo.add_suffix(btn_refresh)

        # args
        self.flatpak_args = Adw.EntryRow(title="Extra arguments")
        self.flatpak_args.set_text("")
        self.flatpak_hint = Adw.ActionRow(title="Hint", subtitle="Example: --fullscreen")
        self._build_options_section(box)

        # zone preview + boutons
        self.preview = Gtk.TextView(editable=False, monospace=True, height_request=120)
        btn_box = Gtk.Box(spacing=6)
        btn_preview = Gtk.Button(label="Preview")
        btn_launch = Gtk.Button(label="Launch")
        btn_preview.connect("clicked", lambda *_: self._update_preview(mode="flatpak"))
        btn_launch.connect("clicked", lambda *_: self._launch(mode="flatpak"))
        btn_box.append(btn_preview); btn_box.append(btn_launch)

        group = Adw.PreferencesGroup(title="Flatpak target")
        group.add(self.flatpak_combo)
        group.add(self.flatpak_args)
        group.add(self.flatpak_hint)

        sc = Gtk.ScrolledWindow()
        sc.set_child(self.preview)

        box.append(group)
        box.append(btn_box)
        box.append(sc)
        return box

    def _build_host_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)

        # binaire host + args
        self.host_cmd = Adw.EntryRow(title="Executable", text="vlc")
        info_btn = Gtk.Button.new_from_icon_name("dialog-information-symbolic")
        info_btn.connect("clicked", lambda *_: show_info(self, "Executable",
                         "Nom d’une commande disponible sur l’hôte (ex: vlc, mpv, dolphin…)."))
        self.host_cmd.add_suffix(info_btn)

        self.host_args = Adw.EntryRow(title="Extra arguments", text="")
        self._build_options_section(box)

        self.preview_host = Gtk.TextView(editable=False, monospace=True, height_request=120)
        btn_box = Gtk.Box(spacing=6)
        btn_prev = Gtk.Button(label="Preview")
        btn_go = Gtk.Button(label="Launch")
        btn_prev.connect("clicked", lambda *_: self._update_preview(mode="host"))
        btn_go.connect("clicked", lambda *_: self._launch(mode="host"))
        btn_box.append(btn_prev); btn_box.append(btn_go)

        sc = Gtk.ScrolledWindow()
        sc.set_child(self.preview_host)

        group = Adw.PreferencesGroup(title="Host target")
        group.add(self.host_cmd)
        group.add(self.host_args)

        box.append(group)
        box.append(btn_box)
        box.append(sc)
        return box

    def _build_options_section(self, parent_box: Gtk.Box):
        group = Adw.PreferencesGroup(title="LSFG-vk options")

        # Multiplier
        row_mul = Adw.ActionRow(title="Multiplier (X)")
        mul_box = Gtk.Box(spacing=6)
        for v in (2,3,4,6,8):
            b = Gtk.ToggleButton(label=str(v))
            b.set_active(v == self.options.multiplier)
            def on_toggled(btn, val=v):
                if btn.get_active():
                    self.options.multiplier = val
                    for child in mul_box:
                        if isinstance(child, Gtk.ToggleButton) and child is not btn:
                            child.set_active(False)
            b.connect("toggled", on_toggled)
            mul_box.append(b)
        info = Gtk.Button.new_from_icon_name("dialog-information-symbolic")
        info.connect("clicked", lambda *_: show_info(self, "Multiplier",
            "LSFG_MULTIPLIER : facteur de génération d’images (2/3/4/6/8)."))
        row_mul.add_suffix(info)
        row_mul.add_suffix(mul_box)

        # Flow Scale
        row_fs = Adw.ActionRow(title="Flow Scale")
        sw_fs = Gtk.Switch(active=False)
        sw_fs.connect("notify::active", lambda *_: setattr(self.options, "flow_scale", sw_fs.get_active()))
        info2 = Gtk.Button.new_from_icon_name("dialog-information-symbolic")
        info2.connect("clicked", lambda *_: show_info(self, "Flow Scale",
            "LSFG_FLOW_SCALE : active le recalage des flux optiques."))
        row_fs.add_suffix(info2); row_fs.add_suffix(sw_fs)

        # Performance
        row_perf = Adw.ActionRow(title="Performance mode")
        sw_perf = Gtk.Switch(active=False)
        sw_perf.connect("notify::active", lambda *_: setattr(self.options, "performance", sw_perf.get_active()))
        info3 = Gtk.Button.new_from_icon_name("dialog-information-symbolic")
        info3.connect("clicked", lambda *_: show_info(self, "Performance",
            "LSFG_PERFORMANCE : mode performance du layer."))
        row_perf.add_suffix(info3); row_perf.add_suffix(sw_perf)

        # HDR
        row_hdr = Adw.ActionRow(title="HDR")
        sw_hdr = Gtk.Switch(active=False)
        sw_hdr.connect("notify::active", lambda *_: setattr(self.options, "hdr", sw_hdr.get_active()))
        info4 = Gtk.Button.new_from_icon_name("dialog-information-symbolic")
        info4.connect("clicked", lambda *_: show_info(self, "HDR",
            "LSFG_HDR : force le mode HDR s’il est supporté par l’app."))
        row_hdr.add_suffix(info4); row_hdr.add_suffix(sw_hdr)

        # Present mode
        row_pm = Adw.ActionRow(title="Present mode")
        combo = Gtk.DropDown.new_from_strings(["auto","fifo","mailbox","immediate"])
        combo.set_selected(0)
        combo.connect("notify::selected", lambda dd,_p: setattr(self.options, "present_mode",
                                                                ["auto","fifo","mailbox","immediate"][dd.get_selected()]))
        info5 = Gtk.Button.new_from_icon_name("dialog-information-symbolic")
        info5.connect("clicked", lambda *_: show_info(self, "Present mode",
            "LSFG_PRESENT_MODE : sélecteur de présent (auto/fifo/mailbox/immediate)."))
        row_pm.add_suffix(info5); row_pm.add_suffix(combo)

        # LSFG_PROCESS
        row_proc = Adw.EntryRow(title="LSFG_PROCESS (optional)")
        row_proc.set_text("")
        row_proc.connect("notify::text", lambda r,_p: setattr(self.options, "lsfg_process", r.get_text()))
        info6 = Gtk.Button.new_from_icon_name("dialog-information-symbolic")
        info6.connect("clicked", lambda *_: show_info(self, "LSFG_PROCESS",
            "Limite l’application du layer à un sous-processus (nom binaire)."))
        row_proc.add_suffix(info6)

        group.add(row_mul); group.add(row_fs); group.add(row_perf)
        group.add(row_hdr); group.add(row_pm); group.add(row_proc)
        parent_box.append(group)

    def _refresh_flatpak_list(self):
        # Liste simple (id Flatpak). Pour les icônes on passerait par un ListView + factory.
        ids = []
        out = subprocess.run(["flatpak","list","--app","--columns=application"], stdout=subprocess.PIPE, text=True, check=False)
        for line in out.stdout.splitlines():
            if line.strip(): ids.append(line.strip())
        model = Gtk.StringList.new(ids or ["org.gnome.Showtime"])
        self.flatpak_combo.set_model(model)

    # ---------- build env + commandes ----------
    def _env_from_options(self):
        env = {
            "VK_INSTANCE_LAYERS": "lsfg_vk",
            "LSFG_MULTIPLIER": str(self.options.multiplier),
            "LSFG_FLOW_SCALE": "1" if self.options.flow_scale else "0",
            "LSFG_PERFORMANCE": "1" if self.options.performance else "0",
            "LSFG_HDR": "1" if self.options.hdr else "0",
        }
        pm_map = {"auto":"auto","fifo":"fifo","mailbox":"mailbox","immediate":"immediate"}
        env["LSFG_PRESENT_MODE"] = pm_map.get(self.options.present_mode, "auto")

        if self.options.lsfg_process.strip():
            env["LSFG_PROCESS"] = self.options.lsfg_process.strip()

        vk_paths = _discover_vk_layer_paths()
        if vk_paths:
            env["VK_LAYER_PATH"] = vk_paths
        return env

    def _flatpak_target(self):
        model = self.flatpak_combo.get_model()
        sel = self.flatpak_combo.get_selected()
        if model and sel >= 0:
            return model.get_string(sel)
        return "org.gnome.Showtime"

    def _cmd_flatpak(self):
        env = self._env_from_options()
        args = shlex.split(self.flatpak_args.get_text() or "")
        cmd = ["flatpak-spawn","--host","env"]
        for k,v in env.items(): cmd.append(f"{k}={v}")
        cmd += ["flatpak","run", self._flatpak_target(), *args]
        return cmd

    def _cmd_host(self):
        env = self._env_from_options()
        args = shlex.split(self.host_args.get_text() or "")
        exe = (self.host_cmd.get_text() or "vlc").strip() or "vlc"
        cmd = ["env", *[f"{k}={v}" for k,v in env.items()], exe, *args]
        return cmd

    def _update_preview(self, mode="flatpak"):
        cmd = self._cmd_flatpak() if mode=="flatpak" else self._cmd_host()
        txt = " ".join(shlex.quote(c) for c in cmd)
        buffer = (self.preview if mode=="flatpak" else self.preview_host).get_buffer()
        buffer.set_text(txt)

    def _launch(self, mode="flatpak"):
        cmd = self._cmd_flatpak() if mode=="flatpak" else self._cmd_host()
        try:
            subprocess.Popen(cmd)
        except Exception as e:
            show_info(self, "Launch error", str(e))

    # ---------- settings ----------
    def _load_settings(self):
        ensure_dir(CONFIG_DIR)
        cfg = configparser.ConfigParser()
        if os.path.exists(CONFIG_FILE):
            cfg.read(CONFIG_FILE)
            s = cfg["lsfg"] if "lsfg" in cfg else {}
            self.options.multiplier = int(s.get("multiplier", self.options.multiplier))
            self.options.flow_scale = (s.get("flow_scale","0")=="1")
            self.options.performance = (s.get("performance","0")=="1")
            self.options.hdr = (s.get("hdr","0")=="1")
            self.options.present_mode = s.get("present_mode", self.options.present_mode)
            self.options.lsfg_process = s.get("lsfg_process","")
            # champs libres
            # (on laisse vides par défaut)
        else:
            pass

    def _save_settings(self):
        ensure_dir(CONFIG_DIR)
        cfg = configparser.ConfigParser()
        cfg["lsfg"] = {
            "multiplier": str(self.options.multiplier),
            "flow_scale": "1" if self.options.flow_scale else "0",
            "performance": "1" if self.options.performance else "0",
            "hdr": "1" if self.options.hdr else "0",
            "present_mode": self.options.present_mode,
            "lsfg_process": self.options.lsfg_process,
        }
        with open(CONFIG_FILE,"w") as f:
            cfg.write(f)

    def close_request(self, *a):
        self._save_settings()
        return super().close_request(*a)

    def _build_help_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        lab = Gtk.Label(
            label="Tips:\n- Installe l’extension org.freedesktop.Platform.VulkanLayer.lsfgvk (24.08 pour GNOME 48).\n"
                  "- VK_LAYER_PATH est détecté automatiquement (extensions et /usr/share/vulkan).",
            xalign=0, wrap=True)
        box.append(lab); return box

class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        win = MainWindow(self)
        win.present()

if __name__ == "__main__":
    app = App()
    app.run()
