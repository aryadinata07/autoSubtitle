"""Main script for generating and translating video subtitles"""
import os
import sys
import pysrt
from pathlib import Path
from dotenv import load_dotenv

# Get script directory (where generate_subtitle.py is located)
SCRIPT_DIR = Path(__file__).parent.absolute()

# Load environment variables from script directory
env_path = SCRIPT_DIR / '.env'
load_dotenv(dotenv_path=env_path)

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
    CheckpointManager,
    cleanup_old_checkpoints,
    handle_transcription_error,
    handle_translation_error,
    handle_video_error,
)
from utils.ui import (
    print_header,
    print_info,
    print_summary,
    ask_question,
)


def get_output_directory():
    """
    Get output directory based on where script is run from
    
    Returns:
        Path: Output directory path
    """
    # Check if running via autosub.bat (has AUTOSUB_USER_DIR env var)
    user_dir_env = os.getenv('AUTOSUB_USER_DIR')
    
    if user_dir_env:
        # Running via autosub.bat - use user's original directory
        current_dir = Path(user_dir_env)
    else:
        # Running directly - use current working directory
        current_dir = Path.cwd()
    
    script_dir = SCRIPT_DIR
    
    # If running from script directory, use 'downloads' folder
    if current_dir == script_dir:
        output_dir = script_dir / 'downloads'
    else:
        # If running from elsewhere, create 'videos' folder in current directory
        output_dir = current_dir / 'videos'
    
    # Create directory if not exists
    output_dir.mkdir(exist_ok=True)
    
    return output_dir


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
    turbo_mode=False,
    embedding_method='standard',
    video_title=None,
    output_dir=None,
    resume=True,
):
    """
    Generate subtitle from video file
    
    Args:
        video_path: Path to video file
        output_srt: Output subtitle file path (default: same name as video with .srt extension)
        model_size: Whisper model size (tiny, base, small, medium, large, distil-small, distil-medium, distil-large)
        language: Language code (e.g., 'id' for Indonesian, 'en' for English, None for auto-detect)
        keep_audio: Keep extracted audio file
        translate: Auto-translate subtitle (en->id or id->en)
        embed_to_video: Embed subtitle directly to video
        use_deepseek: Use DeepSeek AI for translation (more accurate)
        use_faster_whisper: Use Faster-Whisper for transcription (4-5x faster)
        turbo_mode: Enable turbo mode for faster transcription (greedy search)
        embedding_method: Embedding method ('standard', 'fast', 'gpu')
        video_title: Video title (for YouTube videos, used as context for translation)
        output_dir: Output directory for generated files (default: auto-detect)
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    # Get output directory
    if output_dir is None:
        output_dir = get_output_directory()
    
    # Set default output path
    if output_srt is None:
        output_srt = os.path.splitext(video_path)[0] + ".srt"
    
    # Extract audio to script directory (temp file)
    audio_path = str(SCRIPT_DIR / "temp_audio.wav")
    audio_path = extract_audio(video_path, audio_path)
    
    # Verify audio file exists
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Failed to extract audio: {audio_path}")
    
    # Initialize checkpoint manager
    checkpoint = CheckpointManager(video_path) if resume else None
    
    # Check for existing checkpoint
    existing_checkpoint = None
    if checkpoint:
        existing_checkpoint = checkpoint.load()
        if existing_checkpoint:
            from utils.ui import print_warning, print_substep
            print_warning(f"Found previous progress for: {Path(video_path).name}")
            print_substep(f"Last completed step: {existing_checkpoint['step']}")
            print_substep("Resuming from checkpoint...")
    
    try:
        # Step 1: Transcription
        if existing_checkpoint and existing_checkpoint['step'] in ['transcription', 'translation', 'embedding']:
            # Load from checkpoint
            from utils.ui import print_substep, print_success
            print_substep("Loading transcription from checkpoint...")
            result = existing_checkpoint['data']['transcription']
            detected_lang = result.get("language", "unknown")
            print_success(f"Transcription loaded (language: {detected_lang})")
        else:
            # Transcribe
            try:
                result = transcribe_audio(audio_path, model_size, language, use_faster=use_faster_whisper, turbo_mode=turbo_mode)
                detected_lang = result.get("language", "unknown")
                
                # Adjust subtitle timing
                result["segments"] = adjust_subtitle_timing(result["segments"])
                result["segments"] = optimize_subtitle_gaps(result["segments"])
                
                # Save checkpoint
                if checkpoint:
                    checkpoint.save('transcription', {
                        'transcription': result,
                        'detected_lang': detected_lang,
                        'model_size': model_size,
                        'language': language
                    })
            except Exception as e:
                handle_transcription_error(e)
        
        # Step 2: Translation
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
            
            # Check if translation already done
            if existing_checkpoint and existing_checkpoint['step'] in ['translation', 'embedding']:
                # Load translated subtitles from checkpoint
                from utils.ui import print_substep, print_success
                print_substep("Loading translation from checkpoint...")
                
                # Reconstruct translated_subs from checkpoint data
                import pysrt
                translated_subs = pysrt.SubRipFile()
                for sub_data in existing_checkpoint['data']['translated_subs']:
                    sub = pysrt.SubRipItem(
                        index=sub_data['index'],
                        start=sub_data['start'],
                        end=sub_data['end'],
                        text=sub_data['text']
                    )
                    translated_subs.append(sub)
                
                source_lang = existing_checkpoint['data']['source_lang']
                target_lang = existing_checkpoint['data']['target_lang']
                print_success(f"Translation loaded ({source_lang} → {target_lang})")
            else:
                # Determine translation direction
                source_lang, target_lang = determine_translation_direction(detected_lang)
                
                # Get DeepSeek API key if using DeepSeek
                deepseek_key = None
                if use_deepseek:
                    from dotenv import load_dotenv
                    load_dotenv()
                    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
                
                # Translate
                try:
                    translated_subs = translate_subtitles(
                        temp_subs, 
                        source_lang, 
                        target_lang,
                        use_deepseek=use_deepseek,
                        deepseek_api_key=deepseek_key,
                        video_title=video_title
                    )
                    
                    # Save checkpoint
                    if checkpoint:
                        # Convert translated_subs to serializable format
                        subs_data = []
                        for sub in translated_subs:
                            subs_data.append({
                                'index': sub.index,
                                'start': {'hours': sub.start.hours, 'minutes': sub.start.minutes, 
                                         'seconds': sub.start.seconds, 'milliseconds': sub.start.milliseconds},
                                'end': {'hours': sub.end.hours, 'minutes': sub.end.minutes,
                                       'seconds': sub.end.seconds, 'milliseconds': sub.end.milliseconds},
                                'text': sub.text
                            })
                        
                        checkpoint.save('translation', {
                            'transcription': result,
                            'detected_lang': detected_lang,
                            'translated_subs': subs_data,
                            'source_lang': source_lang,
                            'target_lang': target_lang
                        })
                except Exception as e:
                    handle_translation_error(e)
            
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
            
            # Save temporary subtitle for embedding (in script directory)
            temp_srt = str(SCRIPT_DIR / f"temp_subtitle_{target_lang}.srt")
            
            # Hapus file temporary lama jika ada
            if os.path.exists(temp_srt):
                os.remove(temp_srt)
            
            translated_subs.save(temp_srt, encoding="utf-8")
            
            # Determine output video path
            video_filename = Path(video_path).stem
            output_video_name = f"{video_filename}_with_subtitle.mp4"
            output_video_path = str(output_dir / output_video_name)
            
            # Step 3: Video Embedding
            if existing_checkpoint and existing_checkpoint['step'] == 'embedding':
                # Check if output video already exists
                if os.path.exists(output_video_path):
                    from utils.ui import print_substep, print_success
                    print_substep("Video already processed, skipping embedding...")
                    output_video = output_video_path
                    print_success(f"Using existing video: {output_video}")
                else:
                    # Re-embed (file might have been deleted)
                    try:
                        output_video = embed_subtitle_to_video(video_path, temp_srt, output_path=output_video_path, method=embedding_method)
                    except Exception as e:
                        handle_video_error(e)
            else:
                # Embed subtitle to video
                try:
                    output_video = embed_subtitle_to_video(video_path, temp_srt, output_path=output_video_path, method=embedding_method)
                    
                    # Save final checkpoint
                    if checkpoint:
                        checkpoint.save('embedding', {
                            'transcription': result,
                            'detected_lang': detected_lang,
                            'output_video': output_video,
                            'completed': True
                        })
                except Exception as e:
                    handle_video_error(e)
            
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
            
            # Clear checkpoint on success
            if checkpoint:
                checkpoint.clear()
                from utils.ui import print_substep
                print_substep("Checkpoint cleared (process completed successfully)")
            
            # Return output video path for cleanup
            return output_video

        
    finally:
        # Cleanup temporary files
        from utils.ui import print_substep
        if not keep_audio and os.path.exists(audio_path):
            os.remove(audio_path)
            print_substep("Cleaned up temporary audio file")
        
        # Clean up any temp audio files from moviepy (in script directory)
        temp_files = [
            SCRIPT_DIR / 'temp-audio.m4a',
            SCRIPT_DIR / 'temp-audio.m4a.temp'
        ]
        for temp_file in temp_files:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except:
                    pass


def parse_arguments():
    """Parse command line arguments"""
    # Parse arguments
    model = "base"
    lang = None
    deepseek_flag = None  # None means ask user
    faster_flag = None  # None means ask user
    turbo_flag = None  # None means ask user
    video_source = None  # None means ask user
    video_input = None  # URL or file path
    use_defaults = False  # Flag for using default settings
    preset_mode = None  # Preset mode
    no_resume = False  # Disable checkpoint/resume
    
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
        elif arg == "--turbo":
            turbo_flag = True
            i += 1
        elif arg in ["--no-resume", "--no-checkpoint"]:
            no_resume = True
            i += 1
        elif arg in ["-default", "--default"]:
            preset_mode = "default"
            i += 1
        elif arg in ["-fast", "--fast"]:
            preset_mode = "fast"
            i += 1
        elif arg in ["-quality", "--quality"]:
            preset_mode = "quality"
            i += 1
        elif arg in ["-speed", "--speed"]:
            preset_mode = "speed"
            i += 1
        elif arg in ["-budget", "--budget"]:
            preset_mode = "budget"
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
    
    return model, lang, deepseek_flag, faster_flag, turbo_flag, video_source, video_input, preset_mode, no_resume





def ask_turbo_mode():
    """Ask user if they want to use turbo mode"""
    from utils.ui import console
    
    console.print("\n[bold cyan]Choose Transcription Mode:[/bold cyan]")
    
    console.print("\n[bold yellow]1. Standard Mode (Default - Accurate)[/bold yellow]")
    console.print("   [green]Pros:[/green]")
    console.print("   [dim]✓ Maximum accuracy (beam search)[/dim]")
    console.print("   [dim]✓ Best for noisy/challenging audio[/dim]")
    console.print("   [dim]✓ Explores 5 possible transcriptions[/dim]")
    console.print("   [red]Cons:[/red]")
    console.print("   [dim]✗ Slower processing time[/dim]")
    
    console.print("\n[bold green]2. Turbo Mode (Recommended for Clear Audio)[/bold green]")
    console.print("   [green]Pros:[/green]")
    console.print("   [dim]✓ 3-6x faster transcription[/dim]")
    console.print("   [dim]✓ Greedy search (instant decisions)[/dim]")
    console.print("   [dim]✓ 99% same accuracy for clear audio[/dim]")
    console.print("   [dim]✓ Perfect for YouTube/Podcast/TEDx[/dim]")
    console.print("   [red]Cons:[/red]")
    console.print("   [dim]✗ Slightly less accurate for very noisy audio[/dim]")
    
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
    
    console.print("\n[bold green]1. DeepSeek AI (Default - Recommended)[/bold green]")
    console.print("   [green]Pros:[/green]")
    console.print("   [dim]✓ More natural and conversational[/dim]")
    console.print("   [dim]✓ Context-aware (understands video topic)[/dim]")
    console.print("   [dim]✓ Batch processing (10x faster)[/dim]")
    console.print("   [dim]✓ Better translation quality[/dim]")
    console.print("   [red]Cons:[/red]")
    console.print("   [dim]✗ Requires API key (but very cheap)[/dim]")
    
    console.print("\n[bold yellow]2. Google Translate (Free Fallback)[/bold yellow]")
    console.print("   [green]Pros:[/green]")
    console.print("   [dim]✓ Free, no API key required[/dim]")
    console.print("   [dim]✓ Fast and reliable[/dim]")
    console.print("   [dim]✓ Good for basic translation[/dim]")
    console.print("   [red]Cons:[/red]")
    console.print("   [dim]✗ Sometimes too literal/stiff[/dim]")
    console.print("   [dim]✗ Not context-aware[/dim]")
    
    while True:
        console.print("\n[bold yellow]?[/bold yellow] [white]Choose option (1 or 2, default=1):[/white] ", end="")
        choice = input().strip()
        if choice == "" or choice == "1":
            return True
        elif choice == "2":
            return False
        else:
            console.print("[yellow]Please enter 1 or 2 (or press Enter for default)[/yellow]")


def ask_embedding_method():
    """Ask user for embedding method"""
    from utils.ui import console
    from utils.video_embedder import check_gpu_available
    
    # Check GPU availability once
    gpu_available = check_gpu_available()
    
    while True:
        console.print("\n[bold cyan]Choose Embedding Method:[/bold cyan]")
        
        console.print("\n[bold cyan]1. Soft Subtitle - INSTANT ⚡[/bold cyan]")
        console.print("   [green]Pros:[/green]")
        console.print("   [dim]✓ INSTANT (1-5 seconds only!)[/dim]")
        console.print("   [dim]✓ No quality loss (stream copy)[/dim]")
        console.print("   [dim]✓ Subtitle can be toggled On/Off[/dim]")
        console.print("   [dim]✓ Perfect for YouTube, PC playback[/dim]")
        console.print("   [red]Cons:[/red]")
        console.print("   [dim]✗ Need to enable in player (VLC: press V)[/dim]")
        console.print("   [dim]✗ Not visible on Instagram/TikTok[/dim]")
        
        console.print("\n[bold yellow]2. Hardsub - Standard Quality[/bold yellow]")
        console.print("   [green]Pros:[/green]")
        console.print("   [dim]✓ Best quality[/dim]")
        console.print("   [dim]✓ Works on all platforms (Instagram, TikTok)[/dim]")
        console.print("   [dim]✓ Subtitle permanently burned in[/dim]")
        console.print("   [red]Cons:[/red]")
        console.print("   [dim]✗ Slowest (~12-13 min for 17 min video)[/dim]")
        
        console.print("\n[bold green]3. Hardsub - Fast Encoding (Default - Recommended)[/bold green]")
        console.print("   [green]Pros:[/green]")
        console.print("   [dim]✓ 3-4x faster (~3-5 min for 17 min video)[/dim]")
        console.print("   [dim]✓ Works on all platforms[/dim]")
        console.print("   [dim]✓ Good quality[/dim]")
        console.print("   [dim]✓ Always visible (no need to enable)[/dim]")
        console.print("   [red]Cons:[/red]")
        console.print("   [dim]✗ Slightly lower quality than standard[/dim]")
        
        # Show GPU option with availability status
        if gpu_available:
            console.print("\n[bold magenta]4. Hardsub - GPU Accelerated ✓ Available[/bold magenta]")
        else:
            console.print("\n[bold magenta]4. Hardsub - GPU Accelerated ✗ Not Available[/bold magenta]")
        
        console.print("   [green]Pros:[/green]")
        console.print("   [dim]✓ Fastest hardsub (~2-3 min for 17 min video)[/dim]")
        console.print("   [dim]✓ Works on all platforms[/dim]")
        console.print("   [dim]✓ Good quality[/dim]")
        console.print("   [red]Cons:[/red]")
        console.print("   [dim]✗ Requires NVIDIA GPU[/dim]")
        
        console.print("\n[bold yellow]?[/bold yellow] [white]Choose option (1, 2, 3, or 4, default=3):[/white] ", end="")
        choice = input().strip()
        
        if choice == "1":
            return 'soft'
        elif choice == "2":
            return 'standard'
        elif choice == "" or choice == "3":
            return 'fast'
        elif choice == "4":
            # Validate GPU availability
            if not gpu_available:
                console.print("\n[bold red]❌ NVIDIA GPU not detected![/bold red]")
                console.print("[yellow]GPU Accelerated encoding requires NVIDIA GPU with CUDA support.[/yellow]")
                console.print("[yellow]Please choose option 1, 2, or 3.[/yellow]")
                console.print("\n[dim]Press Enter to continue...[/dim]")
                input()
                # Loop back to show menu again
                continue
            return 'gpu'
        else:
            console.print("[yellow]Please enter 1, 2, 3, or 4 (or press Enter for default)[/yellow]")


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
    # Cleanup old checkpoints (older than 7 days)
    try:
        cleanup_old_checkpoints(max_age_days=7)
    except:
        pass  # Ignore cleanup errors
    
    model, lang, deepseek_flag, faster_flag, turbo_flag, video_source, video_input, preset_mode, no_resume = parse_arguments()
    
    # If video source not provided via command line, ask user
    if video_source is None:
        video_source = ask_video_source()
    
    # Get output directory
    output_dir = get_output_directory()
    
    # Process based on video source
    if video_source == "youtube":
        # Get YouTube URL (from command line or ask user)
        if video_input is None:
            youtube_url = get_youtube_url()
        else:
            youtube_url = video_input
        
        # Download YouTube video to output directory
        from utils.youtube_downloader import download_youtube_video
        try:
            # Download to output directory
            video_file, video_title = download_youtube_video(youtube_url, output_path=str(output_dir))
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
    
    # Check if using preset mode
    if preset_mode:
        if preset_mode == "default":
            # Balanced: Standard + DeepSeek + Fast Hardsub
            if turbo_flag is None:
                turbo_flag = False
            if deepseek_flag is None:
                deepseek_flag = True
            embedding_method = 'fast'
            print_info("Preset", "Default (Balanced: Standard + DeepSeek + Fast Hardsub)")
        
        elif preset_mode == "fast":
            # Fast: Turbo + DeepSeek + Fast Hardsub
            if turbo_flag is None:
                turbo_flag = True
            if deepseek_flag is None:
                deepseek_flag = True
            embedding_method = 'fast'
            print_info("Preset", "Fast (Turbo + DeepSeek + Fast Hardsub)")
        
        elif preset_mode == "quality":
            # Quality: Standard + DeepSeek + Standard Hardsub
            if turbo_flag is None:
                turbo_flag = False
            if deepseek_flag is None:
                deepseek_flag = True
            embedding_method = 'standard'
            print_info("Preset", "Quality (Standard + DeepSeek + Standard Hardsub)")
        
        elif preset_mode == "speed":
            # Maximum Speed: Turbo + Google + Fast Hardsub
            if turbo_flag is None:
                turbo_flag = True
            if deepseek_flag is None:
                deepseek_flag = False
            embedding_method = 'fast'
            print_info("Preset", "Speed (Turbo + Google + Fast Hardsub)")
        
        elif preset_mode == "budget":
            # Budget: Standard + Google + Fast Hardsub (no API key needed)
            if turbo_flag is None:
                turbo_flag = False
            if deepseek_flag is None:
                deepseek_flag = False
            embedding_method = 'fast'
            print_info("Preset", "Budget (Standard + Google + Fast Hardsub)")
    
    else:
        # Interactive mode - ask user for each option
        # Get Turbo mode from environment variable if not set via command line
        if turbo_flag is None:
            turbo_env = os.getenv('TURBO_MODE', 'ask')
            if turbo_env.lower() == 'true':
                turbo_flag = True
            elif turbo_env.lower() == 'false':
                turbo_flag = False
            else:
                # Ask user
                turbo_flag = ask_turbo_mode()
        
        # Ask about DeepSeek if not set via command line
        if deepseek_flag is None:
            deepseek_flag = ask_deepseek()
        
        # Ask about embedding method
        embedding_method = ask_embedding_method()
    
    print_header("AUTO SUBTITLE GENERATOR")
    print_info("Video", video_file)
    print_info("Output Directory", str(output_dir))
    print_info("Model", model)
    print_info("Language", lang if lang else "auto-detect")
    
    transcriber_name = "Faster-Whisper" if faster_flag else "Regular Whisper"
    if turbo_flag and faster_flag:
        transcriber_name += " [TURBO]"
    print_info("Transcriber", transcriber_name)
    
    print_info("Translator", "DeepSeek AI" if deepseek_flag else "Google Translate")
    

    
    # Show embedding method
    embedding_names = {
        'soft': 'Soft Subtitle (Instant)',
        'standard': 'Hardsub - Standard Quality',
        'fast': 'Hardsub - Fast Encoding',
        'gpu': 'Hardsub - GPU Accelerated'
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
            turbo_mode=turbo_flag,
            embedding_method=embedding_method,
            video_title=video_title if video_source == "youtube" else None,
            output_dir=output_dir,
            resume=not no_resume  # Enable resume by default, disable if --no-resume flag
        )
        
        # Clean up original YouTube video after successful generation
        if video_source == "youtube" and output_video:
            try:
                video_file_path = Path(video_file)
                if video_file_path.exists():
                    video_file_path.unlink()
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
