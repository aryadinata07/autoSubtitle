# Auto Subtitle Generator 🎬
> Generate professional subtitles & dubbing automatically using AI.

## ✨ Features
- **Deep Hearing™**: 2-Stage Transcription (Draft -> Glossary -> Final) for max accuracy.
- **Smart Batching**: Better Google Translate quality for free users.
- **SubtitleShield**: AI quality control to fix hallucinations.
- **Audio Laundromat**: Auto-denoise & normalize audio.
- **Auto-Embed**: Hardsub directly into video (Instagram/TikTok ready).

## 🚀 Quick Start

### 1. Install
```bash
pip install -r requirements.txt
# Install FFmpeg (Required): www.ffmpeg.org
```

### 2. Configure (One-time)
Run the wizard to set your preferences (API Key, Styling, Free/Premium Mode):
```bash
python generate_subtitle.py --configure
```

### 3. Run!
**Fastest Way (YouTube):**
```bash
python generate_subtitle.py -url "https://youtu.be/..." -fast
```

**Local Video (Interactive):**
```bash
python generate_subtitle.py
```

## 🛠️ Modes (Cheat Sheet)

| Mode | Command | Best For | Cost |
|------|---------|----------|------|
| **Default** | `-default` | General Usage | Paid (DeepSeek) |
| **Fast** | `-fast` | YouTube/Podcasts | Paid (DeepSeek) |
| **Quality** | `-quality` | Professional Work | Paid (DeepSeek) |
| **Free/Budget** | `-budget` | Free Usage | **FREE** (Google) |
| **Speed** | `-speed` | Quick Drafts | **FREE** (Google) |

## 🧠 Premium vs Free

- **Premium (DeepSeek Key)**:
    - Context-aware translation ("Stream" = "Streaming", not "Sungai").
    - Auto-Glossary (Learns distinct terms like "Ganking", "Retri").
    - SubtitleShield (Fixes typos).

- **Free (Google Translate)**:
    - Smart Batching (Translates paragraphs, not just lines).
    - 0 Cost.
    - Decent quality for general content.

## 🤝 License
MIT License. Free to use & modify.
