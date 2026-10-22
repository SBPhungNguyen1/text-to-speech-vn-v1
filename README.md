# **Text to Speech Studio**

> A tiny Python desktop app to turn text into MP3 audiobooks.

## 🎯 Why?

**I WANTED TO LISTEN TO STORIES WHILE CODING INSTEAD OF STOPPING TO READ.**

But many TTS tools limit **how much text you can convert at once** or **how often you can use them**.

So I built my own.

**Long text → One MP3.** Automatically split, converted, and merged. No manual chunking. No complicated setup.

**No custom backend. No FFmpeg. No complicated setup.**

Just paste your text, choose your settings, generate your MP3, and get back to what you were doing. 🎧

> **Note:** This project is a stepping stone toward building my own story-reading app with audio playback.

## ✨ Features

- 🎙️ **Text to Speech** — convert words, paragraphs, or entire chapters into speech.
- 🖥️ **Desktop GUI** — a simple interface built with Python and Tkinter.
- 🇻🇳 **Vietnamese voices** — choose between Hoài My (female) and Nam Minh (male).
- ⚡ **Adjustable speed** — customize the reading speed to your liking.
- 📚 **Chunk processing** — automatically splits long text into smaller chunks for TTS processing.
- 🔗 **Automatic merging** — combines generated audio chunks into a single MP3 file.
- 📝 **Custom filenames** — name your audio files using your own titles.
- 📂 **Custom output folder** — choose where your MP3 files are saved.
- 🔄 **Automatic retries** — retries failed audio generation requests.
- 📊 **Progress tracking** — monitor the audio generation process.
- 🚫 **No backend** — everything is orchestrated locally on your computer.
- 🪶 **Lightweight** — just Python, Tkinter, and `edge-tts`.

## 🛠️ Requirements

- Python 3.10+
- An internet connection
- Microsoft Edge TTS access through `edge-tts`

## 🚀 How to use

### 1. Clone the repository

```bash
git clone https://github.com/SBPhungNguyen1/text-to-speech-vn-v1.git
cd text-to-speech
```

### 2. Create a virtual environment (optional)

```bash
python -m venv .venv
```

Activate it:

**Windows**

```bash
.venv\Scripts\activate
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python text_to_speech.py
```

### 5. Generate your audiobook

1. Enter a title for your audio file.
2. Paste or type the text you want to convert.
3. Choose a voice and reading speed.
4. Select an output folder.
5. Click **Generate MP3**.
6. Wait for the conversion to finish.

Your MP3 file will be saved using the title you entered.

## 🔄 How it works

```text
Paste your text
      ↓
Enter a title
      ↓
Choose voice & speed
      ↓
Split text into chunks
      ↓
Generate audio with edge-tts
      ↓
Merge audio chunks
      ↓
🎧 your_title.mp3
```

## 📁 Project structure

```text
text-to-speech/
├── text_to_speech.py
├── requirements.txt
├── README.md
└── audiobooks/
    └── your_title.mp3
```

## ⚠️ Note

- This application uses `edge-tts`, which requires an internet connection to generate speech.
- Audio generation may fail if the TTS service is unavailable or network access is interrupted.
- Long texts are split into smaller chunks and processed sequentially.
- MP3 chunks are concatenated directly. Playback compatibility may vary depending on the player and the generated audio streams.
- This project does not include a backend, but it does rely on Microsoft's online TTS service.
- Voice availability and service behavior may change over time.

Please respect copyright and authors' rights. Only convert content you have the right to use, and do not redistribute copyrighted material without permission.

## 🔒 Privacy

Your text is processed by the application on your computer before being sent to the online TTS service for speech generation.

**No custom backend. No database. No account system.**

However, the text sent to `edge-tts` is handled by the remote TTS service, so this application should not be considered fully offline or suitable for confidential text.

---

## That's all

I wanted something **simple, lightweight, and convenient** to turn text into audio while coding.

So here it is.

**Paste → Generate → Listen.** 🎧
