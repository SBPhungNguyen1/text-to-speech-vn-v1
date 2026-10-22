# Text to Speech Studio

> A tiny Python desktop app to turn text into MP3 audiobooks.

## 🎯 Why?

**I WANTED TO LISTEN TO STORIES WHILE CODING INSTEAD OF STOPPING TO READ.**

Many TTS tools limit how much text you can convert or how often you can use them.

So I built my own.

**Long text → One MP3.**

Automatically split, converted, and merged. No manual chunking.

**No custom backend. No FFmpeg. No complicated setup.**

Paste your text, choose your settings, generate your MP3, and get back to what you were doing. 🎧

> **Note:** This project is a stepping stone toward building my own story-reading app with audio playback.

## ✨ Features

- 🎙️ **Text to Speech** — convert words, paragraphs, or entire chapters into speech.
- 🖥️ **Desktop GUI** — a simple interface built with Python and Tkinter.
- 🇻🇳 **Vietnamese voices** — choose between Hoài My (female) and Nam Minh (male).
- ⚡ **Adjustable speed** — choose from five reading speeds, from -20% to +20%.
- 📚 **Automatic chunking** — split long text into smaller chunks for TTS processing.
- 🚀 **Concurrent processing** — process up to two chunks at a time while preserving their original order.
- 🔗 **Automatic merging** — combine generated audio chunks into a single MP3 file.
- 📝 **Custom filenames** — name your audio files using your own titles.
- 📂 **Custom output folder** — choose where your MP3 files are saved.
- 🔄 **Automatic retries** — retry failed audio generation requests.
- 📊 **Progress tracking** — monitor the conversion process.
- 🪶 **Lightweight** — Python, Tkinter, and `edge-tts`.

## 🚀 Getting Started

### Option 1: Download the Windows app

1. Open [GitHub Releases](https://github.com/SBPhungNguyen1/text-to-speech-vn-v1/releases).
2. Download the latest `TextToSpeechStudio.exe`.
3. Run the application.
4. Connect to the internet before generating audio.

No separate Python installation is required when using the packaged executable.

### Option 2: Run from source

#### 1. Clone the repository

```bash
git clone https://github.com/SBPhungNguyen1/text-to-speech-vn-v1.git
cd text-to-speech-vn-v1
```

#### 2. Create a virtual environment (recommended)

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

#### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

#### 4. Run the application

```bash
python text_to_speech.py
```

### Generate your audiobook

1. Enter a title for your audio file.
2. Paste or type the text you want to convert.
3. Choose a voice and reading speed.
4. Select an output folder.
5. Click **Generate MP3**.
6. Wait for the conversion to finish.

Your MP3 file will be saved in the selected folder using the title you entered.

## 🔄 How It Works

```text
Paste your text
       ↓
Enter a title
       ↓
Choose voice and speed
       ↓
Split text into chunks
       ↓
Generate audio with edge-tts
       ↓
Process chunks concurrently
       ↓
Merge chunks in the original order
       ↓
🎧 your_title.mp3
```

## ⚡ Performance

Long text is split into smaller chunks and processed with limited concurrency to balance speed and reliability.

Actual conversion time depends on:

- Text length and number of chunks.
- Internet connection and network latency.
- Response time and availability of the online TTS service.
- Temporary throttling or failed requests that require retries.

Concurrent processing may reduce waiting time, but it does not guarantee faster conversion than other TTS services. Performance comparisons require testing the same text under comparable conditions.

## 🛠️ Requirements

When running from source:

- Python 3.10+
- An internet connection
- Access to Microsoft's online TTS service through `edge-tts`

When using the packaged Windows executable, a separate Python installation is not required.

## ⚠️ Limitations

- This application requires an internet connection to generate speech.
- Audio generation may fail if the TTS service is unavailable or network access is interrupted.
- Failed requests are retried automatically, but repeated failures can still stop the conversion.
- MP3 chunks are concatenated directly without FFmpeg. Playback compatibility may vary across audio players.
- Voice availability and service behavior may change over time.
- Conversion speed is not guaranteed and may vary between sessions.

Please respect copyright and authors' rights. Only convert content you have the right to use, and do not redistribute copyrighted material without permission.

## 🔒 Privacy

Text is processed locally by the application before being sent to the online TTS service for speech generation.

**No custom backend. No database. No account system.**

However, text sent to `edge-tts` is handled by a remote service. Do not use this application for confidential text that you are not comfortable sending to an online service.

## 📁 Project Structure

```text
text-to-speech-vn-v1/
├── text_to_speech.py
├── requirements.txt
├── README.md
├── .gitignore
└── ...
```

Generated MP3 files are saved to the output folder you choose. Build artifacts and generated audio files do not need to be committed to Git.

---

## That's all 🎧

I wanted something **simple, lightweight, and convenient** to turn text into audio while coding.

So here it is.

**Paste → Generate → Listen.**
