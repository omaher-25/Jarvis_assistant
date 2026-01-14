import logic

import threading
import traceback
import customtkinter as tk
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
    _tk_root = root
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

    root.after(300, start_jarvis)
    root.after(100, process_log_queue)
    root.protocol("WM_DELETE_WINDOW", stop_app)

    log("Launcher GUI starting mainloop")
    try:
        root.mainloop()
    except Exception:
        log("Exception in GUI mainloop:\n" + traceback.format_exc())

    log("Launcher GUI exited")