# Auto Subtitle Generator

Generate subtitle otomatis dari video menggunakan Whisper AI.

## Instalasi

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install ffmpeg (diperlukan untuk moviepy):
   - **Windows**: Download dari https://ffmpeg.org/download.html
   - **Linux**: `sudo apt install ffmpeg`
   - **Mac**: `brew install ffmpeg`

## Cara Pakai

### Interactive Mode
```bash
python generate_subtitle.py
```
Script akan menanyakan:
1. **Video source**: Local file atau YouTube URL
2. **File path/URL**: Tergantung pilihan di step 1
3. **Transcription method**: Regular Whisper atau Faster-Whisper
4. **Translation method**: Google Translate atau DeepSeek AI
5. **Embedding method**: Standard, Fast, atau GPU

### Command Line Mode

**YouTube URL:**
```bash
python generate_subtitle.py -url "https://youtube.com/watch?v=..."
```

**Local File:**
```bash
python generate_subtitle.py -l "C:\path\to\video.mp4"
```

**Dengan Options:**
```bash
# YouTube dengan Faster-Whisper dan DeepSeek
python generate_subtitle.py -url "https://youtube.com/..." --faster --deepseek

# Local file dengan model small
python generate_subtitle.py -l "video.mp4" --model small

# Local file dengan bahasa spesifik
python generate_subtitle.py -l "video.mp4" --lang id
```

**Available Options:**
- `-url <url>` atau `--url <url>` - YouTube URL
- `-l <path>` atau `--local <path>` - Local video file path
- `--model <size>` - Model size: tiny, base, small, medium, large
- `--lang <code>` - Language: id, en, atau auto-detect
- `--faster` - Use Faster-Whisper
- `--deepseek` - Use DeepSeek AI for translation

Output: `video_with_subtitle.mp4` (video dengan subtitle ter-embed)

- Jika video bahasa **English** → auto translate ke **Indonesian**
- Jika video bahasa **Indonesian** → auto translate ke **English**
- File SRT tidak disimpan, langsung embed ke video
- YouTube video otomatis download kualitas terbaik

### Translate dengan DeepSeek AI (Lebih Akurat)
```bash
python generate_subtitle.py video.mp4 --deepseek
```
DeepSeek AI memberikan hasil terjemahan yang lebih natural dan akurat dibanding Google Translate.

**Setup DeepSeek:**
1. Copy `.env.example` ke `.env`
2. Isi `DEEPSEEK_API_KEY` dengan API key kamu
3. Get API key dari: https://platform.deepseek.com/

### Dengan Model Tertentu
```bash
python generate_subtitle.py video.mp4 --model small
```

### Dengan Bahasa Spesifik
```bash
python generate_subtitle.py video.mp4 --lang id
```

### Options
- `--model <size>` - Model size: tiny, base, small, medium, large (default: base)
- `--lang <code>` - Language: id, en, atau auto-detect (default: auto)
- `--deepseek` - Use DeepSeek AI for translation (more accurate)

## Model Size

- **tiny**: Paling cepat, akurasi rendah
- **base**: Balance antara speed dan akurasi (default)
- **small**: Akurasi lebih baik
- **medium**: Akurasi tinggi
- **large**: Akurasi terbaik, paling lambat

## Language Codes

- `id` - Bahasa Indonesia
- `en` - English
- Kosongkan untuk auto-detect

## Output

File subtitle (.srt) akan dibuat dengan nama yang sama dengan video.

Contoh:
- Input: `video.mp4`
- Output: `video.srt`

## Output

Script akan menghasilkan:
- `video_with_subtitle.mp4` - Video dengan subtitle ter-embed (hardcoded)
- File SRT tidak disimpan (langsung embed ke video)

## Struktur Project

```
vidio-subtitle/
├── generate_subtitle.py       # Main script
├── utils/
│   ├── __init__.py            # Package initialization
│   ├── audio_extractor.py     # Extract audio from video
│   ├── transcriber.py         # Whisper transcription
│   ├── subtitle_creator.py    # Create SRT files
│   ├── translator.py          # Translation interface
│   ├── translator_google.py   # Google Translate implementation
│   ├── translator_deepseek.py # DeepSeek AI implementation
│   ├── video_embedder.py      # Embed subtitle to video
│   └── ui.py                  # Terminal UI utilities
├── .env                       # API keys configuration
├── .env.example               # Example configuration
├── requirements.txt
└── README.md
```

## Tips

- Untuk video pendek (< 5 menit): gunakan model `base` atau `small`
- Untuk video panjang: gunakan model `tiny` atau `base` untuk lebih cepat
- Untuk akurasi maksimal: gunakan model `large` (butuh RAM besar)
- Translation pakai Google Translate API (gratis)
