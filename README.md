# Auto Subtitle Generator

Automatically generate subtitles and voice dubbing for videos using Whisper AI.

## ✨ Features

- 🎯 **Automatic Transcription** - Using OpenAI Whisper (Faster-Whisper by default)
- 🌍 **Auto Translation** - English ↔ Indonesian with Google Translate or DeepSeek AI
- 🎬 **Video Embedding** - Hardcode subtitles directly into video (3 encoding methods)
- 🎤 **Voice Dubbing** - Generate AI voice dubbing (gTTS or Piper TTS)
- 📺 **YouTube Support** - Download and process YouTube videos automatically
- ⚡ **GPU Acceleration** - Support for NVIDIA GPU (CUDA) for faster processing
- 🎨 **Customizable Styling** - Adjust subtitle appearance via .env configuration

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

# Subtitle Styling (minimal, standard, bold)
SUBTITLE_PRESET=minimal

# Subtitle Position (bottom, top, center)
SUBTITLE_POSITION=bottom
```

Get DeepSeek API key from: https://platform.deepseek.com/

## 📖 Usage

### Interactive Mode (Recommended)

```bash
python generate_subtitle.py
```

The script will guide you through:
1. **Video Source** - Local file or YouTube URL
2. **Translation Method** - Google Translate (free) or DeepSeek AI (better quality)
3. **Dubbing Option** - No dubbing, gTTS (fast), or Piper TTS (natural)
4. **Embedding Method** - Standard quality, Fast encoding, or GPU accelerated

### Command Line Mode

**Process YouTube Video:**
```bash
python generate_subtitle.py -url "https://youtube.com/watch?v=..."
```

**Process Local File:**
```bash
python generate_subtitle.py -l "path/to/video.mp4"
```

**With Options:**
```bash
# YouTube with DeepSeek AI translation
python generate_subtitle.py -url "https://youtube.com/..." --deepseek

# Local file with specific model
python generate_subtitle.py -l "video.mp4" --model small

# Local file with specific language
python generate_subtitle.py -l "video.mp4" --lang id
```

**Available Options:**
- `-url <url>` or `--url <url>` - YouTube URL
- `-l <path>` or `--local <path>` - Local video file path
- `--model <size>` - Model size: tiny, base, small, medium, large (default: base)
- `--lang <code>` - Language code: id, en, or auto-detect (default: auto)
- `--deepseek` - Use DeepSeek AI for translation (more accurate)

## 🎯 Features Explained

### 1. Transcription Methods

**Faster-Whisper (Default)**
- ✅ 4-5x faster than regular Whisper
- ✅ 50% less memory usage
- ✅ Same accuracy as regular Whisper
- ✅ GPU acceleration support

**Regular Whisper**
- ✅ Standard OpenAI implementation
- ✅ Reliable and well-tested
- ⚠️ Slower processing

Configure in `.env`: `WHISPER_MODE=1` (Faster) or `WHISPER_MODE=2` (Regular)

### 2. Translation Methods

**Google Translate (Free)**
- ✅ Free, no API key required
- ✅ Fast and reliable
- ⚠️ Sometimes too literal

**DeepSeek AI (Recommended)**
- ✅ More natural and conversational
- ✅ Context-aware (understands video topic)
- ✅ Batch processing (10x faster)
- ⚠️ Requires API key (very cheap)

### 3. Voice Dubbing (BETA - Experimental)

> ⚠️ **WARNING**: This feature is experimental and disabled by default. Enable in `.env` by setting `ENABLE_DUBBING=true`

**Known Issues:**
- Audio timing may not sync perfectly with video
- Voice quality varies depending on TTS engine
- Significantly increases processing time
- May require additional troubleshooting

**No Dubbing (Default)**
- Only adds subtitle, keeps original audio

**gTTS (Fast)**
- ✅ Free and unlimited
- ✅ Very fast processing
- ⚠️ Robotic voice
- ⚠️ May have timing issues

**pyttsx3 TTS (Offline)**
- ✅ Free and offline
- ✅ No internet required
- ✅ Uses system voices
- ⚠️ Voice quality depends on system
- ⚠️ Limited voice options
- ⚠️ May have timing issues

### 4. Video Embedding Methods

**Standard Quality**
- ✅ Best quality
- ✅ Compatible with all players
- ⚠️ Slowest (~12-13 min for 17 min video)

**Fast Encoding (Recommended)**
- ✅ 2-3x faster (~4-6 min for 17 min video)
- ✅ Still good quality
- ⚠️ Slightly lower quality (barely noticeable)

**GPU Accelerated**
- ✅ 3-5x faster (~2-3 min for 17 min video)
- ✅ Quality almost same as standard
- ⚠️ Requires NVIDIA GPU with CUDA

### 5. Subtitle Styling

Configure in `.env`:

**Presets:**
- `minimal` - Small font, thin outline, doesn't distract from video (Recommended)
- `standard` - Balanced, readable but not too dominant
- `bold` - Large font, thick outline, for better readability

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

| Model | Speed | Accuracy | RAM Usage |
|-------|-------|----------|-----------|
| tiny | ⚡⚡⚡⚡⚡ | ⭐⭐ | ~1 GB |
| base | ⚡⚡⚡⚡ | ⭐⭐⭐ | ~1.5 GB |
| small | ⚡⚡⚡ | ⭐⭐⭐⭐ | ~2.5 GB |
| medium | ⚡⚡ | ⭐⭐⭐⭐⭐ | ~5 GB |
| large | ⚡ | ⭐⭐⭐⭐⭐ | ~10 GB |

## 🌍 Language Codes

- `id` - Indonesian
- `en` - English
- Leave empty for auto-detect

## 📁 Output

The script generates:
- `video_with_subtitle.mp4` - Video with embedded subtitle
- `video_dubbed.mp4` - Video with dubbing (if dubbing option selected)

Translation direction:
- English video → Indonesian subtitle/dubbing
- Indonesian video → English subtitle/dubbing

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

## 💡 Tips

**For Best Results:**
- Use `base` or `small` model for short videos (< 5 min)
- Use `tiny` or `base` model for long videos (faster processing)
- Use `large` model for maximum accuracy (requires more RAM)
- Use DeepSeek AI for better translation quality
- Use Piper TTS for more natural dubbing voice
- Use GPU acceleration if you have NVIDIA GPU
- Use `minimal` subtitle preset to avoid distracting from video

**Performance:**
- Faster-Whisper is 4-5x faster than Regular Whisper
- GPU acceleration is 3-5x faster than CPU for video encoding
- DeepSeek batch processing is 10x faster than Google Translate
- Fast encoding is 2-3x faster than standard quality

**Troubleshooting:**
- If cuDNN error occurs, the script will automatically fallback to CPU mode
- If GPU not detected, GPU acceleration option will be disabled
- If Piper TTS not installed, use gTTS instead
- Make sure FFmpeg is in PATH for video processing

## 📝 License

MIT License

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🐛 Issues

If you encounter any issues, please report them on the GitHub Issues page.
