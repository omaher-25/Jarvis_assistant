import sys
import os
import pyttsx3
import pygame
import subprocess
import queue
import gtts as gTTS
import cv2
import keyboard
import pyautogui as auto
import pywhatkit as kit
from PIL import ImageGrab
import speech_recognition as sr
import uuid
import requests
import time
import webbrowser


# --- Logging Setup ---
LOG_PATH = os.path.join(os.path.expanduser("~"), "jarvis_launcher.log") 
log_queue = queue.Queue()


def log(msg: str):
    """Append timestamped message to log file and queue for GUI."""
    try:
        log_message = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n"
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(log_message)
        log_queue.put(log_message)

    except Exception:
        pass


class LogWriter:
    def write(self, message):
        log(message)
    def flush(self):
        pass


if getattr(sys, 'frozen', False):
    sys.stdout = LogWriter()
    sys.stderr = LogWriter()
_tk_root = None
try:
    engine = pyttsx3.init('sapi5')
    engine.setProperty("rate", 165)
    engine_ok = True
except Exception as e:
    log(f"pyttsx3 init with sapi5 failed: {e}")
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 165)
        engine_ok = True
    except Exception as e2:
        log(f"pyttsx3 init failed: {e2}")
        engine = None
        engine_ok = False
pygame_inited = False


def init_pygame_mixer():
    global pygame_inited
    if not pygame_inited:
        try:
            pygame.mixer.init()
            pygame_inited = True
            log("Pygame mixer initialized successfully.")
        except Exception as e:
            log(f"pygame mixer init failed: {e}")
            pygame_inited = False
try:
    import win32com.client as win32
    _HAS_WIN32 = True
except Exception:
    _HAS_WIN32 = False


def speak(text_to_speak: str):
    if not text_to_speak:
        return

    # --- List of TTS engines to try in order ---
    tts_methods = [
        speak_win32,
        speak_pyttsx3,
        speak_powershell,
        speak_gtts
    ]

    for method in tts_methods:
        try:
            method(text_to_speak)
            return  # Success, so exit the function
        except Exception as e:
            log(f"[speak] {method.__name__} failed: {e}")

    log("[speak] All TTS methods failed.")


def speak_win32(text):
    if _HAS_WIN32:
        voice = win32.Dispatch("SAPI.SpVoice")
        voice.Speak(str(text))
    else:
        raise Exception("win32com not available")


def speak_pyttsx3(text):
    if engine_ok and engine:
        engine.say(text)
        engine.runAndWait()
    else:
        raise Exception("pyttsx3 not available")


def speak_powershell(text):
    escaped = text.replace('"', '`"').replace("'", "`'")
    ps_cmd = f'Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{escaped}")'
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True, timeout=12)


def speak_gtts(text):
    tmp = None
    try:
        tts = gTTS(text=str(text), lang='en')
        tmp = f"tmp_tts_{uuid.uuid4().hex}.mp3"
        tts.save(tmp)
        if not pygame.mixer.get_init():
            init_pygame_mixer()
        if pygame.mixer.get_init():
            pygame.mixer.music.load(tmp)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(50)
            pygame.mixer.music.stop()
        else:
            raise Exception("Pygame mixer could not be initialized.")
    finally:
        if tmp and os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass


def local_llm_stream(prompt, model="gemma2:2b"):
    try:
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": model,
            "prompt": f'''Follow these rules:
                     1. Act as you are a personal assistant having name is 'Jarvis'.
                     2. Do not use emojis or any special characters in your answers.
                     3. Do not add markdown unless I say.
                     4. When I ask for code or program, output only the code do not include any unnecessary text.
                     5. Be direct and factual.
                     6. Give the answer as short as possible, also try to answer in one line if possible.
                     7. use numbers to list things in your answer if there. 
                     8. call me 'sir' if you need to ask something.
                     Now my question: {prompt}''',
            "stream": False
        }
        response = requests.post(url, json=payload)
        data = response.json()
        text = data.get("response", "")
        if "code" in prompt.lower() or "program" in prompt.lower():
            save_to_notepad(text.strip())
            time.sleep(5)
            os.remove("code.txt")
        else:
            log(text.strip())
            not_include = [1,2,3,4,5,6,7,8,9,0]
            for i in not_include:
                if str(i) in text:
                    text = text.replace(str(i),"")
            speak(text.strip()) 
    except Exception as e:
        log(f"Exception in local_llm_stream: {e}")


def save_to_notepad(text, filename="code.txt"):
    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(text)
        speak("program generated...")
        log("program generated...")    
        subprocess.Popen(['notepad.exe',filename ])
        time.sleep(1) 
    except Exception as e:
        log(f" Error: {e}")
       

def capture_photo():
    try:
        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            log("Error: Could not open camera.")
            speak("Sorry, I couldn't access the camera.")
            return

        ret, frame = cam.read()
        if ret:
            photo_path = "photo.jpg"
            cv2.imwrite(photo_path, frame)
            speak("Analyzing the captured image.")
            log(f"Captured image saved as {photo_path}")
            aianalyser(photo_path)
        else:
            log("Failed to capture image.")
            speak("Sorry, I couldn't capture a photo.")
    except Exception as e:
        log(f"Camera error: {e}")
        speak("An unexpected error occurred with the camera.")
    finally:
        if 'cam' in locals() and cam.isOpened():
            cam.release()
        cv2.destroyAllWindows()


def stop_app():
    """Stop the whole application."""
    try:
        speak("Jarvis is shutting down. Goodbye Captain!")
        time.sleep(0.5)
        if pygame.get_init():
            pygame.quit()
        if _tk_root:
            log("Destroying Tkinter root window.")
            _tk_root.destroy()
        sys.exit(0)
    except Exception as e:
        log(f"Exception during shutdown: {e}")
        os._exit(1)


def open_website(site_name: str):
    site_name = site_name.lower().replace("open", "").strip()
    
    special_sites = {
        "chat gpt": "https://chat.openai.com"
    }

    if site_name in special_sites:
        site_url = special_sites[site_name]
        speak(f"Opening {site_name}")
    else:
        site_url = f"https://www.{site_name.replace(' ', '')}.com"
        speak(f"Opening {site_name}")
        
    try:
        webbrowser.open(site_url)
        log(f"Opening {site_url}")
    except Exception as e:
        log(f"Failed to open {site_name}: {e}")
        speak(f"Sorry, I couldn't open {site_name}")

      
def search_on_website(site: str):
    site = site.lower().strip()

    # Extract query early
    cleaned = site.replace("search", "", 1).strip()

    search_patterns = {
        "spotify": "https://open.spotify.com/search/{}",
        "map": "https://www.google.com/maps/place/{}",
        "youtube": "https://www.youtube.com/results?search_query={}",
        "amazon": "https://www.amazon.in/s?k={}",
        "wikipedia": "https://en.wikipedia.org/wiki/{}",
    }

    # 1. Check for known site searches
    for keyword, url_template in search_patterns.items():
        if keyword in site:
            words = cleaned.split()
            query = " ".join(w for w in words if w != keyword and w != "on")
            url = url_template.format(query.replace(' ', '+'))
            speak(f"Searching for {query} on {keyword.capitalize()}")
            try:
                webbrowser.open(url)
                log(f"Opening {keyword}")
            except Exception as e:
                log(f"Failed to open {url}: {e}")
                speak(f"Sorry, I couldn't perform the search on {keyword.capitalize()}.")
            return

    # 2. Generic "search X on Y"
    if " on " in cleaned:
        q, s = cleaned.split(" on ", 1)
        q = q.strip()
        s = s.strip().replace(" ", "")
        url = f"https://www.{s}.com/search?q={q}"
        speak(f"Searching for {q} on {s}")
        try:
            webbrowser.open(url)
            log(f"Opening {url}")
        except Exception as e:
            log(f"Failed to open {url}: {e}")
            speak(f"Sorry, I couldn't perform the search on {s}.")
        return

    # 3. Fallback: Google search
    query = cleaned
    try:
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
        speak(f"Searching for {query}")
        log(f"Searching for {query}")
    except Exception as e:
        log(f"Failed to open browser: {e}")
        speak("Sorry, I couldn't perform the web search.")


def send_image(whom: str):
    whom = whom.lower().strip()
    contacts = {"sumit": "+918668809839",
                "didi" : "+918080232567",
                "papa" : "+919049137649",
                "me"   : "+917030137649",
        }
    for name, number in contacts.items():
        if name in whom:
                speak("Please select an area of the screen to capture.")
                auto.hotkey('win', 'shift', 's')
                time.sleep(2)  # Give time for the snipping tool to activate

                start_time = time.time()
                timeout = 20  # seconds

                while time.time() - start_time < timeout:
                    if keyboard.is_pressed("esc"):
                        speak("Cancelled by user.")
                        return

                    try:
                        img = ImageGrab.grabclipboard()
                        if img:
                            if img.mode == "RGBA":
                                img = img.convert("RGB")

                            temp_path = os.path.join(os.path.expanduser("~"), "snipped_image.jpg")
                            img.save(temp_path, "JPEG")

                            speak("sending the image.")
                            log("Analyzing the image.")
                            try:
                                speak(f"Sending image to {name.capitalize()}")
                                log(f"Sending image to {name.capitalize()}")
                                kit.sendwhats_image(f"{number}", temp_path, "Check this out!")
                                time.sleep(2)
                                return
                            except Exception as e:
                                log(f"Failed to send image to {name}: {e}")
                                speak(f"Sorry, I couldn't send the image to {name.capitalize()}.")
                                return
                    except Exception as e:
                        log(f"Clipboard error: {e}")
                    time.sleep(1)

                speak("No screenshot detected. Exiting.")
                log("No screenshot detected. Exiting.")  
    speak("Please specify a valid recipient for the image.")
        


def message_(message: str):
    message = message.lower().strip()
    contacts = {"sumit": "+918668809839",
                "didi" : "+918080232567",
                "papa" : "+919049137649",
                "me"   : "+917030137649",
                }
    
    for name, number in contacts.items():
        if name in message:
            message_text = message.split(name)[-1].strip()
            try:
                kit.sendwhatmsg_instantly(number, message_text)
                speak(f"Sending message '{message_text}' to {name.capitalize()}")
                log(f"Sending message '{message_text}' to {name.capitalize()}")
                return
            except Exception as e:
                log(f"Failed to send message to {name}: {e}")
                speak(f"Sorry, I couldn't send the message to {name.capitalize()}.")
                return
    speak("Please specify a valid recipient for the message.")


def close_window():
    # Move the mouse to absolute coordinates (x, y)
    auto.moveTo(1900, 15) 
    auto.click()


def minimise_window():
    auto.moveTo(1803, 12) 
    auto.click()


COMMANDS = {
    "analyse": lambda: get_clipboard_image(),
    "analyse the image": lambda : get_clipboard_image(),
    "open": open_website,
    "search": search_on_website,
    "play": lambda command: (kit.playonyt(command), speak(f"playing {command}")),
    "what is your name": lambda: speak("I am jarvis, your personal assistant. How can I help you today?"),
    "who are you": lambda: speak("I am jarvis, your personal assistant. How can I help you today?"),
    "shutdown": stop_app,
    "shut down": stop_app,
    "capture image": capture_photo,
    "capture": capture_photo,
    "message": message_,
    "close window" : close_window,
    "minimise window" : minimise_window,
    "send image" : send_image,
}


def processCommand(c: str):
    cl = c.lower()
    
    # Exact match for commands without arguments
    if cl in COMMANDS and cl not in ["play", "open", "search", "message", "analyse", "analyse the image", "send image"]:
        COMMANDS[cl]()
        return

    # Match for commands that take arguments
    for command, action in COMMANDS.items():
        if cl.startswith(command + " ") and command in ["play", "open", "search", "message", "send image"]:
            argument = cl.replace(command, "", 1).strip()
            action(argument)
            return
    
    if cl in ["analyse", "analyse the image"]:
        COMMANDS[cl]()
        return
            
    # Fallback to local LLM
    local_llm_stream(c)


def get_clipboard_image():
    speak("Please select an area of the screen to capture.")
    auto.hotkey('win', 'shift', 's')
    time.sleep(2)  # Give time for the snipping tool to activate

    start_time = time.time()
    timeout = 20  # seconds

    while time.time() - start_time < timeout:
        if keyboard.is_pressed("esc"):
            speak("Cancelled by user.")
            return

        try:
            img = ImageGrab.grabclipboard()
            if img:
                if img.mode == "RGBA":
                    img = img.convert("RGB")

                temp_path = os.path.join(os.path.expanduser("~"), "snipped_image.jpg")
                img.save(temp_path, "JPEG")

                speak("Analyzing the image.")
                log("Analyzing the image.")
                aianalyser(temp_path)
                return  # Exit after successful analysis
        except Exception as e:
            log(f"Clipboard error: {e}")
        time.sleep(1)

    speak("No screenshot detected. Exiting.")
    log("No screenshot detected. Exiting.")


def aianalyser(path: str):
    if not path or not os.path.exists(path):
        log(f"Invalid path for analysis: {path}")
        speak("Image analysis failed: Invalid file.")
        return

    try:
        from tensorflow.keras.applications import MobileNetV2
        from tensorflow.keras.preprocessing import image
        from tensorflow.keras.applications.mobilenet_v2 import preprocess_input, decode_predictions
        import tensorflow as tf
        import numpy as np

        log("Analyzing...")
        model = MobileNetV2(weights="imagenet")
        img = tf.keras.preprocessing.image.load_img(path, target_size=(224, 224))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        preds = model.predict(x)
        decoded = decode_predictions(preds, top=1)[0]

        if decoded:
            label, score = decoded[0][1], decoded[0][2]
            prediction_text = f"{label.replace('_', ' ')}: {score*100:.2f}%"
            log(prediction_text)
            speak(f"This looks like a {label.replace('_', ' ')} with {score*100:.0f} percent confidence.")
        else:
            speak("I'm not sure what this is.")

    except ImportError:
        log("TensorFlow or Keras not installed.")
        speak("Image analysis module not installed. Please install TensorFlow and Keras.")
    except Exception as e:
        log(f"Error in aianalyser: {e}")
        speak("Sorry, I encountered an error during image analysis.")
    finally:
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                log(f"Failed to remove temp file {path}: {e}")


def jarvis_main():
    """The main logic for the Jarvis assistant."""
    speak("How may I help you?")
    recognizer = sr.Recognizer()
    try:
        mic = sr.Microphone()
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
    except Exception as e:
        log(f"Error initializing microphone: {e}")
        speak("Microphone not available. Exiting.")
        return

    while True:
        try:
            with mic as source:
                log("Listening...")
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    word = recognizer.recognize_google(audio)
                    if word.strip().lower().startswith("jarvis"):
                        command = word.strip().lower().replace("jarvis", "").strip()
                        if command:
                            log(f"Command: {command}")
                            processCommand(command)
                except sr.UnknownValueError:
                    continue
                except sr.RequestError as e:
                    log(f"Could not request results: {e}")
                    speak("Sorry, I'm having trouble connecting to the speech service.")
                    time.sleep(5)
                except sr.WaitTimeoutError:
                    continue
        except KeyboardInterrupt:
            log("Interrupted by user")
            speak("Shutting down")
            break
        except Exception as e:
            log(f"An unexpected error occurred in the main loop: {e}")
            speak("An unexpected error occurred. Please check the logs.")
            time.sleep(1)
            continue