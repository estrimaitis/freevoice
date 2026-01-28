<p align="center">
  <img src="assets/logo.png" alt="freevoice logo" width="128">
</p>

<h1 align="center">freevoice</h1>

<p align="center">
  <strong>Free, Open-Source Voice-to-Text for Windows using OpenAI Whisper</strong>
</p>

<p align="center">
  Press a hotkey, speak, and your words get typed into any text field. Simple as that.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License MIT">
  <img src="https://img.shields.io/badge/platform-Windows-lightgrey.svg" alt="Platform Windows">
</p>

<p align="center">
  <img src="assets/models.png" alt="Model selection settings" width="500">
</p>

<p align="center">
  <img src="assets/statistics.png" alt="Usage statistics" width="500">
</p>

## Why freevoice?

Tired of slow, inaccurate, or subscription-based dictation software? freevoice is a **free, offline voice typing app** for Windows that actually works.

**The problem:** Most speech-to-text tools are either cloud-based (privacy concerns, requires internet, often paid), or the built-in Windows voice typing is limited and inconsistent.

**The solution:** freevoice runs entirely on your machine using OpenAI's Whisper - the same AI that powers professional transcription services. No subscriptions, no internet required, no data leaving your computer.

Whether you're writing emails, coding, taking notes, or just prefer speaking over typing, freevoice gives you fast, accurate voice-to-text in any application. It works everywhere - browsers, Word, Slack, VS Code, even games with chat.

## Features

- **Push-to-talk** - Hold the hotkey to record, release to transcribe
- **Hands-free mode** - Lock recording to speak without holding keys
- **System tray app** - Runs quietly in the background
- **Auto-type** - Transcribed text is automatically typed into the focused field
- **Smart Dictionary** - Automatically corrects brand names and technical terms
- **Text Cleanup** - Removes filler words (um, uh, etc.)
- **Multiple Whisper models** - Choose speed vs accuracy
- **Customizable shortcuts** - Set your own hotkeys
- **Notification sounds** - Audio feedback for recording start/stop
- **Offline** - Everything runs locally, no internet needed after model download
- **GPU acceleration** - Supports CUDA for faster transcription (optional)

## Quick Start

1. **Install Python 3.10+** from [python.org](https://www.python.org/downloads/)
   - Check "Add Python to PATH" during installation

2. **Download this repository** (Code → Download ZIP) and extract it

3. **Install dependencies** - Open terminal in the folder and run:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run freevoice** - Double-click `freevoice.bat`

That's it! The app will download the Whisper model on first run, then you're ready to go.

> **Note:** This is plain Python code - feel free to look around, customize it, or learn from it. No hidden magic here.

## Usage

1. **Start the app** - It appears in your system tray (bottom-right, near the clock)
2. **Click on any text field** where you want to type
3. **Hold your hotkey and speak** - Release to transcribe

### Default Shortcuts

| Action | Keys | Description |
|--------|------|-------------|
| **Push-to-talk** | Hold `Ctrl+Alt` | Hold to record, release to transcribe |
| **Lock recording** | `Ctrl+Alt` + `Space` | Hands-free mode - keeps recording after release |
| **Stop locked recording** | `Ctrl+Alt` | Stops recording and transcribes |
| **Cancel** | `Esc` | Cancels recording without transcribing |

All shortcuts can be customized in Settings.

### Tray Icon Status

The app icon shows a colored dot in the corner to indicate status:

| Dot | Status |
|-----|--------|
| (none) | Idle, ready to record |
| 🔴 Red | Recording (push-to-talk) |
| 🟣 Purple | Recording locked (hands-free) |
| 🟠 Orange | Processing/transcribing |

### Settings

Right-click the tray icon → **Settings** (or double-click the icon)

- **Model** - Choose Whisper model (tiny → large-v3)
- **Language** - Auto-detect or specify language
- **Shortcuts** - Customize all hotkeys
- **Text Cleanup** - Remove filler words automatically
- **Dictionary** - Add custom terms and brand names
- **Sounds** - Toggle notification sounds
- **Startup** - Launch automatically with Windows

## Whisper Models

| Model | Download | Speed | Accuracy | Best for |
|-------|----------|-------|----------|----------|
| `tiny` | ~75 MB | Fastest | Basic | Quick notes |
| `base` | ~150 MB | Fast | Good | **Recommended** |
| `small` | ~500 MB | Medium | Better | General use |
| `medium` | ~1.5 GB | Slow | Great | Important content |
| `large-v2` | ~3 GB | Slowest | Excellent | Maximum accuracy |
| `large-v3` | ~3 GB | Slowest | Best | Maximum accuracy |

Models are downloaded automatically when first selected.

## Smart Dictionary

freevoice automatically recognizes similar-sounding words and replaces them with your preferred spelling. Just add your terms - no need to list every variation!

Edit in Settings → Dictionary, or directly in `dictionary.json`:

```json
{
    "terms": [
        "ChatGPT",
        "JavaScript", 
        "TypeScript",
        "PostgreSQL",
        "Kubernetes",
        "YourBrandName"
    ]
}
```

**How it works:**
- Say "chat gpt" → types "ChatGPT"
- Say "javascript" → types "JavaScript"
- Say "post gres" → types "PostgreSQL"

Uses phonetic matching - just add the correct spelling and it figures out the rest!

## Tips

- **Speak clearly** with natural pauses between sentences
- **GPU acceleration** - If you have an NVIDIA GPU with CUDA, transcription will be much faster
- **Set your language** - Specifying a language is faster than auto-detect
- **Clipboard preserved** - Your clipboard contents are restored after typing

## Troubleshooting

### "No audio recorded"
- Check your microphone is set as default in Windows Sound Settings
- Make sure no other app is exclusively using the microphone

### Slow transcription
- Use a smaller model (Settings → Model → tiny or base)
- If you have an NVIDIA GPU, ensure CUDA drivers are installed

### Text not appearing
- Make sure a text field is focused before releasing the hotkey
- Some applications may block simulated keyboard input
- Check tray menu → "Copy Last" to get the text to your clipboard

### Hotkeys not working
- Some apps may capture global hotkeys - try different shortcuts in Settings
- Run as administrator if shortcuts don't work in elevated apps

## Project Structure

```
freevoice/
├── assets/           # Icons and sounds
├── scripts/          # Development tools
├── src/              # Source code modules
├── config.json       # User settings
├── dictionary.json   # Custom terms
├── main.py           # Entry point
├── freevoice.bat     # Launch script
└── requirements.txt  # Dependencies
```

## Development

For development with auto-reload (restarts the app when you change files):

```bash
python scripts/dev.py
```

Press `Ctrl+C` to stop. Requires `watchdog` (installed automatically on first run).

## Requirements

- Windows 10/11
- Python 3.10+
- Microphone
- ~200 MB disk space (plus model size)

## Credits

- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition model
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) - Optimized Whisper implementation

## Author

Created by [@estrimaitis](https://github.com/estrimaitis)

- GitHub: [github.com/estrimaitis/freevoice](https://github.com/estrimaitis/freevoice)

## License

MIT License - Use it however you want!
