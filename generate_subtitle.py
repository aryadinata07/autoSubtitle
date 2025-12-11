"""Main script for generating and translating video subtitles"""
import os
import sys
import pysrt

# Disable huggingface symlinks warning on Windows
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

from utils import (
    extract_audio,
    transcribe_audio,
    create_srt,
    translate_subtitles,
    determine_translation_direction,
    embed_subtitle_to_video,
)
from utils.ui import (
    print_header,
    print_info,
    print_summary,
    ask_question,
)


def generate_subtitle(
    video_path,
    output_srt=None,
    model_size="base",
    language=None,
    keep_audio=False,
    translate=False,
    embed_to_video=False,
    use_deepseek=False,
    use_faster_whisper=False,
    embedding_method='standard',
):
    """
    Generate subtitle from video file
    
    Args:
        video_path: Path to video file
        output_srt: Output subtitle file path (default: same name as video with .srt extension)
        model_size: Whisper model size (tiny, base, small, medium, large)
        language: Language code (e.g., 'id' for Indonesian, 'en' for English, None for auto-detect)
        keep_audio: Keep extracted audio file
        translate: Auto-translate subtitle (en->id or id->en)
        embed_to_video: Embed subtitle directly to video
        use_deepseek: Use DeepSeek AI for translation (more accurate)
        use_faster_whisper: Use Faster-Whisper for transcription (4-5x faster)
        embedding_method: Embedding method ('standard', 'fast', 'gpu')
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    # Set default output path
    if output_srt is None:
        output_srt = os.path.splitext(video_path)[0] + ".srt"
    
    # Extract audio
    audio_path = "temp_audio.wav"
    audio_path = extract_audio(video_path, audio_path)
    
    # Verify audio file exists
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Failed to extract audio: {audio_path}")
    
    try:
        # Transcribe
        result = transcribe_audio(audio_path, model_size, language, use_faster=use_faster_whisper)
        detected_lang = result.get("language", "unknown")
        
        # Auto-translate if requested
        if translate:
            # Create temporary subtitle in memory
            import pysrt
            temp_subs = pysrt.SubRipFile()
            
            for i, segment in enumerate(result["segments"], start=1):
                start_sec = segment["start"]
                end_sec = segment["end"]
                
                start_hours = int(start_sec // 3600)
                start_minutes = int((start_sec % 3600) // 60)
                start_seconds = int(start_sec % 60)
                start_millis = int((start_sec % 1) * 1000)
                
                end_hours = int(end_sec // 3600)
                end_minutes = int((end_sec % 3600) // 60)
                end_seconds = int(end_sec % 60)
                end_millis = int((end_sec % 1) * 1000)
                
                text = segment["text"].strip()
                
                sub = pysrt.SubRipItem(
                    index=i,
                    start={
                        "hours": start_hours,
                        "minutes": start_minutes,
                        "seconds": start_seconds,
                        "milliseconds": start_millis,
                    },
                    end={
                        "hours": end_hours,
                        "minutes": end_minutes,
                        "seconds": end_seconds,
                        "milliseconds": end_millis,
                    },
                    text=text,
                )
                temp_subs.append(sub)
            
            # Determine translation direction
            source_lang, target_lang = determine_translation_direction(detected_lang)
            
            # Get DeepSeek API key if using DeepSeek
            deepseek_key = None
            if use_deepseek:
                from dotenv import load_dotenv
                load_dotenv()
                deepseek_key = os.getenv('DEEPSEEK_API_KEY')
            
            # Translate
            translated_subs = translate_subtitles(
                temp_subs, 
                source_lang, 
                target_lang,
                use_deepseek=use_deepseek,
                deepseek_api_key=deepseek_key
            )
            
            # Save temporary subtitle for embedding
            base_name = os.path.splitext(output_srt)[0]
            temp_srt = f"{base_name}_{target_lang}_temp.srt"
            translated_subs.save(temp_srt, encoding="utf-8")
            
            # Embed to video
            output_video = embed_subtitle_to_video(video_path, temp_srt, method=embedding_method)
            
            # Delete temporary SRT file
            if os.path.exists(temp_srt):
                os.remove(temp_srt)
            
            # Print summary
            summary_data = {
                "Input video": video_path,
                "Output video": output_video,
                "Language": f"{detected_lang} → {target_lang.upper()}",
                "Total subtitles": len(result['segments'])
            }
            
            print_summary(summary_data)

        
    finally:
        # Cleanup temporary files
        from utils.ui import print_substep
        if not keep_audio and os.path.exists(audio_path):
            os.remove(audio_path)
            print_substep("Cleaned up temporary audio file")
        
        # Clean up any temp audio files from moviepy
        temp_files = ['temp-audio.m4a', 'temp-audio.m4a.temp']
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass


def parse_arguments():
    """Parse command line arguments"""
    # Parse arguments
    model = "base"
    lang = None
    deepseek_flag = None  # None means ask user
    faster_flag = None  # None means ask user
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--model" and i + 1 < len(sys.argv):
            model = sys.argv[i + 1]
            i += 2
        elif arg == "--lang" and i + 1 < len(sys.argv):
            lang = sys.argv[i + 1]
            i += 2
        elif arg == "--deepseek":
            deepseek_flag = True
            i += 1
        elif arg == "--faster":
            faster_flag = True
            i += 1
        else:
            i += 1
    
    return model, lang, deepseek_flag, faster_flag


def ask_faster_whisper():
    """Ask user if they want to use Faster-Whisper"""
    from utils.ui import console
    
    console.print("\n[bold cyan]Choose Transcription Method:[/bold cyan]")
    
    console.print("\n[bold yellow]1. Regular Whisper (Default)[/bold yellow]")
    console.print("   [green]Kelebihan:[/green]")
    console.print("   [dim]✓ Standard implementation dari OpenAI[/dim]")
    console.print("   [dim]✓ Reliable dan well-tested[/dim]")
    console.print("   [dim]✓ Akurasi bagus untuk semua bahasa[/dim]")
    console.print("   [dim]✓ Tidak perlu install library tambahan[/dim]")
    console.print("   [red]Kekurangan:[/red]")
    console.print("   [dim]✗ Lebih lambat (10 menit video = ~10 menit proses)[/dim]")
    console.print("   [dim]✗ Memory usage lebih tinggi[/dim]")
    
    console.print("\n[bold green]2. Faster-Whisper (Recommended)[/bold green]")
    console.print("   [green]Kelebihan:[/green]")
    console.print("   [dim]✓ 4-5x lebih cepat (10 menit video = ~2 menit proses)[/dim]")
    console.print("   [dim]✓ Memory usage 50% lebih rendah[/dim]")
    console.print("   [dim]✓ Akurasi sama dengan Regular Whisper[/dim]")
    console.print("   [dim]✓ Support GPU acceleration (CUDA)[/dim]")
    console.print("   [dim]✓ Optimized dengan CTranslate2[/dim]")
    console.print("   [red]Kekurangan:[/red]")
    console.print("   [dim]✗ Perlu install faster-whisper library[/dim]")
    
    while True:
        console.print("\n[bold yellow]?[/bold yellow] [white]Choose option (1 or 2):[/white] ", end="")
        choice = input().strip()
        if choice == "1":
            return False
        elif choice == "2":
            return True
        else:
            console.print("[yellow]Please enter 1 or 2[/yellow]")


def ask_deepseek():
    """Ask user if they want to use DeepSeek for translation"""
    from utils.ui import console
    
    console.print("\n[bold cyan]Choose Translation Method:[/bold cyan]")
    
    console.print("\n[bold yellow]1. Google Translate (Default - Free)[/bold yellow]")
    console.print("   [green]Kelebihan:[/green]")
    console.print("   [dim]✓ Gratis, tidak perlu API key[/dim]")
    console.print("   [dim]✓ Cepat dan reliable[/dim]")
    console.print("   [dim]✓ Bagus untuk terjemahan basic[/dim]")
    console.print("   [red]Kekurangan:[/red]")
    console.print("   [dim]✗ Kadang terlalu literal/kaku[/dim]")
    console.print("   [dim]✗ Tidak context-aware[/dim]")
    
    console.print("\n[bold green]2. DeepSeek AI (Recommended)[/bold green]")
    console.print("   [green]Kelebihan:[/green]")
    console.print("   [dim]✓ Lebih natural dan conversational[/dim]")
    console.print("   [dim]✓ Context-aware (paham topik video)[/dim]")
    console.print("   [dim]✓ Batch processing (10x lebih cepat)[/dim]")
    console.print("   [dim]✓ Hasil terjemahan lebih enak dibaca[/dim]")
    console.print("   [red]Kekurangan:[/red]")
    console.print("   [dim]✗ Perlu API key (tapi sangat murah)[/dim]")
    
    while True:
        console.print("\n[bold yellow]?[/bold yellow] [white]Choose option (1 or 2):[/white] ", end="")
        choice = input().strip()
        if choice == "1":
            return False
        elif choice == "2":
            return True
        else:
            console.print("[yellow]Please enter 1 or 2[/yellow]")


def ask_embedding_method():
    """Ask user for embedding method"""
    from utils.ui import console
    
    console.print("\n[bold cyan]Choose Embedding Method:[/bold cyan]")
    
    console.print("\n[bold yellow]1. Standard Quality (Default)[/bold yellow]")
    console.print("   [green]Kelebihan:[/green]")
    console.print("   [dim]✓ Kualitas terbaik[/dim]")
    console.print("   [dim]✓ Compatible dengan semua player[/dim]")
    console.print("   [red]Kekurangan:[/red]")
    console.print("   [dim]✗ Paling lambat (~12-13 menit untuk video 17 menit)[/dim]")
    
    console.print("\n[bold green]2. Fast Encoding (Recommended)[/bold green]")
    console.print("   [green]Kelebihan:[/green]")
    console.print("   [dim]✓ 2-3x lebih cepat (~4-6 menit untuk video 17 menit)[/dim]")
    console.print("   [dim]✓ Kualitas masih bagus[/dim]")
    console.print("   [dim]✓ File size sedikit lebih besar[/dim]")
    console.print("   [red]Kekurangan:[/red]")
    console.print("   [dim]✗ Kualitas sedikit turun (barely noticeable)[/dim]")
    
    console.print("\n[bold magenta]3. GPU Accelerated (Fastest)[/bold magenta]")
    console.print("   [green]Kelebihan:[/green]")
    console.print("   [dim]✓ 3-5x lebih cepat (~2-3 menit untuk video 17 menit)[/dim]")
    console.print("   [dim]✓ Kualitas hampir sama dengan standard[/dim]")
    console.print("   [red]Kekurangan:[/red]")
    console.print("   [dim]✗ Butuh NVIDIA GPU[/dim]")
    
    while True:
        console.print("\n[bold yellow]?[/bold yellow] [white]Choose option (1, 2, or 3):[/white] ", end="")
        choice = input().strip()
        if choice == "1":
            return 'standard'
        elif choice == "2":
            return 'fast'
        elif choice == "3":
            return 'gpu'
        else:
            console.print("[yellow]Please enter 1, 2, or 3[/yellow]")


def ask_video_source():
    """Ask user for video source"""
    from utils.ui import console
    
    console.print("\n[bold cyan]Choose Video Source:[/bold cyan]")
    console.print("\n[bold yellow]1. Local File[/bold yellow]")
    console.print("   [dim]Video file dari komputer lo[/dim]")
    
    console.print("\n[bold green]2. YouTube URL[/bold green]")
    console.print("   [dim]Download video dari YouTube[/dim]")
    console.print("   [dim]Otomatis download kualitas terbaik[/dim]")
    
    while True:
        console.print("\n[bold yellow]?[/bold yellow] [white]Choose option (1 or 2):[/white] ", end="")
        choice = input().strip()
        if choice == "1":
            return "local"
        elif choice == "2":
            return "youtube"
        else:
            console.print("[yellow]Please enter 1 or 2[/yellow]")


def get_youtube_url():
    """Get YouTube URL from user"""
    from utils.ui import console
    
    while True:
        console.print("\n[bold yellow]?[/bold yellow] [white]Enter YouTube URL:[/white] ", end="")
        url = input().strip()
        
        if url:
            from utils.youtube_downloader import is_youtube_url
            if is_youtube_url(url):
                return url
            else:
                console.print("[yellow]Invalid YouTube URL. Please try again.[/yellow]")
        else:
            console.print("[yellow]URL cannot be empty[/yellow]")


def get_local_file():
    """Get local file path from user"""
    from utils.ui import console
    
    while True:
        console.print("\n[bold yellow]?[/bold yellow] [white]Enter video file path:[/white] ", end="")
        file_path = input().strip()
        
        if file_path:
            if os.path.exists(file_path):
                return file_path
            else:
                console.print(f"[yellow]File not found: {file_path}[/yellow]")
                console.print("[yellow]Please enter a valid file path[/yellow]")
        else:
            console.print("[yellow]File path cannot be empty[/yellow]")


def main():
    """Main entry point"""
    model, lang, deepseek_flag, faster_flag = parse_arguments()
    
    # Ask for video source
    video_source = ask_video_source()
    
    if video_source == "youtube":
        # Get YouTube URL
        youtube_url = get_youtube_url()
        
        # Download YouTube video
        from utils.youtube_downloader import download_youtube_video
        try:
            video_file = download_youtube_video(youtube_url)
        except Exception as e:
            from utils.ui import print_error
            print_error(f"Failed to download YouTube video: {str(e)}")
            sys.exit(1)
    else:
        # Get local file path
        video_file = get_local_file()
    
    # Default: always translate and embed
    translate_flag = True
    embed_flag = True
    
    # Ask about Faster-Whisper if not set via command line
    if faster_flag is None:
        faster_flag = ask_faster_whisper()
    
    # Ask about DeepSeek if not set via command line
    if deepseek_flag is None:
        deepseek_flag = ask_deepseek()
    
    # Ask about embedding method
    embedding_method = ask_embedding_method()
    
    print_header("AUTO SUBTITLE GENERATOR")
    print_info("Video", video_file)
    print_info("Model", model)
    print_info("Language", lang if lang else "auto-detect")
    print_info("Transcriber", "Faster-Whisper" if faster_flag else "Regular Whisper")
    print_info("Translator", "DeepSeek AI" if deepseek_flag else "Google Translate")
    
    # Show embedding method
    embedding_names = {
        'standard': 'Standard Quality',
        'fast': 'Fast Encoding',
        'gpu': 'GPU Accelerated'
    }
    print_info("Embedding", embedding_names.get(embedding_method, embedding_method))
    print_info("Output", "Video with embedded subtitle")
    
    try:
        generate_subtitle(
            video_file, 
            model_size=model, 
            language=lang, 
            translate=translate_flag,
            embed_to_video=embed_flag,
            use_deepseek=deepseek_flag,
            use_faster_whisper=faster_flag,
            embedding_method=embedding_method
        )
    except KeyboardInterrupt:
        from utils.ui import print_warning
        print_warning("\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        from utils.ui import print_error
        print_error(f"\n{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
