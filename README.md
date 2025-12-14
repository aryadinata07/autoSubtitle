# Auto Subtitle Generator

Automatically generate subtitles and voice dubbing for videos using Whisper AI.

## ✨ Features

- 🎯 **Automatic Transcription** - Using OpenAI Whisper (Faster-Whisper by default)
- 🌍 **Auto Translation** - English ↔ Indonesian with Google Translate or DeepSeek AI
- 🎬 **Video Embedding** - Hardcode subtitles directly into video (3 encoding methods)
- 📺 **YouTube Support** - Download and process YouTube videos automatically
- ⚡ **GPU Acceleration** - Support for NVIDIA GPU (CUDA) for faster processing
- 🎨 **Customizable Styling** - Adjust subtitle appearance via .env configuration
- 🎬 **Auto-detect Video Orientation** - Automatically adjust subtitle size for Reels/Shorts

## 📋 Requirements

- Python 3.8+
- FFmpeg (for video/audio processing)
- NVIDIA GPU with CUDA (optional, for GPU acceleration)

## 🚀 Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install FFmpeg

- **Windows**: Download from https://ffmpeg.org/download.html
- **Linux**: `sudo apt install ffmpeg`
- **Mac**: `brew install ffmpeg`

### 3. Setup Configuration (Optional)

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` file:
```env
# DeepSeek API Key (for better translation quality)
DEEPSEEK_API_KEY=your_api_key_here

# Whisper Mode (1=Faster-Whisper, 2=Regular Whisper)
WHISPER_MODE=1

# Turbo Mode (true=always on, false=always off, ask=ask every time)
TURBO_MODE=ask

# Subtitle Styling (auto, minimal, standard, bold, reels, reels-bold)
# 'auto' will automatically detect video orientation and choose the best preset
SUBTITLE_PRESET=auto

# Subtitle Position (bottom, top, center)
SUBTITLE_POSITION=bottom
```

Get DeepSeek API key from: https://platform.deepseek.com/

## 📖 Usage

### Interactive Mode (Recommended)

```bash
python generate_subtitle.py
```

**Interactive Mode** - The script will guide you through:
1. **Video Source** - Local file or YouTube URL
2. **Transcription Mode** - Standard (accurate) or Turbo (3-6x faster)
3. **Translation Method** - DeepSeek AI (default, better quality) or Google Translate (free fallback)
4. **Embedding Method** - Fast encoding (default), Standard quality, or GPU accelerated

**Preset Modes** - Skip all prompts, use pre-configured settings:
```bash
# Fast mode (recommended for most users)
autosub -url "https://youtube.com/..." -fast

# Default mode (balanced quality/speed)
autosub -url "https://youtube.com/..." -default

# Quality mode (maximum accuracy)
autosub -url "https://youtube.com/..." -quality

# Speed mode (maximum speed, no API key)
autosub -url "https://youtube.com/..." -speed

# Budget mode (free, no API key)
autosub -url "https://youtube.com/..." -budget
```

### Command Line Mode

**Process YouTube Video:**
```bash
python generate_subtitle.py -url "https://youtube.com/watch?v=..."
```

**Process Local File:**
```bash
python generate_subtitle.py -l "path/to/video.mp4"
```

**With Preset Modes:**
```bash
# Fast mode (recommended for most users)
python generate_subtitle.py -url "https://youtube.com/..." -fast

# Default mode (balanced)
python generate_subtitle.py -l "video.mp4" -default

# Quality mode (maximum accuracy)
python generate_subtitle.py -l "video.mp4" -quality

# Speed mode (maximum speed, no API key)
python generate_subtitle.py -l "video.mp4" -speed

# Budget mode (free, no API key)
python generate_subtitle.py -l "video.mp4" -budget
```

**With Custom Options:**
```bash
# Fast mode + Distil model (18x faster!)
python generate_subtitle.py -l "video.mp4" --model distil-large -fast

# Quality mode + Large model
python generate_subtitle.py -l "video.mp4" --model large -quality

# Speed mode + Specific language
python generate_subtitle.py -l "video.mp4" --lang id -speed

# Interactive mode (choose all options manually)
python generate_subtitle.py -l "video.mp4"
```

**Available Options:**

**Preset Modes (No Prompts):**
- `-default` - Balanced (Standard + DeepSeek + Fast Encoding)
- `-fast` - Fast mode (Turbo + DeepSeek + Fast Encoding) ⚡ Recommended
- `-quality` - Quality mode (Standard + DeepSeek + Standard Encoding)
- `-speed` - Speed mode (Turbo + Google + Fast Encoding)
- `-budget` - Budget mode (Standard + Google + Fast Encoding) 💰 No API key

**Video Source:**
- `-url <url>` or `--url <url>` - YouTube URL
- `-l <path>` or `--local <path>` - Local video file path

**Customization:**
- `--model <size>` - Model size: tiny, base, small, medium, large, distil-small, distil-medium, distil-large (default: base)
- `--lang <code>` - Language code: id, en, or auto-detect (default: auto)
- `--turbo` - Force turbo mode (can override preset)
- `--deepseek` - Force DeepSeek AI (can override preset)

## 🎯 Features Explained

### 1. Transcription Methods

**Faster-Whisper (Default)**
- ✅ 4-5x faster than regular Whisper
- ✅ 50% less memory usage
- ✅ Same accuracy as regular Whisper
- ✅ GPU acceleration support
- ✅ Turbo Mode available (3-6x faster)

**Regular Whisper**
- ✅ Standard OpenAI implementation
- ✅ Reliable and well-tested
- ⚠️ Slower processing

Configure in `.env`: `WHISPER_MODE=1` (Faster) or `WHISPER_MODE=2` (Regular)

**Turbo Mode (Both Whisper Implementations)**
- ✅ 2-6x faster than standard mode
- ✅ Greedy decoding (instant decisions, no beam search)
- ✅ 99% same accuracy for clear audio
- ✅ Perfect for YouTube/Podcast/TEDx
- ⚠️ Slightly less accurate for very noisy audio
- 📊 Speed boost: Faster-Whisper (3-6x), Regular Whisper (2-3x)

Configure in `.env`: `TURBO_MODE=true` (always on), `false` (always off), or `ask` (ask every time)

### 2. Translation Methods

**DeepSeek AI (Default - Recommended)**
- ✅ More natural and conversational
- ✅ Context-aware (understands video topic)
- ✅ Batch processing (10x faster)
- ✅ Better translation quality
- ⚠️ Requires API key (very cheap - ~$0.14 per 1M tokens)

**Google Translate (Free Fallback)**
- ✅ Free, no API key required
- ✅ Fast and reliable
- ✅ Good for basic translation
- ⚠️ Sometimes too literal/stiff
- ⚠️ Not context-aware

### 3. Video Embedding Methods

**Fast Encoding (Default - Recommended)**
- ✅ 2-3x faster (~4-6 min for 17 min video)
- ✅ Still good quality
- ✅ Best balance of speed and quality
- ⚠️ Slightly lower quality (barely noticeable)

**Standard Quality**
- ✅ Best quality
- ✅ Compatible with all players
- ⚠️ Slowest (~12-13 min for 17 min video)

**GPU Accelerated**
- ✅ 3-5x faster (~2-3 min for 17 min video)
- ✅ Quality almost same as standard
- ⚠️ Requires NVIDIA GPU with CUDA

### 4. Subtitle Styling

Configure in `.env`:

**Presets:**
- `auto` - **Auto-detect based on video orientation** (vertical → reels, horizontal → minimal) [RECOMMENDED]
- `minimal` - Small font, thin outline, doesn't distract from video (for landscape videos)
- `standard` - Balanced, readable but not too dominant
- `bold` - Large font, thick outline, for better readability
- `reels` - Extra small font, optimized for vertical videos (Instagram Reels, TikTok, YouTube Shorts)
- `reels-bold` - Small font with better visibility for vertical videos

**Position:**
- `bottom` - Bottom position (default)
- `top` - Top position
- `center` - Center position (not recommended)

**Custom Styling:**
```env
SUBTITLE_FONT_SIZE=14
SUBTITLE_OUTLINE=1
SUBTITLE_MARGIN=10
```

## 📊 Model Sizes

| Model | Speed | Accuracy | RAM Usage | Notes |
|-------|-------|----------|-----------|-------|
| tiny | ⚡⚡⚡⚡⚡ | ⭐⭐ | ~1 GB | Fastest, lowest quality |
| base | ⚡⚡⚡⚡ | ⭐⭐⭐ | ~1.5 GB | Good balance |
| small | ⚡⚡⚡ | ⭐⭐⭐⭐ | ~2.5 GB | Recommended |
| medium | ⚡⚡ | ⭐⭐⭐⭐⭐ | ~5 GB | High accuracy |
| large | ⚡ | ⭐⭐⭐⭐⭐ | ~10 GB | Maximum accuracy |
| **distil-small** | ⚡⚡⚡⚡⚡⚡ | ⭐⭐⭐⭐ | ~1 GB | **6x faster than small** |
| **distil-medium** | ⚡⚡⚡⚡⚡ | ⭐⭐⭐⭐⭐ | ~2 GB | **6x faster than medium** |
| **distil-large** | ⚡⚡⚡⚡ | ⭐⭐⭐⭐⭐ | ~3 GB | **6x faster than large** |

**Distil-Whisper Models:**
- Compressed using Knowledge Distillation by HuggingFace
- 50% smaller model size
- 6x faster inference speed
- Same accuracy as original models
- Recommended for production use

## 🌍 Language Codes

- `id` - Indonesian
- `en` - English
- Leave empty for auto-detect

## 📁 Output

### Output Directory Logic:
- **Running from project folder**: Output saved to `downloads/` folder
- **Running from anywhere else**: Output saved to `videos/` folder in current directory

Example:
```bash
# From project folder
cd C:\project\vidio-subtitle
autosub -url "https://youtube.com/..."
# Output: C:\project\vidio-subtitle\downloads\video_with_subtitle.mp4

# From Desktop
cd C:\Users\YourName\Desktop
autosub -url "https://youtube.com/..."
# Output: C:\Users\YourName\Desktop\videos\video_with_subtitle.mp4
```

### Generated Files:
- `{video_name}_with_subtitle.mp4` - Video with embedded subtitle
- Temporary files are automatically cleaned up

### Translation Direction:
- English video → Indonesian subtitle
- Indonesian video → English subtitle

## 🏗️ Project Structure

```
autoSubtitle/
├── generate_subtitle.py       # Main script
├── utils/
│   ├── __init__.py            # Package initialization
│   ├── audio_extractor.py     # Extract audio from video
│   ├── transcriber.py         # Whisper transcription interface
│   ├── transcriber_faster.py  # Faster-Whisper implementation
│   ├── transcriber_whisper.py # Regular Whisper implementation
│   ├── subtitle_creator.py    # Create SRT files with styling
│   ├── translator.py          # Translation interface
│   ├── translator_google.py   # Google Translate implementation
│   ├── translator_deepseek.py # DeepSeek AI implementation
│   ├── video_embedder.py      # Embed subtitle to video
│   ├── dubbing.py             # Voice dubbing (gTTS, Piper TTS)
│   ├── youtube_downloader.py  # YouTube video downloader
│   └── ui.py                  # Terminal UI utilities
├── .env                       # Configuration (API keys, settings)
├── .env.example               # Example configuration
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🚀 Quick Reference - Preset Modes

### 1. Default Mode (Balanced) ⚖️
```bash
autosub -url "https://youtube.com/..." -default
```
**Configuration:**
- 🎯 Standard Mode (beam search, maximum accuracy)
- 🤖 DeepSeek AI (better translation)
- ⚡ Fast Encoding (2-3x faster)
- ✅ Best for: General use, balanced quality/speed

### 2. Fast Mode (Recommended for Most Users) 🚀
```bash
autosub -url "https://youtube.com/..." -fast
```
**Configuration:**
- ⚡ Turbo Mode (greedy search, 3-6x faster)
- 🤖 DeepSeek AI (better translation)
- ⚡ Fast Encoding (2-3x faster)
- ✅ Best for: YouTube videos, podcasts, clear audio

### 3. Quality Mode (Maximum Accuracy) 💎
```bash
autosub -url "https://youtube.com/..." -quality
```
**Configuration:**
- 🎯 Standard Mode (beam search, maximum accuracy)
- 🤖 DeepSeek AI (better translation)
- 🎬 Standard Encoding (best quality)
- ✅ Best for: Professional work, important content

### 4. Speed Mode (Maximum Speed) ⚡⚡⚡
```bash
autosub -url "https://youtube.com/..." -speed
```
**Configuration:**
- ⚡ Turbo Mode (greedy search, 3-6x faster)
- 🌐 Google Translate (free, no API key)
- ⚡ Fast Encoding (2-3x faster)
- ✅ Best for: Quick tests, batch processing

### 5. Budget Mode (Free, No API Key) 💰
```bash
autosub -url "https://youtube.com/..." -budget
```
**Configuration:**
- 🎯 Standard Mode (beam search, maximum accuracy)
- 🌐 Google Translate (free, no API key)
- ⚡ Fast Encoding (2-3x faster)
- ✅ Best for: No DeepSeek API key, free usage

### Comparison Table

| Preset | Transcription | Translation | Encoding | Speed | Quality | API Key |
|--------|--------------|-------------|----------|-------|---------|---------|
| **-default** | Standard | DeepSeek | Fast | ⚡⚡ | ⭐⭐⭐⭐ | Required |
| **-fast** | Turbo | DeepSeek | Fast | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | Required |
| **-quality** | Standard | DeepSeek | Standard | ⚡ | ⭐⭐⭐⭐⭐ | Required |
| **-speed** | Turbo | Google | Fast | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ | Not Required |
| **-budget** | Standard | Google | Fast | ⚡⚡ | ⭐⭐⭐ | Not Required |

### Advanced Combinations
```bash
# Fast mode + Distil model (18x faster!)
autosub -l "video.mp4" --model distil-large -fast

# Quality mode + Large model (maximum accuracy)
autosub -l "video.mp4" --model large -quality

# Speed mode + Distil model (ultimate speed)
autosub -l "video.mp4" --model distil-medium -speed

# Budget mode + Specific language
autosub -l "video.mp4" --lang id -budget
```

---

## 📋 Cheat Sheet

```bash
# Quick commands for common scenarios

# YouTube video (fast, recommended)
autosub -url "https://youtube.com/..." -fast

# Local video (balanced)
autosub -l "video.mp4" -default

# Professional work (maximum quality)
autosub -l "video.mp4" --model large -quality

# No API key (free)
autosub -l "video.mp4" -budget

# Maximum speed (18x faster!)
autosub -l "video.mp4" --model distil-large -speed

# Specific language
autosub -l "video.mp4" --lang id -fast

# Interactive mode (full control)
autosub -l "video.mp4"
```

---

## 💡 Tips

**For Best Results:**
- Use `distil-small` or `distil-medium` for best speed/accuracy balance
- Use `base` or `small` model for short videos (< 5 min)
- Use `tiny` or `base` model for long videos (faster processing)
- Use `large` or `distil-large` for maximum accuracy
- Enable **Turbo Mode** for YouTube/Podcast (3-6x faster, same accuracy)
- Use DeepSeek AI for better translation quality
- Use GPU acceleration if you have NVIDIA GPU
- Use `minimal` subtitle preset to avoid distracting from video

**Performance:**
- Faster-Whisper is 4-5x faster than Regular Whisper
- **Turbo Mode: 2-3x faster (Regular Whisper), 3-6x faster (Faster-Whisper)**
- **Distil-Whisper is 6x faster than regular models**
- **Combined: Turbo + Distil = up to 18x faster!**
- GPU acceleration is 3-5x faster than CPU for video encoding
- DeepSeek batch processing is 10x faster than Google Translate
- Fast encoding is 2-3x faster than standard quality

**Speed Comparison (17 min video):**
- Regular Whisper (large): ~25 minutes
- Regular Whisper (large) + Turbo: ~10 minutes
- Faster-Whisper (large): ~6 minutes
- Faster-Whisper (large) + Turbo: ~2 minutes
- Faster-Whisper (distil-large): ~1 minute
- **Faster-Whisper (distil-large) + Turbo: ~30 seconds** ⚡

**Troubleshooting:**
- If cuDNN error occurs, the script will automatically fallback to CPU mode
- If GPU not detected, GPU acceleration option will be disabled
- If Piper TTS not installed, use gTTS instead
- Make sure FFmpeg is in PATH for video processing

## 📝 License

MIT License

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📥 YouTube Download

### Automatic Download with yt-dlp

The script attempts to download YouTube videos automatically using yt-dlp.

**Note:** YouTube actively blocks automated downloaders. Success rate varies.

### ⚠️ If Download Fails

**Recommended: Manual Download** (Most Reliable)

1. **Download video manually:**
   - **y2mate.com** (recommended)
   - **savefrom.net**
   - **ssyoutube.com** (add "ss" before youtube.com in URL)
   - Browser extension: Video DownloadHelper

2. **Process with autosub:**
   ```bash
   autosub -l "downloaded_video.mp4" -default
   ```

### 💡 Pro Tip

For best results and reliability, **download videos manually first**, then process with autosub. This avoids YouTube's bot detection and is faster overall.

### 💡 Pro Tip
The fallback system usually works! Just run the command and let it try all methods automatically.

---

## 🐛 Issues

If you encounter any issues, please report them on the GitHub Issues page.
