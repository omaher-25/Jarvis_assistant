import logic

import threading
import traceback
import customtkinter as tk
import tkinter as tk_native
from tkinter import messagebox
import os
import subprocess
from logic import jarvis_main
from logic import log
from logic import log_queue
from logic import stop_app
from logic import capture_photo
from logic import get_clipboard_image
from logic import processCommand
from logic import save_config
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


def open_settings_window():
    """Open settings window for managing contacts and configuration."""
    settings_window = tk.CTkToplevel(root)
    settings_window.title("Settings")
    settings_window.geometry("700x500")
    settings_window.resizable(False, False)
    settings_window.grab_set()  # Make modal
    
    # Create tabview
    tabview = tk.CTkTabview(settings_window, width=680, height=450)
    tabview.pack(padx=10, pady=10, fill="both", expand=True)
    
    # Add tabs
    contacts_tab = tabview.add("Contacts")
    features_tab = tabview.add("Features")
    coords_tab = tabview.add("Coordinates")
    
    # ===== CONTACTS TAB =====
    contacts_frame = tk.CTkFrame(contacts_tab)
    contacts_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Title
    tk.CTkLabel(contacts_frame, text="Manage Contacts", font=tk.CTkFont(size=16, weight="bold")).pack(pady=10)
    
    # Contact list frame with scrollbar
    list_frame = tk.CTkFrame(contacts_frame)
    list_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Headers
    headers_frame = tk.CTkFrame(list_frame, fg_color="transparent")
    headers_frame.pack(fill="x", padx=5, pady=(5, 0))
    tk.CTkLabel(headers_frame, text="Name", font=tk.CTkFont(weight="bold"), width=150, anchor="w").pack(side="left", padx=5)
    tk.CTkLabel(headers_frame, text="Phone Number", font=tk.CTkFont(weight="bold"), width=200, anchor="w").pack(side="left", padx=5)
    tk.CTkLabel(headers_frame, text="Actions", font=tk.CTkFont(weight="bold"), width=100, anchor="center").pack(side="left", padx=5)
    
    # Scrollable frame for contacts
    contacts_scrollframe = tk.CTkScrollableFrame(list_frame, height=200)
    contacts_scrollframe.pack(fill="both", expand=True, padx=5, pady=5)
    
    def refresh_contacts_list():
        """Refresh the contacts display."""
        for widget in contacts_scrollframe.winfo_children():
            widget.destroy()
        
        contacts = logic.CONFIG.get("contacts", {})
        for name, number in contacts.items():
            contact_frame = tk.CTkFrame(contacts_scrollframe, fg_color="transparent")
            contact_frame.pack(fill="x", pady=2)
            
            tk.CTkLabel(contact_frame, text=name, width=150, anchor="w").pack(side="left", padx=5)
            tk.CTkLabel(contact_frame, text=number, width=200, anchor="w").pack(side="left", padx=5)
            
            actions_frame = tk.CTkFrame(contact_frame, fg_color="transparent", width=100)
            actions_frame.pack(side="left", padx=5)
            
            def make_delete_callback(contact_name):
                return lambda: delete_contact(contact_name)
            
            def make_edit_callback(contact_name):
                return lambda: edit_contact(contact_name)
            
            tk.CTkButton(actions_frame, text="Edit", width=60, command=make_edit_callback(name)).pack(side="left", padx=2)
            tk.CTkButton(actions_frame, text="Delete", width=60, fg_color="#EF4444", hover_color="#DC2626", 
                        command=make_delete_callback(name)).pack(side="left", padx=2)
    
    def delete_contact(name):
        """Delete a contact."""
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{name}'?"):
            if "contacts" in logic.CONFIG:
                logic.CONFIG["contacts"].pop(name, None)
                save_config()
                refresh_contacts_list()
                log(f"Deleted contact: {name}")
    
    def edit_contact(name):
        """Edit an existing contact."""
        contacts = logic.CONFIG.get("contacts", {})
        current_number = contacts.get(name, "")
        
        edit_window = tk.CTkToplevel(settings_window)
        edit_window.title(f"Edit Contact: {name}")
        edit_window.geometry("400x280")
        edit_window.grab_set()
        
        tk.CTkLabel(edit_window, text="Name:", font=tk.CTkFont(size=12)).pack(pady=(20, 5))
        name_entry = tk.CTkEntry(edit_window, width=300)
        name_entry.insert(0, name)
        name_entry.pack(pady=5)
        
        tk.CTkLabel(edit_window, text="Phone Number (with country code):", font=tk.CTkFont(size=12)).pack(pady=(10, 5))
        number_entry = tk.CTkEntry(edit_window, width=300, placeholder_text="+1234567890")
        number_entry.insert(0, current_number)
        number_entry.pack(pady=5)
        
        def save_edit():
            new_name = name_entry.get().strip()
            new_number = number_entry.get().strip()
            
            if not new_name or not new_number:
                messagebox.showerror("Error", "Both name and number are required!")
                return
            
            if not new_number.startswith("+"):
                messagebox.showerror("Error", "Phone number must start with + and country code!")
                return
            
            # Remove old entry if name changed
            if new_name != name and "contacts" in logic.CONFIG:
                logic.CONFIG["contacts"].pop(name, None)
            
            if "contacts" not in logic.CONFIG:
                logic.CONFIG["contacts"] = {}
            
            logic.CONFIG["contacts"][new_name] = new_number
            save_config()
            refresh_contacts_list()
            edit_window.destroy()
            log(f"Updated contact: {new_name} -> {new_number}")
        
        # Save button with larger size and more padding
        save_button = tk.CTkButton(edit_window, text="Save Changes", command=save_edit, width=250, height=40,
                                  font=tk.CTkFont(size=14, weight="bold"))
        save_button.pack(pady=25)
        
        # Bind Enter key to both entry fields
        name_entry.bind("<Return>", lambda e: save_edit())
        number_entry.bind("<Return>", lambda e: save_edit())
        
        # Focus on name entry
        name_entry.focus()
    
    def add_contact():
        """Add a new contact."""
        add_window = tk.CTkToplevel(settings_window)
        add_window.title("Add Contact")
        add_window.geometry("400x280")
        add_window.grab_set()
        
        tk.CTkLabel(add_window, text="Name:", font=tk.CTkFont(size=12)).pack(pady=(20, 5))
        name_entry = tk.CTkEntry(add_window, width=300, placeholder_text="friend, mom, dad, etc.")
        name_entry.pack(pady=5)
        
        tk.CTkLabel(add_window, text="Phone Number (with country code):", font=tk.CTkFont(size=12)).pack(pady=(10, 5))
        number_entry = tk.CTkEntry(add_window, width=300, placeholder_text="+1234567890")
        number_entry.pack(pady=5)
        
        def save_new():
            name = name_entry.get().strip().lower()
            number = number_entry.get().strip()
            
            if not name or not number:
                messagebox.showerror("Error", "Both name and number are required!")
                return
            
            if not number.startswith("+"):
                messagebox.showerror("Error", "Phone number must start with + and country code!")
                return
            
            if "contacts" not in logic.CONFIG:
                logic.CONFIG["contacts"] = {}
            
            if name in logic.CONFIG["contacts"]:
                if not messagebox.askyesno("Confirm", f"Contact '{name}' already exists. Overwrite?"):
                    return
            
            logic.CONFIG["contacts"][name] = number
            save_config()
            refresh_contacts_list()
            add_window.destroy()
            log(f"Added contact: {name} -> {number}")
        
        # Add button with larger size and more padding
        add_button = tk.CTkButton(add_window, text="Add Contact", command=save_new, width=250, height=40,
                                 font=tk.CTkFont(size=14, weight="bold"),
                                 fg_color="#10B981", hover_color="#059669")
        add_button.pack(pady=25)
        
        # Bind Enter key to both entry fields
        name_entry.bind("<Return>", lambda e: save_new())
        number_entry.bind("<Return>", lambda e: save_new())
        
        # Focus on name entry
        name_entry.focus()
    
    # Add contact button
    tk.CTkButton(contacts_frame, text="+ Add Contact", command=add_contact, width=200, 
                fg_color="#10B981", hover_color="#059669").pack(pady=10)
    
    refresh_contacts_list()
    
    # ===== FEATURES TAB =====
    features_frame = tk.CTkFrame(features_tab)
    features_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    tk.CTkLabel(features_frame, text="Feature Toggles", font=tk.CTkFont(size=16, weight="bold")).pack(pady=20)
    
    features = logic.CONFIG.get("features", {})
    
    llm_var = tk.BooleanVar(value=features.get("enable_llm", True))
    tf_var = tk.BooleanVar(value=features.get("enable_tensorflow", True))
    cam_var = tk.BooleanVar(value=features.get("enable_camera", True))
    
    tk.CTkCheckBox(features_frame, text="Enable LLM (Local Language Model)", 
                   variable=llm_var, font=tk.CTkFont(size=13)).pack(pady=10, padx=20, anchor="w")
    tk.CTkCheckBox(features_frame, text="Enable TensorFlow (Image Analysis)", 
                   variable=tf_var, font=tk.CTkFont(size=13)).pack(pady=10, padx=20, anchor="w")
    tk.CTkCheckBox(features_frame, text="Enable Camera", 
                   variable=cam_var, font=tk.CTkFont(size=13)).pack(pady=10, padx=20, anchor="w")
    
    def save_features():
        if "features" not in logic.CONFIG:
            logic.CONFIG["features"] = {}
        
        logic.CONFIG["features"]["enable_llm"] = llm_var.get()
        logic.CONFIG["features"]["enable_tensorflow"] = tf_var.get()
        logic.CONFIG["features"]["enable_camera"] = cam_var.get()
        
        if save_config():
            messagebox.showinfo("Success", "Features updated successfully!")
            log("Features configuration updated")
    
    tk.CTkButton(features_frame, text="Save Features", command=save_features, width=200).pack(pady=20)
    
    # ===== COORDINATES TAB =====
    coords_frame = tk.CTkFrame(coords_tab)
    coords_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    tk.CTkLabel(coords_frame, text="Window Close Coordinates", font=tk.CTkFont(size=16, weight="bold")).pack(pady=20)
    tk.CTkLabel(coords_frame, text="Set the screen coordinates for the close button position", 
                font=tk.CTkFont(size=11)).pack(pady=5)
    
    coords = logic.CONFIG.get("coords", {})
    
    tk.CTkLabel(coords_frame, text="Close Button X Position:", font=tk.CTkFont(size=12)).pack(pady=(20, 5))
    close_x_entry = tk.CTkEntry(coords_frame, width=200, placeholder_text="1900")
    close_x_entry.insert(0, str(coords.get("close_x", 1900)))
    close_x_entry.pack(pady=5)
    
    tk.CTkLabel(coords_frame, text="Close Button Y Position:", font=tk.CTkFont(size=12)).pack(pady=(20, 5))
    close_y_entry = tk.CTkEntry(coords_frame, width=200, placeholder_text="15")
    close_y_entry.insert(0, str(coords.get("close_y", 15)))
    close_y_entry.pack(pady=5)
    
    def save_coords():
        try:
            close_x = int(close_x_entry.get().strip())
            close_y = int(close_y_entry.get().strip())
            
            if "coords" not in logic.CONFIG:
                logic.CONFIG["coords"] = {}
            
            logic.CONFIG["coords"]["close_x"] = close_x
            logic.CONFIG["coords"]["close_y"] = close_y
            
            if save_config():
                messagebox.showinfo("Success", "Coordinates updated successfully!")
                log(f"Coordinates updated: close_x={close_x}, close_y={close_y}")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid integer values!")
    
    tk.CTkButton(coords_frame, text="Save Coordinates", command=save_coords, width=200).pack(pady=20)
    
    # Close button at bottom — improved visibility and keyboard shortcuts
    bottom_frame = tk.CTkFrame(settings_window, fg_color="transparent")
    bottom_frame.pack(fill="x", padx=20, pady=(10, 15))
    close_btn = tk.CTkButton(bottom_frame, text="Close Settings  (Esc)", command=settings_window.destroy,
                             width=220, height=40, font=tk.CTkFont(size=13, weight="bold"),
                             fg_color="#374151", hover_color="#1F2937")
    close_btn.pack(pady=6)
    # Bind Escape and Ctrl+W to close the settings window for quick keyboard access
    try:
        settings_window.bind("<Escape>", lambda e: settings_window.destroy())
        settings_window.bind("<Control-w>", lambda e: settings_window.destroy())
    except Exception:
        pass


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
    button_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
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
    settings_button = tk.CTkButton(button_frame, text="⚙ Settings", command=open_settings_window, 
                                   fg_color="#6366F1", hover_color="#4F46E5")
    settings_button.grid(row=0, column=4, padx=5, pady=10, sticky="ew")

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