
# JARVIS - Desktop AI Assistant

A voice- and text-controlled assistant for Windows that can browse the web, control your desktop, send WhatsApp messages, analyse images with deep learning, and answer questions via a local LLM.

[![GitHub Repo](https://img.shields.io/badge/GitHub-Repo-blue)](https://github.com/omaher-25/Jarvis_assistant)

---

## Features

- Voice hotword "Jarvis" with continuous listening
- Text command box in a modern CustomTkinter GUI
- Local TTS pipeline (Win32 SAPI, pyttsx3, PowerShell, gTTS fallback)
- Web automation: open sites, search Google / YouTube / Wikipedia / Amazon / Maps / Spotify
- WhatsApp automation for instant messages and image sending (via pywhatkit)
- Desktop control: close and minimise the active window
- Image understanding using MobileNetV2 (TensorFlow/Keras)
- Screenshot + clipboard analysis workflow
- Photo capture from webcam and AI-based description
- Optional local LLM integration (Ollama-style HTTP endpoint) for general Q&A and code generation

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
     git clone <your-repository-url>
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
- `message <name> <text>` – send instant WhatsApp messages (contacts hard-coded in `logic.py`)
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

## Local LLM Integration

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