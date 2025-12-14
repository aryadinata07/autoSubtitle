"""Main script for generating and translating video subtitles"""
import os
import sys
import pysrt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Disable huggingface symlinks warning on Windows
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

from utils import (
    extract_audio,
    transcribe_audio,
    create_srt,
    translate_subtitles,
    determine_translation_direction,
    embed_subtitle_to_video,
    adjust_subtitle_timing,
    optimize_subtitle_gaps,
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
    video_title=None,
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
        video_title: Video title (for YouTube videos, used as context for translation)
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
        
        # Adjust subtitle timing
        result["segments"] = adjust_subtitle_timing(result["segments"])
        result["segments"] = optimize_subtitle_gaps(result["segments"])
        
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
                deepseek_api_key=deepseek_key,
                video_title=video_title
            )
            
            # Apply styling to translated subtitles (with auto-detection)
            from utils.subtitle_creator import get_subtitle_styling
            style = get_subtitle_styling(video_path)
            
            # Apply ASS styling tags to each subtitle
            for sub in translated_subs:
                text = sub.text.strip()
                styling = (
                    f"{{\\fs{style['font_size']}"
                    f"\\b0"
                    f"\\c&HFFFFFF&"
                    f"\\3c&H000000&"
                    f"\\bord{style['outline']}"
                    f"\\shad{style['shadow']}"
                    f"\\a{style['alignment']}"
                    f"\\MarginV={style['margin_v']}}}"
                )
                sub.text = f"{styling}{text}"
            
            # Save temporary subtitle for embedding
            base_name = os.path.splitext(output_srt)[0]
            temp_srt = f"{base_name}_{target_lang}_temp.srt"
            
            # Hapus file temporary lama jika ada
            if os.path.exists(temp_srt):
                os.remove(temp_srt)
            
            translated_subs.save(temp_srt, encoding="utf-8")
            
            # Embed subtitle to video
            output_video = embed_subtitle_to_video(video_path, temp_srt, method=embedding_method)
            
            # Cleanup temporary files
            from utils.ui import print_substep
            
            # Delete temporary SRT file
            if os.path.exists(temp_srt):
                os.remove(temp_srt)
                print_substep("Cleaned up temporary subtitle file")
            
            # Print summary
            summary_data = {
                "Input video": video_path,
                "Output video": output_video,
                "Language": f"{detected_lang} → {target_lang.upper()}",
                "Total subtitles": len(result['segments'])
            }
            
            print_summary(summary_data)
            
            # Return output video path for cleanup
            return output_video

        
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
    video_source = None  # None means ask user
    video_input = None  # URL or file path
    
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
        elif arg in ["-url", "--url"] and i + 1 < len(sys.argv):
            video_source = "youtube"
            video_input = sys.argv[i + 1]
            i += 2
        elif arg in ["-l", "--local"] and i + 1 < len(sys.argv):
            video_source = "local"
            video_input = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    return model, lang, deepseek_flag, faster_flag, video_source, video_input





def ask_deepseek():
    """Ask user if they want to use DeepSeek for translation"""
    from utils.ui import console
    
    console.print("\n[bold cyan]Choose Translation Method:[/bold cyan]")
    
    console.print("\n[bold yellow]1. Google Translate (Default - Free)[/bold yellow]")
    console.print("   [green]Pros:[/green]")
    console.print("   [dim]✓ Free, no API key required[/dim]")
    console.print("   [dim]✓ Fast and reliable[/dim]")
    console.print("   [dim]✓ Good for basic translation[/dim]")
    console.print("   [red]Cons:[/red]")
    console.print("   [dim]✗ Sometimes too literal/stiff[/dim]")
    console.print("   [dim]✗ Not context-aware[/dim]")
    
    console.print("\n[bold green]2. DeepSeek AI (Recommended)[/bold green]")
    console.print("   [green]Pros:[/green]")
    console.print("   [dim]✓ More natural and conversational[/dim]")
    console.print("   [dim]✓ Context-aware (understands video topic)[/dim]")
    console.print("   [dim]✓ Batch processing (10x faster)[/dim]")
    console.print("   [dim]✓ Better translation quality[/dim]")
    console.print("   [red]Cons:[/red]")
    console.print("   [dim]✗ Requires API key (but very cheap)[/dim]")
    
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
    from utils.video_embedder import check_gpu_available
    
    # Check GPU availability once
    gpu_available = check_gpu_available()
    
    while True:
        console.print("\n[bold cyan]Choose Embedding Method:[/bold cyan]")
        
        console.print("\n[bold yellow]1. Standard Quality (Default)[/bold yellow]")
        console.print("   [green]Pros:[/green]")
        console.print("   [dim]✓ Best quality[/dim]")
        console.print("   [dim]✓ Compatible with all players[/dim]")
        console.print("   [red]Cons:[/red]")
        console.print("   [dim]✗ Slowest (~12-13 min for 17 min video)[/dim]")
        
        console.print("\n[bold green]2. Fast Encoding (Recommended)[/bold green]")
        console.print("   [green]Pros:[/green]")
        console.print("   [dim]✓ 2-3x faster (~4-6 min for 17 min video)[/dim]")
        console.print("   [dim]✓ Still good quality[/dim]")
        console.print("   [dim]✓ Slightly larger file size[/dim]")
        console.print("   [red]Cons:[/red]")
        console.print("   [dim]✗ Slightly lower quality (barely noticeable)[/dim]")
        
        # Show GPU option with availability status
        if gpu_available:
            console.print("\n[bold magenta]3. GPU Accelerated (Fastest) ✓ Available[/bold magenta]")
        else:
            console.print("\n[bold magenta]3. GPU Accelerated (Fastest) ✗ Not Available[/bold magenta]")
        
        console.print("   [green]Pros:[/green]")
        console.print("   [dim]✓ 3-5x faster (~2-3 min for 17 min video)[/dim]")
        console.print("   [dim]✓ Quality almost same as standard[/dim]")
        console.print("   [red]Cons:[/red]")
        console.print("   [dim]✗ Requires NVIDIA GPU[/dim]")
        
        console.print("\n[bold yellow]?[/bold yellow] [white]Choose option (1, 2, or 3):[/white] ", end="")
        choice = input().strip()
        
        if choice == "1":
            return 'standard'
        elif choice == "2":
            return 'fast'
        elif choice == "3":
            # Validate GPU availability
            if not gpu_available:
                console.print("\n[bold red]❌ NVIDIA GPU not detected![/bold red]")
                console.print("[yellow]GPU Accelerated encoding requires NVIDIA GPU with CUDA support.[/yellow]")
                console.print("[yellow]Please choose option 1 or 2.[/yellow]")
                console.print("\n[dim]Press Enter to continue...[/dim]")
                input()
                # Loop back to show menu again
                continue
            return 'gpu'
        else:
            console.print("[yellow]Please enter 1, 2, or 3[/yellow]")


def ask_video_source():
    """Ask user for video source"""
    from utils.ui import console
    
    console.print("\n[bold cyan]Choose Video Source:[/bold cyan]")
    console.print("\n[bold yellow]1. Local File[/bold yellow]")
    console.print("   [dim]Video file from your computer[/dim]")
    
    console.print("\n[bold green]2. YouTube URL[/bold green]")
    console.print("   [dim]Download video from YouTube[/dim]")
    console.print("   [dim]Automatically downloads best quality[/dim]")
    
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
    model, lang, deepseek_flag, faster_flag, video_source, video_input = parse_arguments()
    
    # If video source not provided via command line, ask user
    if video_source is None:
        video_source = ask_video_source()
    
    # Process based on video source
    if video_source == "youtube":
        # Get YouTube URL (from command line or ask user)
        if video_input is None:
            youtube_url = get_youtube_url()
        else:
            youtube_url = video_input
        
        # Download YouTube video
        from utils.youtube_downloader import download_youtube_video
        try:
            video_file, video_title = download_youtube_video(youtube_url)
        except Exception as e:
            from utils.ui import print_error
            print_error(f"Failed to download YouTube video: {str(e)}")
            sys.exit(1)
    else:
        video_title = None  # No title for local files
        # Get local file path (from command line or ask user)
        if video_input is None:
            video_file = get_local_file()
        else:
            video_file = video_input
            # Validate file exists
            if not os.path.exists(video_file):
                from utils.ui import print_error
                print_error(f"Video file not found: {video_file}")
                sys.exit(1)
    
    # Default: always translate and embed
    translate_flag = True
    embed_flag = True
    
    # Get Whisper mode from environment variable (default: Faster-Whisper)
    whisper_mode = os.getenv('WHISPER_MODE', '1')
    faster_flag = True if whisper_mode == '1' else False
    
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
    
    print_info("Output", "Video with subtitle")
    
    try:
        output_video = generate_subtitle(
            video_file, 
            model_size=model, 
            language=lang, 
            translate=translate_flag,
            embed_to_video=embed_flag,
            use_deepseek=deepseek_flag,
            use_faster_whisper=faster_flag,
            embedding_method=embedding_method,
            video_title=video_title if video_source == "youtube" else None
        )
        
        # Clean up original YouTube video after successful generation
        if video_source == "youtube" and output_video:
            try:
                if os.path.exists(video_file):
                    os.remove(video_file)
                    from utils.ui import print_substep
                    print_substep(f"Cleaned up original video: {video_file}")
            except Exception as e:
                from utils.ui import print_warning
                print_warning(f"Failed to delete original video: {str(e)}")
        
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
