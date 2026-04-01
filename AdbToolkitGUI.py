import os
import subprocess
import threading
import time
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk

# Configure global CustomTkinter Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ADBToolkitAppV2(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Advanced ADB Toolkit - Phone Link Alternative")
        self.geometry("900x600")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Bind unmap event to detect minimization
        self.bind("<Unmap>", self.on_unmap)
        
        # Determine the scrcpy executable path based on your folder structure
        self.scrcpy_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "scrcpy-win64-v3.3.4",
            "scrcpy-win64-v3.3.4",
            "scrcpy.exe"
        )
        self.scrcpy_exists = os.path.exists(self.scrcpy_path)
        
        # Auto-mirror and Auto-close state
        self.auto_mirror_enabled = True
        self.auto_mirror_running = False
        self.last_known_device = None
        self.auto_close_mirror_enabled = True
        self.scrcpy_process = None
        self.auto_sync_enabled = False
        self.auto_sync_running = False
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.setup_ui()
        
        # Start ADB server, check devices, and begin auto-mirror loop
        threading.Thread(target=self.init_adb, daemon=True).start()

    def setup_ui(self):
        # Main Frame setup
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1) # Allow console to expand
        
        # Header Label
        self.header_label = ctk.CTkLabel(self.main_frame, text="📱 Advanced Desktop-to-Phone Toolkit", font=ctk.CTkFont(size=24, weight="bold"))
        self.header_label.grid(row=0, column=0, pady=(10, 5))
        
        # Status Label Tracking Connection
        status_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        status_frame.grid(row=1, column=0, pady=(0, 10), sticky="ew")
        
        self.status_var = ctk.StringVar(value="Checking device status...")
        self.status_label = ctk.CTkLabel(status_frame, textvariable=self.status_var, font=ctk.CTkFont(size=14), text_color="yellow")
        self.status_label.pack(side="left")
        
        # Logs always hidden, button removed per user request
        
        self.is_always_on_top = False
        self.btn_always_on_top = ctk.CTkButton(status_frame, text="📌 Pin", width=60, height=24, fg_color="transparent", border_width=1, command=self.toggle_always_on_top)
        self.btn_always_on_top.pack(side="right", padx=10)
        
        # ----- TABVIEW SETUP -----
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        
        self.tab_mirror = self.tabview.add("Mirror & Core")
        self.tab_remote = self.tabview.add("Remote Control")
        self.tab_apps = self.tabview.add("Apps & Files")
        self.tab_wifi = self.tabview.add("Wireless ADB")
        self.tab_files = self.tabview.add("File Transfer")
        
        self.setup_tab_mirror()
        self.setup_tab_remote()
        self.setup_tab_apps()
        self.setup_tab_wifi()
        self.setup_tab_files()
        
        # ----- CONSOLE -----
        self.console = ctk.CTkTextbox(self.main_frame, height=150, font=ctk.CTkFont(family="Consolas", size=12), text_color="#a8ffb2", fg_color="#121212")
        self.console.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
        self.log("--- SYSTEM READY ---")
        
        # Always default to hidden
        self.console.grid_remove()

    def setup_tab_mirror(self):
        frame = ctk.CTkFrame(self.tab_mirror, fg_color="transparent")
        frame.pack(pady=10, fill="both", expand=True)
        
        # Device Controls
        dev_frame = ctk.CTkFrame(frame)
        dev_frame.pack(pady=10, fill="x")
        
        ctk.CTkLabel(dev_frame, text="USB / ADB Core Controls", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        btn_box1 = ctk.CTkFrame(dev_frame, fg_color="transparent")
        btn_box1.pack(pady=5)
        
        ctk.CTkButton(btn_box1, text="🔄 Refresh Devices", command=self.refresh_devices).pack(side="left", padx=10)
        self.btn_auto = ctk.CTkButton(btn_box1, text="⚡ Auto-Mirror: ON", fg_color="#e67e22", hover_color="#f39c12", command=self.toggle_auto_mirror)
        self.btn_auto.pack(side="left", padx=10)
        self.btn_auto_close = ctk.CTkButton(btn_box1, text="🚪 Auto-Close: ON", fg_color="#c0392b", hover_color="#e74c3c", command=self.toggle_auto_close_mirror)
        self.btn_auto_close.pack(side="left", padx=10)
        
        # Advanced Mirroring Options
        adv_frame = ctk.CTkFrame(frame)
        adv_frame.pack(pady=10, fill="x")
        
        ctk.CTkLabel(adv_frame, text="Advanced Screen Mirror Options", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, pady=5)
        
        self.screen_off_var = ctk.BooleanVar(value=True) # Default on for battery saving
        self.record_var = ctk.BooleanVar(value=False)
        self.audio_route_var = ctk.StringVar(value="PC (Forwarded)")
        
        ctk.CTkCheckBox(adv_frame, text="Power Off Phone Screen While Mirroring (Saves Battery)", variable=self.screen_off_var).grid(row=1, column=0, padx=20, pady=5, sticky="w")
        ctk.CTkCheckBox(adv_frame, text="Record Screen to PC Desktop (.mkv)", variable=self.record_var).grid(row=2, column=0, padx=20, pady=5, sticky="w")
        
        audio_frame = ctk.CTkFrame(adv_frame, fg_color="transparent")
        audio_frame.grid(row=3, column=0, padx=20, pady=5, sticky="w")
        ctk.CTkLabel(audio_frame, text="Audio:").pack(side="left")
        ctk.CTkOptionMenu(audio_frame, variable=self.audio_route_var, values=["PC (Forwarded)", "Phone Only", "Duplicate (Both)"]).pack(side="left", padx=10)
        
        self.btn_mirror = ctk.CTkButton(adv_frame, text="📺 Launch Mirror", fg_color="#27ae60", hover_color="#2ecc71", width=200, height=40, font=ctk.CTkFont(size=16, weight="bold"), command=self.launch_scrcpy)
        self.btn_mirror.grid(row=4, column=0, columnspan=2, pady=15)
        
        if not self.scrcpy_exists:
            self.btn_mirror.configure(state="disabled", text="❌ Scrcpy Not Found")

    def setup_tab_remote(self):
        frame = ctk.CTkFrame(self.tab_remote, fg_color="transparent")
        frame.pack(pady=10, fill="both", expand=True)
        
        # Hardware Keys Grid
        hw_frame = ctk.CTkFrame(frame)
        hw_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(hw_frame, text="Hardware Keys Injection", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=3, pady=10)
        
        btn_style = {"width": 120, "height": 40}
        ctk.CTkButton(hw_frame, text="🔊 Vol UP", command=lambda: self.send_keyevent(24), **btn_style).grid(row=1, column=0, padx=10, pady=10)
        ctk.CTkButton(hw_frame, text="🔌 Power", fg_color="#c0392b", hover_color="#e74c3c", command=lambda: self.send_keyevent(26), **btn_style).grid(row=1, column=1, padx=10, pady=10)
        ctk.CTkButton(hw_frame, text="⏯ Play/Pause", fg_color="#8e44ad", command=lambda: self.send_keyevent(85), **btn_style).grid(row=1, column=2, padx=10, pady=10)
        
        ctk.CTkButton(hw_frame, text="🔉 Vol DOWN", command=lambda: self.send_keyevent(25), **btn_style).grid(row=2, column=0, padx=10, pady=10)
        ctk.CTkButton(hw_frame, text="🏠 Home", command=lambda: self.send_keyevent(3), **btn_style).grid(row=2, column=1, padx=10, pady=10)
        ctk.CTkButton(hw_frame, text="🔙 Back", command=lambda: self.send_keyevent(4), **btn_style).grid(row=2, column=2, padx=10, pady=10)

        hw_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Text Injection
        txt_frame = ctk.CTkFrame(frame)
        txt_frame.pack(pady=20, padx=20, fill="x")
        ctk.CTkLabel(txt_frame, text="PC-to-Phone Text Input", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        self.txt_input = ctk.CTkEntry(txt_frame, placeholder_text="Type message here to send to phone...", width=400)
        self.txt_input.pack(side="left", padx=10, pady=10, fill="x", expand=True)
        
        btn_send = ctk.CTkButton(txt_frame, text="✉ Send Text", command=self.send_text)
        btn_send.pack(side="right", padx=10, pady=10)

    def setup_tab_apps(self):
        frame = ctk.CTkFrame(self.tab_apps, fg_color="transparent")
        frame.pack(pady=10, fill="both", expand=True)
        
        top_bar = ctk.CTkFrame(frame, fg_color="transparent")
        top_bar.pack(fill="x")
        
        ctk.CTkButton(top_bar, text="📥 Load Installed Apps", command=self.load_apps).pack(side="left", padx=5)
        self.show_system_apps_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(top_bar, text="Include System Apps", variable=self.show_system_apps_var).pack(side="left", padx=10)
        ctk.CTkButton(top_bar, text="📸 Pull Latest 5 Photos", fg_color="#8e44ad", command=self.pull_photos).pack(side="right", padx=5)
        
        # Scrollable App List
        self.app_list_frame = ctk.CTkScrollableFrame(frame, label_text="Installed Applications")
        self.app_list_frame.pack(pady=10, fill="both", expand=True)

    def setup_tab_wifi(self):
        frame = ctk.CTkFrame(self.tab_wifi, fg_color="transparent")
        frame.pack(pady=10, fill="both", expand=True)
        
        ctk.CTkLabel(frame, text="Wireless ADB Connection (No USB Required)", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        info_text = ("1. Plug in phone via USB ONE TIME per reboot.\n"
                     "2. Click 'Enable TCP/IP'.\n"
                     "3. Unplug USB, enter your phone's IP address below, and Connect!")
        ctk.CTkLabel(frame, text=info_text, justify="left").pack(pady=10)
        
        btn_tcp = ctk.CTkButton(frame, text="📡 Enable TCP/IP on Port 5555", fg_color="#d35400", command=self.enable_tcpip)
        btn_tcp.pack(pady=10)
        
        btn_get_ip = ctk.CTkButton(frame, text="🔍 Auto-Find Phone IP Address", command=self.find_device_ip)
        btn_get_ip.pack(pady=5)
        
        ip_frame = ctk.CTkFrame(frame, fg_color="transparent")
        ip_frame.pack(pady=20)
        
        ctk.CTkLabel(ip_frame, text="Phone IP:").pack(side="left", padx=5)
        self.ip_entry = ctk.CTkEntry(ip_frame, placeholder_text="192.168.1.xxx", width=150)
        self.ip_entry.pack(side="left", padx=5)
        
        ctk.CTkButton(ip_frame, text="Connect Wi-Fi", fg_color="#27ae60", command=self.connect_wifi).pack(side="left", padx=10)
        ctk.CTkButton(ip_frame, text="Disconnect", fg_color="#c0392b", command=self.disconnect_wifi).pack(side="left", padx=5)

    def setup_tab_files(self):
        frame = ctk.CTkFrame(self.tab_files, fg_color="transparent")
        frame.pack(pady=10, fill="both", expand=True)
        
        ctk.CTkLabel(frame, text="Two-Way File & App Transfer", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        # Push Section
        push_frame = ctk.CTkFrame(frame)
        push_frame.pack(pady=10, fill="x", padx=20)
        ctk.CTkLabel(push_frame, text="Push to Phone (PC -> Phone)", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, pady=5)
        
        btn_push = ctk.CTkButton(push_frame, text="📤 Select File to Push", fg_color="#2980b9", width=200, command=self.push_file)
        btn_push.grid(row=1, column=0, padx=20, pady=10)
        
        btn_apk = ctk.CTkButton(push_frame, text="📦 Install APK", fg_color="#8e44ad", width=200, command=self.install_apk)
        btn_apk.grid(row=1, column=1, padx=20, pady=10)
        push_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Pull Section
        pull_frame = ctk.CTkFrame(frame)
        pull_frame.pack(pady=10, fill="x", padx=20)
        ctk.CTkLabel(pull_frame, text="Pull from Phone (Phone -> PC)", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        self.pull_path_entry = ctk.CTkEntry(pull_frame, placeholder_text="/sdcard/Download/somefile.txt")
        self.pull_path_entry.pack(side="left", fill="x", expand=True, padx=20, pady=10)
        
        btn_pull = ctk.CTkButton(pull_frame, text="📥 Pull Path", fg_color="#27ae60", command=self.pull_file)
        btn_pull.pack(side="right", padx=20, pady=10)
        
        # Auto Sync Section
        sync_frame = ctk.CTkFrame(frame)
        sync_frame.pack(pady=10, fill="x", padx=20)
        ctk.CTkLabel(sync_frame, text="Auto-Sync Missing Files to PC", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        self.sync_path_entry = ctk.CTkEntry(sync_frame, placeholder_text="Remote Folder (e.g., /sdcard/DCIM/Camera)")
        self.sync_path_entry.insert(0, "/sdcard/DCIM/Camera")
        self.sync_path_entry.pack(side="left", fill="x", expand=True, padx=20, pady=10)
        
        self.btn_auto_sync = ctk.CTkButton(sync_frame, text="🔄 Start Auto-Sync", fg_color="#e67e22", hover_color="#f39c12", command=self.toggle_auto_sync)
        self.btn_auto_sync.pack(side="right", padx=20, pady=10)


    def toggle_always_on_top(self):
        self.is_always_on_top = not self.is_always_on_top
        self.attributes("-topmost", self.is_always_on_top)
        if self.is_always_on_top:
            self.btn_always_on_top.configure(fg_color="#27ae60", text_color="white")
        else:
            self.btn_always_on_top.configure(fg_color="transparent", text_color=("gray10", "#DCE4EE"))

    # --- CORE METHODS & ADB EXEC ---
    
    def log(self, text):
        def update_console():
            self.console.insert("end", text + "\n")
            self.console.see("end")
        self.after(0, update_console)

    def run_adb_cmd(self, args, log_output=True, timeout=15):
        try:
            startupinfo = None
            if os.name == 'nt':
                 startupinfo = subprocess.STARTUPINFO()
                 startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                 
            cmd = ["adb"] + args
            res = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo, timeout=timeout)
            
            if log_output and res.stdout:
                self.log(f"> adb {' '.join(args)}\n" + res.stdout.strip())
            if log_output and res.stderr:
                self.log(f"[Error]:\n" + res.stderr.strip())
            return res.stdout.strip()
        except subprocess.TimeoutExpired:
            self.log(f"[Error]: Command {' '.join(args)} timed out after {timeout}s.")
            return ""
        except Exception as e:
            self.log(f"[Exception]: {str(e)}")
            return ""

    def init_adb(self):
        self.log("[*] Starting ADB Server...")
        self.run_adb_cmd(["start-server"], log_output=False)
        self.refresh_devices()
        if self.auto_mirror_enabled and not self.auto_mirror_running:
            self.auto_mirror_running = True
            threading.Thread(target=self.auto_mirror_loop, daemon=True).start()
        
    def refresh_devices(self):
        out = self.run_adb_cmd(["devices"], log_output=False)
        lines = out.split('\n')[1:]
        devices = []
        for line in lines:
            if "\tdevice" in line:
                devices.append(line.split("\t")[0])
                
        if devices:
            def update_gui_on():
                self.status_var.set(f"✅ Secure Connection: {devices[0]}")
                self.status_label.configure(text_color="#2ecc71")
            self.after(0, update_gui_on)
            self.log(f"[+] Found device(s): {', '.join(devices)}")
            return devices[0]
        else:
            def update_gui_off():
                self.status_var.set("❌ No Active Connection")
                self.status_label.configure(text_color="#e74c3c")
            self.after(0, update_gui_off)
            return None

    # --- MIRRORING METHODS ---

    def launch_scrcpy(self):
        if not self.scrcpy_exists:
            self.log("[!] Scrcpy executable not found.")
            return
            
        self.log("[*] Launching Screen Mirror...")
        
        args = [self.scrcpy_path, "--always-on-top"]
        
        if self.screen_off_var.get():
            args.append("--turn-screen-off")
        else:
            args.append("--stay-awake") # standard behavior
            
        audio_route = getattr(self, "audio_route_var", None)
        if audio_route:
            if audio_route.get() == "Phone Only":
                args.append("--no-audio")
            elif audio_route.get() == "Duplicate (Both)":
                args.append("--audio-dup")
        
        if self.record_var.get():
            desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
            filename = f"scrcpy_record_{int(time.time())}.mkv"
            args.extend(["--record", os.path.join(desktop_path, filename)])
            self.log(f"[*] Recording to Desktop: {filename}")
            
        def worker(cmd):
            creationflags = 0
            if os.name == 'nt':
                creationflags = subprocess.CREATE_NO_WINDOW
            self.scrcpy_process = subprocess.Popen(cmd, creationflags=creationflags)
            
        threading.Thread(target=worker, args=(args,), daemon=True).start()

    def toggle_auto_mirror(self):
        self.auto_mirror_enabled = not self.auto_mirror_enabled
        if self.auto_mirror_enabled:
            self.btn_auto.configure(text="⚡ Auto-Mirror: ON", fg_color="#e67e22")
            if not self.auto_mirror_running:
                self.auto_mirror_running = True
                threading.Thread(target=self.auto_mirror_loop, daemon=True).start()
        else:
            self.btn_auto.configure(text="⚡ Auto-Mirror: OFF", fg_color="#7f8c8d")
            
    def toggle_auto_close_mirror(self):
        self.auto_close_mirror_enabled = not self.auto_close_mirror_enabled
        if self.auto_close_mirror_enabled:
            self.btn_auto_close.configure(text="🚪 Auto-Close: ON", fg_color="#c0392b")
        else:
            self.btn_auto_close.configure(text="🚪 Auto-Close: OFF", fg_color="#7f8c8d")

    def auto_mirror_loop(self):
        while self.auto_mirror_enabled:
            device = self.refresh_devices()
            if device and device != self.last_known_device and not self.is_scrcpy_running():
                self.last_known_device = device
                self.log(f"[⚡] Auto-launching mirror for: {device}")
                time.sleep(2)
                self.launch_scrcpy()
                time.sleep(5)
            elif not device:
                self.last_known_device = None
            time.sleep(3)
        self.auto_mirror_running = False

    def is_scrcpy_running(self):
        if self.scrcpy_process is not None:
            # poll() returns None if process is still running, otherwise returns exit code
            return self.scrcpy_process.poll() is None
        return False

    def on_closing(self):
        if self.auto_close_mirror_enabled:
            # Gracefully terminate our process if tracked
            if self.scrcpy_process is not None and self.scrcpy_process.poll() is None:
                try:
                    self.scrcpy_process.terminate()
                    self.scrcpy_process.wait(timeout=2)
                except:
                    pass
            # Fallback to taskkill
            try:
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                subprocess.run(["taskkill", "/F", "/IM", "scrcpy.exe"], capture_output=True, startupinfo=startupinfo)
            except:
                pass
        self.destroy()

    # --- DESKTOP OVERLAY ICON ---

    def on_unmap(self, event):
        if event.widget is self and self.wm_state() == 'iconic':
            self.create_overlay_icon()

    def create_overlay_icon(self):
        # Don't create multiple overlays
        if hasattr(self, 'overlay') and self.overlay.winfo_exists():
            return
            
        self.withdraw() # Hide the main big GUI window
        
        self.overlay = tk.Toplevel(self)
        self.overlay.overrideredirect(True) # Remove standard window borders
        self.overlay.attributes('-topmost', True) # Stay on top of other windows
        self.overlay.geometry("50x50+100+100") # 50x50 size, upper left corner
        self.overlay.configure(bg="#2ecc71")
        
        # Improved Click and drag logic (using root coords to avoid glitching)
        self.dock_to_scrcpy = True # By default, dock to the phone screen
        
        def start_drag(event):
            self.dock_to_scrcpy = False # Manual drag breaks the auto-docking
            self.overlay._drag_start_x = event.x_root
            self.overlay._drag_start_y = event.y_root
            self.overlay._drag_moved = False

        def do_drag(event):
            dx = event.x_root - self.overlay._drag_start_x
            dy = event.y_root - self.overlay._drag_start_y
            if abs(dx) > 2 or abs(dy) > 2:
                self.overlay._drag_moved = True
            x = self.overlay.winfo_x() + dx
            y = self.overlay.winfo_y() + dy
            self.overlay.geometry(f"+{x}+{y}")
            self.overlay._drag_start_x = event.x_root
            self.overlay._drag_start_y = event.y_root

        # Single click to restore main GUI
        def on_release(event):
            if not getattr(self.overlay, '_drag_moved', False):
                restore()

        def restore(event=None):
            self.overlay.destroy()
            self.deiconify() # Bring back main GUI
            self.wm_state('normal') # Ensure it exits minimize state
            self.focus_force()   # Force focus to the window
            self.lift()          # Bring to front

        # background loop to track scrcpy window and stick to it
        def track_scrcpy():
            if not getattr(self, "overlay", None) or not self.overlay.winfo_exists():
                return
            if self.dock_to_scrcpy:
                try:
                    import ctypes
                    from ctypes import wintypes
                    hwnd = ctypes.windll.user32.FindWindowW("SDL_app", None)
                    if hwnd:
                        rect = wintypes.RECT()
                        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                        # Attach perfectly to the top right outside edge of the phone
                        x = rect.right
                        y = rect.top
                        if x > 0 and y > 0:
                            self.overlay.geometry(f"50x50+{x}+{y}")
                except Exception as e:
                    pass
            self.after(30, track_scrcpy) # Poll fast for smooth sticking
            
        track_scrcpy()

        # Add the phone icon
        lbl = tk.Label(self.overlay, text="📱", font=("Segoe UI Emoji", 24), bg="#2ecc71", fg="white")
        lbl.pack(expand=True, fill="both")
        
        # Add bindings for dragging on both the window and the label
        lbl.bind("<ButtonPress-1>", start_drag)
        lbl.bind("<B1-Motion>", do_drag)
        lbl.bind("<ButtonRelease-1>", on_release)
        
        self.overlay.bind("<ButtonPress-1>", start_drag)
        self.overlay.bind("<B1-Motion>", do_drag)
        self.overlay.bind("<ButtonRelease-1>", on_release)

    # --- ADVANCED ADB METHODS (REMOTE) ---

    def send_keyevent(self, keycode):
        self.log(f"[*] Sending Keyevent {keycode}")
        def worker():
            self.run_adb_cmd(["shell", "input", "keyevent", str(keycode)], log_output=False)
        threading.Thread(target=worker, daemon=True).start()

    def send_text(self):
        txt = self.txt_input.get()
        if not txt: return
        self.log(f"[*] Injecting text: {txt}")
        # Need to replace spaces with %s for adb shell input text
        formatted_txt = txt.replace(' ', '%s')
        def worker():
            self.run_adb_cmd(["shell", "input", "text", f'"{formatted_txt}"'], log_output=False)
            self.after(0, lambda: self.txt_input.delete(0, 'end'))
        threading.Thread(target=worker, daemon=True).start()

    # --- APP MANAGEMENT & FILE METHODS ---

    def load_apps(self):
        # Clear existing
        for widget in self.app_list_frame.winfo_children():
            widget.destroy()
            
        sys_apps = getattr(self, "show_system_apps_var", None)
        include_sys = sys_apps is not None and sys_apps.get()
        msg = "[*] Fetching all apps..." if include_sys else "[*] Fetching 3rd party apps..."
        self.log(msg)
        
        def worker():
            cmd = ["shell", "pm", "list", "packages"]
            if not include_sys:
                cmd.append("-3")
            out = self.run_adb_cmd(cmd, log_output=False)
            if not out: return
            
            packages = [line.replace("package:", "").strip() for line in out.split('\n') if line.startswith("package:")]
            packages.sort()
            
            # Update GUI from main thread
            for pkg in packages:
                self.after(0, self.add_app_row, pkg)
        threading.Thread(target=worker, daemon=True).start()

    def add_app_row(self, pkg_name):
        row = ctk.CTkFrame(self.app_list_frame)
        row.pack(fill="x", pady=2, padx=1)
        
        lbl = ctk.CTkLabel(row, text=pkg_name, anchor="w")
        lbl.pack(side="left", padx=10)
        
        btn_launch = ctk.CTkButton(row, text="Launch", width=60, height=24, fg_color="#27ae60", hover_color="#2ecc71", command=lambda p=pkg_name: self.launch_app(p))
        btn_launch.pack(side="right", padx=5)
        
        btn_settings = ctk.CTkButton(row, text="App Settings", width=90, height=24, fg_color="#3498db", hover_color="#2980b9", command=lambda p=pkg_name: self.open_app_info(p))
        btn_settings.pack(side="right", padx=5)
        
        btn_clear = ctk.CTkButton(row, text="Clear Data", width=80, height=24, fg_color="#e74c3c", hover_color="#c0392b", command=lambda p=pkg_name: self.clear_app_data(p))
        btn_clear.pack(side="right", padx=5)

    def launch_app(self, pkg_name):
        self.log(f"[*] Launching {pkg_name}...")
        def worker():
            self.run_adb_cmd(["shell", "monkey", "-p", pkg_name, "-c", "android.intent.category.LAUNCHER", "1"], log_output=False)
        threading.Thread(target=worker, daemon=True).start()

    def open_app_info(self, pkg_name):
        self.log(f"[*] Opened App Settings for: {pkg_name}")
        self.log("[-] NOTE: Android blocks wiping ONLY cache via ADB (without root).")
        self.log("[*] Tap 'Storage' -> 'Clear Cache' on your phone to safely clear it!")
        def worker():
            self.run_adb_cmd(["shell", "am", "start", "-a", "android.settings.APPLICATION_DETAILS_SETTINGS", "-d", f"package:{pkg_name}"], log_output=False)
        threading.Thread(target=worker, daemon=True).start()

    def clear_app_data(self, pkg_name):
        if not messagebox.askyesno("Confirm Clear Data", f"Are you sure you want to completely wipe all data for {pkg_name}?\nThis cannot be undone and is like reinstalling the app.", parent=self):
            return
            
        self.log(f"[*] Clearing data and cache for {pkg_name}...")
        def worker():
            out = self.run_adb_cmd(["shell", "pm", "clear", pkg_name])
            if "Success" in out:
                self.log(f"[+] Successfully cleared data for {pkg_name}.")
            else:
                self.log(f"[-] Failed to clear data for {pkg_name}.")
        threading.Thread(target=worker, daemon=True).start()

    def pull_photos(self):
        self.log("[*] Attempting to pull Camera photos...")
        def worker():
            # Usually DCIM/Camera
            out = self.run_adb_cmd(["shell", "ls", "-t", "/sdcard/DCIM/Camera/"], log_output=False)
            if "No such file" in out or not out:
                self.log("[-] Camera folder not found or empty.")
                return
            
            files = [f.strip() for f in out.split('\n') if (f.endswith('.jpg') or f.endswith('.png') or f.endswith('.mp4'))]
            if not files:
                self.log("[-] No images found.")
                return
                
            desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop', 'ADB_Toolkit_Downloads')
            os.makedirs(desktop_path, exist_ok=True)
            
            for f in files[:5]: # Take top 5
                remote_path = f"/sdcard/DCIM/Camera/{f}"
                self.log(f"[*] Pulling {f}...")
                self.run_adb_cmd(["pull", remote_path, desktop_path], log_output=False)
            
            self.log(f"[+] Downloaded {min(len(files), 5)} files to {desktop_path}")
            # Optionally open the folder
            os.startfile(desktop_path)
            
        threading.Thread(target=worker, daemon=True).start()

    # --- WIRELESS ADB METHODS ---
    
    def enable_tcpip(self):
        self.log("[*] Enabling TCP/IP mode on port 5555...")
        threading.Thread(target=lambda: self.run_adb_cmd(["tcpip", "5555"]), daemon=True).start()

    def find_device_ip(self):
        self.log("[*] Searching for wlan0 IP Address...")
        def worker():
            out = self.run_adb_cmd(["shell", "ip", "route"], log_output=False)
            ip = None
            for line in out.split('\n'):
                if 'wlan0' in line and 'src' in line:
                    parts = line.split('src')
                    if len(parts) > 1:
                        ip = parts[1].strip().split(' ')[0]
                        break
            if ip:
                self.log(f"[+] Found IP Address: {ip}")
                self.after(0, lambda: self.ip_entry.delete(0, 'end'))
                self.after(0, lambda: self.ip_entry.insert(0, ip))
            else:
                self.log("[-] Could not determine IP address automatically.")
        threading.Thread(target=worker, daemon=True).start()
        
    def connect_wifi(self):
        ip = self.ip_entry.get().strip()
        if not ip:
            self.log("[-] IP Address required.")
            return
        self.log(f"[*] Connecting to {ip}:5555...")
        threading.Thread(target=lambda: self.run_adb_cmd(["connect", f"{ip}:5555"]), daemon=True).start()
        
    def disconnect_wifi(self):
        ip = self.ip_entry.get().strip()
        if not ip:
             # Disconnect all if no IP specified
             self.run_adb_cmd(["disconnect"])
        else:
             self.run_adb_cmd(["disconnect", f"{ip}:5555"])
        self.refresh_devices()

    # --- FILE TRANSFER METHODS ---

    def push_file(self):
        filepath = filedialog.askopenfilename(title="Select File to Push")
        if not filepath:
            return
        self.log(f"[*] Pushing file '{os.path.basename(filepath)}' to /sdcard/Download/ ...")
        def worker():
            out = self.run_adb_cmd(["push", filepath, "/sdcard/Download/"])
            if "error" not in out.lower():
                self.log(f"[+] Successfully pushed to /sdcard/Download/")
        threading.Thread(target=worker, daemon=True).start()

    def install_apk(self):
        filepath = filedialog.askopenfilename(title="Select APK to Install", filetypes=[("APK Files", "*.apk")])
        if not filepath:
            return
        self.log(f"[*] Installing APK '{os.path.basename(filepath)}'...")
        def worker():
            out = self.run_adb_cmd(["install", filepath], timeout=60)
            if "Success" in out:
                self.log("[+] APK Installed Successfully!")
            else:
                self.log("[-] APK Installation Failed. Check logs.")
        threading.Thread(target=worker, daemon=True).start()

    def pull_file(self):
        remote_path = self.pull_path_entry.get().strip()
        if not remote_path:
            self.log("[-] Please enter a remote path to pull.")
            return
        desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop', 'ADB_Downloads')
        os.makedirs(desktop_path, exist_ok=True)
        self.log(f"[*] Pulling from '{remote_path}' to Desktop/ADB_Downloads...")
        def worker():
            out = self.run_adb_cmd(["pull", remote_path, desktop_path])
            if "error" not in out.lower():
                self.log(f"[+] Download complete: {desktop_path}")
        threading.Thread(target=worker, daemon=True).start()

    def toggle_auto_sync(self):
        self.auto_sync_enabled = not self.auto_sync_enabled
        if self.auto_sync_enabled:
            self.btn_auto_sync.configure(text="🔁 Auto-Sync: ON", fg_color="#27ae60")
            if not self.auto_sync_running:
                self.auto_sync_running = True
                threading.Thread(target=self.auto_sync_loop, daemon=True).start()
        else:
            self.btn_auto_sync.configure(text="🔄 Start Auto-Sync", fg_color="#e67e22")

    def auto_sync_loop(self):
        self.log("[*] Auto-Sync background listener started.")
        # Minimalist state storage for files tracked in the current session
        known_files = set()
        
        while self.auto_sync_enabled:
            remote_dir = self.sync_path_entry.get().strip()
            # If no device or missing dir, just wait
            if not remote_dir or not self.last_known_device:
                time.sleep(5)
                continue
                
            desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop', 'ADB_Downloads', 'AutoSync')
            os.makedirs(desktop_path, exist_ok=True)
            
            # Local inventory
            local_files = set(os.listdir(desktop_path))

            # Query remote inventory (using raw ls output, ignoring permission sub-directories usually ending in newline)
            out = self.run_adb_cmd(["shell", f"ls -A1 '{remote_dir}' 2>/dev/null"], log_output=False)
            if out:
                # Basic string filtering to get distinct filename blocks
                remote_files = set([line.strip() for line in out.split('\n') if line.strip() and '/' not in line])
                
                # The files that exist Remotely, BUT NOT Locally, AND we haven't already tried to sync them
                new_files = remote_files - local_files - known_files
                for nf in new_files:
                    if not self.auto_sync_enabled: break
                    full_remote = f"{remote_dir}/{nf}" if not remote_dir.endswith('/') else f"{remote_dir}{nf}"
                    self.log(f"[Sync] Pulling new file: {nf} ...")
                    pull_out = self.run_adb_cmd(["pull", full_remote, desktop_path], log_output=False)
                    if "error" not in pull_out.lower():
                        known_files.add(nf)
                        self.log(f"[+] Synced {nf} perfectly.")
                        
            time.sleep(5)
        self.auto_sync_running = False
        self.log("[-] Auto-Sync stopped.")

if __name__ == "__main__":
    app = ADBToolkitAppV2()
    app.mainloop()
