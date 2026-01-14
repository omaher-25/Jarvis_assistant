import logic

import threading
import traceback
import customtkinter as tk
import tkinter as tk_native
import os
import subprocess
from logic import jarvis_main
from logic import log
from logic import log_queue
from logic import stop_app
from logic import capture_photo
from logic import get_clipboard_image
from logic import processCommand
import queue


def _run_jarvis_safe():
    """Run jarvis_main() and log any exceptions."""
    try:
        log("Starting jarvis_main()")
        jarvis_main()
    except SystemExit:
        log("jarvis_main called SystemExit")
        raise
    except Exception:
        log("Exception in jarvis_main:\n" + traceback.format_exc())

def start_jarvis():
    """Start jarvis_main() in a background daemon thread."""
    try:
        t = threading.Thread(target=_run_jarvis_safe, daemon=True, name="JarvisThread")
        t.start()
        status_var.set("Status: Running")
        start_button.configure(state="disabled")
        stop_button.configure(state="normal")
        log("Jarvis thread started")
    except Exception:
        log("start_jarvis failed:\n" + traceback.format_exc())

def process_log_queue():
    try:
        while not log_queue.empty():
            message = log_queue.get_nowait()
            log_widget.configure(state='normal')
            log_widget.insert('end', message)
            log_widget.see('end')
            log_widget.configure(state='disabled')
    except queue.Empty:
        pass
    root.after(100, process_log_queue)

def run_gui():
    """Run the GUI."""
    # --- GUI Setup ---
    tk.set_appearance_mode("Dark")
    tk.set_default_color_theme("blue")

    global root
    root = tk.CTk()
    logic._tk_root = root  # Share the root with logic.py for shutdown
    root.title("Jarvis")
    root.geometry("550x450")
    root.resizable(False, False)

    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=1)

    # --- Top Frame (Title and Status) ---
    top_frame = tk.CTkFrame(root, fg_color="transparent")
    top_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
    top_frame.grid_columnconfigure(0, weight=1)

    title_label = tk.CTkLabel(top_frame, text="JARVIS", font=tk.CTkFont(size=24, weight="bold"))
    title_label.grid(row=0, column=0, sticky="w")

    global status_var
    status_var = tk.StringVar(value="Status: Stopped")
    status_label = tk.CTkLabel(top_frame, textvariable=status_var, font=tk.CTkFont(size=12))
    status_label.grid(row=1, column=0, sticky="w")

    # --- Command Entry ---
    def execute_command():
        command_text = command_entry.get()
        log(f"Command: {command_text}")
        processCommand(command_text)
        command_entry.delete(0, tk.END) # Clear the entry after execution
    command_entry = tk.CTkEntry(root, placeholder_text="Enter command")
    command_entry.grid(row=3, column=0, padx=20, pady=(10, 10), sticky="ew")

    # --- Button Frame ---
    button_frame = tk.CTkFrame(root)
    button_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
    button_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
    command_entry.bind("<Return>", lambda event: execute_command()) # Bind Enter key to execute_command
 
    global start_button, stop_button
    start_button = tk.CTkButton(button_frame, text="Start", command=start_jarvis, state="normal")
    start_button.grid(row=0, column=0, padx=5, pady=10, sticky="ew")
    stop_button = tk.CTkButton(button_frame, text="Stop", command=stop_app, state="disabled")
    stop_button.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
    analyse_button = tk.CTkButton(button_frame, text="Analyse Image", command=get_clipboard_image)
    analyse_button.grid(row=0, column=2, padx=5, pady=10, sticky="ew")
    capture_image_button = tk.CTkButton(button_frame, text="Capture Photo", command=capture_photo)
    capture_image_button.grid(row=0, column=3, padx=5, pady=10, sticky="ew")

    # --- Log Viewer ---
    global log_widget
    log_widget = tk.CTkTextbox(root, state='disabled', font=("Consolas", 11))
    log_widget.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="nsew")

    # --- Stylish Status Bar (enhanced) ---
    status_frame = tk.CTkFrame(root, fg_color="#0b1220", corner_radius=8)
    status_frame.grid(row=4, column=0, padx=12, pady=(8, 12), sticky="ew")
    status_frame.grid_columnconfigure(0, weight=1)

    status_inner = tk.CTkFrame(status_frame, fg_color="transparent")
    status_inner.grid(row=0, column=0, padx=12, pady=10, sticky="ew")
    status_inner.grid_columnconfigure((0,1,2,3,4,5,6,7), weight=1)

    def dot_btn(color):
        return tk.CTkButton(status_inner, text="", width=18, height=18, fg_color=color, corner_radius=9, state="disabled")

    # Create components
    llm_dot = dot_btn("#9CA3AF")
    llm_label = tk.CTkLabel(status_inner, text="LLM: ?", font=tk.CTkFont(size=11, weight="bold"), text_color="#E5E7EB")

    sep1 = tk.CTkLabel(status_inner, text="|")

    tf_dot = dot_btn("#9CA3AF")
    tf_label = tk.CTkLabel(status_inner, text="TensorFlow: ?", font=tk.CTkFont(size=11, weight="bold"), text_color="#E5E7EB")

    sep2 = tk.CTkLabel(status_inner, text="|")

    cam_dot = dot_btn("#9CA3AF")
    cam_label = tk.CTkLabel(status_inner, text="Camera: ?", font=tk.CTkFont(size=11, weight="bold"), text_color="#E5E7EB")

    sep3 = tk.CTkLabel(status_inner, text="|")

    contacts_dot = dot_btn("#60A5FA")
    contacts_label = tk.CTkLabel(status_inner, text="Contacts: ?", font=tk.CTkFont(size=11, weight="bold"), text_color="#E5E7EB")

    # Layout
    llm_dot.grid(row=0, column=0, sticky="w")
    llm_label.grid(row=0, column=1, sticky="w", padx=(6,12))
    sep1.grid(row=0, column=2, sticky="w")
    tf_dot.grid(row=0, column=3, sticky="w", padx=(12,0))
    tf_label.grid(row=0, column=4, sticky="w", padx=(6,12))
    sep2.grid(row=0, column=5, sticky="w")
    cam_dot.grid(row=0, column=6, sticky="w", padx=(12,0))
    cam_label.grid(row=0, column=7, sticky="w", padx=(6,12))
    sep3.grid(row=0, column=8, sticky="w")
    contacts_dot.grid(row=0, column=9, sticky="w", padx=(12,0))
    contacts_label.grid(row=0, column=10, sticky="w", padx=(6,0))

    def refresh_status():
        try:
            cfg = logic.CONFIG if hasattr(logic, 'CONFIG') else {}
            features = cfg.get('features', {}) if cfg else {}
            contacts = cfg.get('contacts', {}) if cfg else {}

            def color_on(b):
                return "#34D399" if b else "#EF4444"

            llm_enabled = features.get('enable_llm', True)
            tf_enabled = features.get('enable_tensorflow', True)
            cam_enabled = features.get('enable_camera', True)

            llm_dot.configure(fg_color=color_on(llm_enabled))
            llm_label.configure(text=f"LLM: {'ON' if llm_enabled else 'OFF'}")

            tf_dot.configure(fg_color=color_on(tf_enabled))
            tf_label.configure(text=f"TensorFlow: {'ON' if tf_enabled else 'OFF'}")

            cam_dot.configure(fg_color=color_on(cam_enabled))
            cam_label.configure(text=f"Camera: {'ON' if cam_enabled else 'OFF'}")

            contacts_count = len(contacts) if isinstance(contacts, dict) else 0
            contacts_label.configure(text=f"Contacts: {contacts_count} loaded")
        except Exception:
            pass
        root.after(1400, refresh_status)

    # Tooltip showing config path and status summary
    tooltip = None
    def show_tooltip(_event=None):
        nonlocal tooltip
        try:
            if tooltip:
                return
            cfg_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')), 'config.json')
            cfg = logic.CONFIG if hasattr(logic, 'CONFIG') else {}
            features = cfg.get('features', {}) if cfg else {}
            lines = [f"Config: {cfg_path}", f"LLM: {'ON' if features.get('enable_llm', True) else 'OFF'}", f"TF: {'ON' if features.get('enable_tensorflow', True) else 'OFF'}", f"Camera: {'ON' if features.get('enable_camera', True) else 'OFF'}"]
            tooltip = tk_native.Toplevel(root)
            tooltip.wm_overrideredirect(True)
            tooltip.attributes('-topmost', True)
            x = root.winfo_pointerx() + 12
            y = root.winfo_pointery() + 12
            tooltip.geometry(f"+{x}+{y}")
            lbl = tk_native.Label(tooltip, text="\n".join(lines), justify='left', bg='#0b1220', fg='white', bd=1, padx=8, pady=6, font=(None, 9))
            lbl.pack()
        except Exception:
            pass

    def hide_tooltip(_event=None):
        nonlocal tooltip
        try:
            if tooltip:
                tooltip.destroy()
                tooltip = None
        except Exception:
            tooltip = None

    def open_config(_event=None):
        try:
            cfg_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')), 'config.json')
            subprocess.Popen(['notepad.exe', cfg_path])
        except Exception:
            log('Failed to open config.json')

    status_inner.bind('<Enter>', show_tooltip)
    status_inner.bind('<Leave>', hide_tooltip)
    status_inner.bind('<Button-1>', open_config)

    refresh_status()

    root.after(300, start_jarvis)
    root.after(100, process_log_queue)
    root.protocol("WM_DELETE_WINDOW", stop_app)

    log("Launcher GUI starting mainloop")
    try:
        root.mainloop()
    except Exception:
        log("Exception in GUI mainloop:\n" + traceback.format_exc())

    log("Launcher GUI exited")