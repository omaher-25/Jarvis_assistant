
# JARVIS - Desktop AI Assistant

A voice- and text-controlled assistant for Windows that can browse the web, control your desktop, send WhatsApp messages, analyse images with deep learning, and answer questions via a local LLM.

[![GitHub Repo](https://img.shields.io/badge/GitHub-Repo-blue)](https://github.com/omaher-25/Jarvis_assistant)

---

## Features

> Highlights: core features are grouped and marked so you can quickly see what works out-of-the-box, what requires external services, and what is optional.

### Core (Immediate / Offline)

- **Text Command UI** — modern `CustomTkinter` GUI with a command textbox and log viewer.
- **Local TTS** — Windows SAPI + `pyttsx3` pipeline with fallbacks (PowerShell/gTTS) for spoken responses.
- **Basic Desktop Automation** — move/click automation to `close window` and `minimise window` commands.
- **Command Router** — `processCommand` maps typed/voice commands to internal actions and falls back to the local LLM when configured.

### Communication (Requires Internet / External Services)

- **WhatsApp Automation** — send instant messages and images using `pywhatkit` (requires WhatsApp Web logged in). Commands: `message <name> <text>`, `send image <name>`.
- **Web Automation & Search** — Open sites and perform smart searches on Google/YouTube/Wikipedia/Amazon/Maps/Spotify using the `open` and `search` commands.

### Vision & ML (Optional / Heavy Dependencies)

- **Screenshot + Clipboard Analysis** — snip-screen workflow using `ImageGrab` and classification via MobileNetV2.
- **Webcam Capture & Analyse** — capture photos from the webcam and run AI-based descriptions.
- **TensorFlow Models** — MobileNetV2 based image recognition (controlled by `enable_tensorflow`).

### Local LLM / Advanced AI (Optional)

- **Local LLM Integration** — Optional Ollama-style HTTP API client (`local_llm_stream`) to generate answers and code snippets; controlled by `enable_llm`.

### Developer / Utilities

- **Logging** — `jarvis_launcher.log` captures runtime activity and exceptions for troubleshooting.
- **Config Persistence** — `config.json` stores `contacts`, `features`, and `coords`; editable via the Settings UI.
- **Extensible Command Set** — Add new commands in `logic.py` and expose them through the GUI command box.

### Quick Feature Summary (Defaults)

- `contacts`: preloaded friendly names and numbers (editable via Settings)
- `features.enable_llm`: `true` (toggle in Settings)
- `features.enable_tensorflow`: `true` (toggle in Settings)
- `features.enable_camera`: `true` (toggle in Settings)
- `coords.close_x`: `1900`
- `coords.close_y`: `15`

---


---

## Project Layout

- `src/full_assistant/main.py` – entry point; starts the GUI and Jarvis thread
- `src/full_assistant/gui.py` – CustomTkinter UI, buttons, logging window, command box
- `src/full_assistant/logic.py` – speech, TTS, command routing, web/WhatsApp/vision helpers, LLM client
- `requirements.txt` – Python dependencies for the whole project

Run everything from the project root (`full_assistant`).

---

## Requirements

- Windows (TTS and automation code are Windows-focused)
- Python 3.10–3.13 (tested with 3.13)
- Microphone (for voice activation)
- Webcam (for photo capture feature)
- Internet connection (speech recognition, web, WhatsApp, gTTS, TensorFlow model download)
- Optional: Local LLM server compatible with the Ollama HTTP API on `http://localhost:11434` (e.g. `gemma2:2b`)

> Note: `tensorflow` and `opencv-python` are large packages and may take time to install.

---

## Installation (Windows)

1. **Clone the repository**

     ```powershell
     git clone https://github.com/omaher-25/Jarvis_assistant.git
     cd full_assistant
     ```

2. **Create and activate a virtual environment**

     ```powershell
     python -m venv env
     .\env\Scripts\activate
     ```

3. **Install dependencies**

     From the project root (where `requirements.txt` lives):

     ```powershell
     pip install --upgrade pip
     pip install -r requirements.txt
     ```

     If you hit TensorFlow install issues, try:

     - Ensuring you are on a 64‑bit Python
     - Updating `pip`, `setuptools`, and `wheel`
     - Installing a TensorFlow version compatible with your Python if needed

### Student Quickstart (lightweight)

If you want to run Jarvis for development or demonstration without heavy packages like TensorFlow or OpenCV, use the lightweight requirements and disable heavy features in `config.json`.

1. Create and activate a virtual environment:

```powershell
python -m venv env
.\env\Scripts\activate
```

2. Install the lightweight dependencies:

```powershell
pip install --upgrade pip
pip install -r requirements-lite.txt
```

3. Disable heavy features (optional): open `config.json` and set `enable_tensorflow` and `enable_llm` to `false`.

4. Run the GUI:

```powershell
.\env\Scripts\activate
pythonw src/full_assistant/main.py
```

This mode lets you test GUI, TTS, basic web automation, and WhatsApp features without installing large ML libraries.

---

## Running JARVIS

From the project root, double-click `run_jarvis.vbs` (Windows) to start the GUI without a console window.

### Manual Run (if needed)
If the VBS file doesn't work, activate manually:

```powershell
.\env\Scripts\activate
pythonw src/full_assistant/main.py
```

This will open the Jarvis GUI and automatically start the background Jarvis thread.

---

## Using the Assistant

### Voice mode

- Jarvis continuously listens for the hotword: `jarvis`.
- After you say "Jarvis", speak your command within a few seconds.
- Example phrases:
    - "Jarvis open YouTube"
    - "Jarvis search latest AI news on Google"
    - "Jarvis play lo-fi beats on YouTube"
    - "Jarvis send image to me"

### Text mode (GUI)

- Use the input box at the bottom of the window.
- Type a command and press Enter.
- Examples:
    - `open youtube`
    - `search cats on wikipedia`
    - `play lo-fi beats`
    - `capture image`
    - `analyse` (analyse a snipped screenshot)

---

## Built‑in Commands

The `processCommand` function in `logic.py` currently supports:

- `open <site>` – open a website (`open youtube`, `open chat gpt`)
- `search <query> on <site>` – smart search on Google/YouTube/Wikipedia/Amazon/Maps/Spotify
- `play <something>` – play a YouTube video via pywhatkit
- `message <name> <text>` – send instant WhatsApp messages 
- `send image <name>` – snip an area and WhatsApp it to a contact
- `analyse` / `analyse the image` – snip an area and run image classification
- `capture image` / `capture` – capture from webcam and analyse
- `close window` – move mouse and close the active window
- `minimise window` – move mouse and minimise the active window
- `shutdown` / `shut down` – stop Jarvis and exit the app

If a command does not match any of the above, it is forwarded to the local LLM via `local_llm_stream`, which can:

- Speak the answer back (short textual answers)
- Or, for code/programming queries, generate code and open it in Notepad (`code.txt`).

> Contacts for WhatsApp can be defined directly in `logic.py`. Add the numbers before using this feature.

---

## Settings (Configurable)

Jarvis exposes a small settings UI and a persistent `config.json` for storing user-configurable options. You can open the Settings from the main GUI by clicking the ⚙ Settings button.

- `contacts`: A mapping of friendly names to phone numbers (must include country code, e.g. `+1234567890`). These names are used by the `message` and `send image` commands.
- `features`: Feature toggles (boolean) that enable/disable optional subsystems:
    - `enable_llm` (default: `true`) — enable the local LLM integration used for fallback Q&A and code generation.
    - `enable_tensorflow` (default: `true`) — enable TensorFlow image analysis features (MobileNetV2).
    - `enable_camera` (default: `true`) — allow webcam capture and camera-based features.
- `llm`: LLM behavior and response configuration (configure how the assistant responds):
  - `model` (default: `"gemma2:2b"`) — name of the local LLM model to use (must be available in Ollama).
  - `temperature` (default: `0.5`, range 0.0–1.0) — controls randomness/creativity. Lower = more deterministic, higher = more random.
  - `max_tokens` (default: `512`) — maximum response length in tokens (limits how long answers can be).
  - `system_prompt` (default: custom instructions) — system instructions that define assistant behavior, personality, and response style.

All settings are saved to `config.json` in the project root. Use the Settings window to add/edit/delete contacts, toggle features, and customize LLM response behavior. For a full walkthrough see `SETTINGS_GUIDE.md`.

The assistant talks to a local model using an Ollama-style HTTP API:

- Endpoint: `POST http://localhost:11434/api/generate`
- Default model: `gemma2:2b`

To enable this:

1. Install and run an Ollama‑compatible server.
2. Pull or make available a `gemma2:2b` (or similar) model.
3. Keep the server running while you use Jarvis.

If the LLM server is unavailable, Jarvis will log the error and continue working for non‑LLM commands.

---

## Troubleshooting

- **`pip install -r requirements.txt` fails**
    - Make sure you are using 64‑bit Python and a supported version for TensorFlow.
    - Run `pip install --upgrade pip setuptools wheel` and retry.
- **Microphone errors**
    - Check your default recording device in Windows.
    - Install `pyaudio` (or the appropriate backend) if speech recognition complains.
- **Camera errors**
    - Ensure no other app is using the webcam.
    - Confirm that `cv2.VideoCapture(0)` works in a simple test script.
- **WhatsApp automation**
    - You must be logged in to WhatsApp Web in your default browser.
    - pywhatkit may open browser tabs and wait a few seconds to send.

---

## Contributing

Suggestions, bug reports, and pull requests are welcome. Useful areas to contribute:

- Adding more robust error handling and status reporting in the GUI
- Extending the command set (e.g., media control, system utilities)
- Improving TensorFlow model loading (caching, lighter models)
- Making contact lists and configuration user‑editable instead of hard‑coded

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.