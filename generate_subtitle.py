"""
Auto Subtitle Generator
Entry point script.
"""
import os
# Suppress HF Symlink Warning on Windows
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
import sys
from pathlib import Path

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).parent
sys.path.append(str(SCRIPT_DIR))

from core.cli import parse_arguments
from core.runner import process_video_runner, get_output_directory
from utils.system.config_wizard import run_wizard
from utils.system.ui import (
    console, print_header, print_info, print_error, print_warning, print_substep, 
    ask_turbo_mode, ask_deepseek, ask_embedding_method, ask_video_source,
    get_youtube_url, get_local_file, ask_target_language
)
from core.config import load_config
from core.logger import log
import traceback

def main():
    """Main entry point"""
    # Parse arguments
    args = parse_arguments()
    
    # Run configuration wizard if requested
    if args.configure:
        run_wizard()
        return

    # User Interactions & Defaults Logic
    # (Adapted from original logic to map args to runner parameters)
    
    # Check for existing checkpoints logic (To be moved to core/cli or handled here? Handled here is fine for UI flow)
    # But for cleaner code, we might want to move this "Recover Checkpoint" UI to core too.
    # For now, let's keep it minimal.
    
    # Map Args to Variables
    model = args.model
    lang = args.lang
    no_resume = args.no_resume
    
    # Handle Flags (Lazy logic: None means ask user)
    turbo_flag = True if args.turbo else (False if args.accurate else None)
    deepseek_flag = True if args.deepseek else (False if args.google else None)
    faster_flag = True # Defaulting to True as per "Recommended" in CLI, unless --original passed?
    if args.original: faster_flag = False
    if args.faster: faster_flag = True
    
    # Determine Preset
    preset_mode = args.preset
    embedding_method = None
    
    if preset_mode:
        if preset_mode == "default": # Balanced
            if turbo_flag is None: turbo_flag = False
            if deepseek_flag is None: deepseek_flag = True
            embedding_method = 'fast'
        elif preset_mode == "fast":
            if turbo_flag is None: turbo_flag = True
            if deepseek_flag is None: deepseek_flag = True
            embedding_method = 'fast'
        elif preset_mode == "quality": 
            if turbo_flag is None: turbo_flag = False
            if deepseek_flag is None: deepseek_flag = True
            embedding_method = 'standard'
        elif preset_mode == "speed":
            if turbo_flag is None: turbo_flag = True
            if deepseek_flag is None: deepseek_flag = False
            embedding_method = 'fast'
        elif preset_mode == "budget":
            if turbo_flag is None: turbo_flag = False
            if deepseek_flag is None: deepseek_flag = False
            embedding_method = 'fast'
        elif preset_mode == "instant":
            if turbo_flag is None: turbo_flag = False
            if deepseek_flag is None: deepseek_flag = True
            embedding_method = 'soft'
            
    else:
        # Interactive checks
        config = load_config()
        
        if turbo_flag is None:
            turbo_env = config.get('TURBO_MODE', 'ask')
            if turbo_env == 'true': turbo_flag = True
            elif turbo_env == 'false': turbo_flag = False
            else: turbo_flag = ask_turbo_mode()
            
        if deepseek_flag is None:
            # Check explicit config first
            saved_method = config.get('TRANSLATION_METHOD')
            
            if saved_method == 'google':
                deepseek_flag = False
            elif saved_method == 'deepseek':
                deepseek_flag = True
                # Ensure key exists if method is forced
                if not config.get('DEEPSEEK_API_KEY'):
                    deepseek_flag = ask_deepseek()
            else:
                # Legacy/First Run Logic
                api_key = config.get('DEEPSEEK_API_KEY')
                if api_key: 
                    deepseek_flag = True
                    # Auto-migrate to new config style
                    from core.config import save_config
                    save_config('TRANSLATION_METHOD', 'deepseek')
                else:
                    deepseek_flag = ask_deepseek()
                    # Persist user choice
                    from core.config import save_config
                    if deepseek_flag:
                        save_config('TRANSLATION_METHOD', 'deepseek')
                    else:
                        save_config('TRANSLATION_METHOD', 'google')
        
        if embedding_method is None:
            embed_config = config.get('EMBEDDING_METHOD', 'ask')
            if embed_config in ['soft', 'fast', 'gpu']:
                embedding_method = embed_config
            else:
                embedding_method = ask_embedding_method()
                
        # Target Language Logic (Just load config, no ask yet)
        target_lang = config.get('TARGET_LANGUAGE', 'ask')

    # Display Header Info
    output_dir = args.output_dir if args.output_dir else get_output_directory()
    
    print_header("AUTO SUBTITLE GENERATOR")
    print_info("Model", model)
    print_info("Language", lang if lang else "auto-detect")
    print_info("Target Lang", args.target_lang if hasattr(args, 'target_lang') and args.target_lang else (target_lang if 'target_lang' in locals() else 'auto'))
    print_info("Transcriber", f"Faster-Whisper {'[TURBO]' if turbo_flag and faster_flag else ''}")
    print_info("Translator", "DeepSeek AI" if deepseek_flag else "Google Translate")
    print_info("Embedding", embedding_method)

    # Video Source Logic
    video_source = "youtube" if args.youtube else ("local" if args.file else None)
    video_input = args.youtube if args.youtube else (args.file if args.file else None)
    
    # If not provided via CLI, ask user
    if video_source is None:
        video_source_selection = ask_video_source()
        
        # Handle Resume
        if video_source_selection.startswith("resume:"):
            video_input = video_source_selection.split(":", 1)[1]
            print(f"RESUMING: {Path(video_input).name}")
            
            # Infer source type from path (mostly for internal logging)
            if "http" in video_input:
                video_source = 'youtube'
            else:
                video_source = 'local'
                
        # Handle Local
        elif video_source_selection == 'local':
            video_source = 'local'
            video_input = get_local_file()
            
        # Handle YouTube
        elif video_source_selection == 'youtube':
            video_source = 'youtube'
            video_input = get_youtube_url()

    # Process Input (Download or path resolution)
    final_video_path = None
    video_title = None

    if video_source == 'youtube':
        from utils.media.youtube_downloader import download_youtube_video
        try:
            print_substep(f"Downloading YouTube video: {video_input}")
            final_video_path, video_title = download_youtube_video(video_input, output_path=str(output_dir))
        except Exception as e:
            print_error(f"Download failed: {e}")
            sys.exit(1)
    else:
        # Local file
        final_video_path = video_input
        # Infer title from filename for context
        if final_video_path:
            video_title = Path(final_video_path).stem.replace("_", " ").replace("-", " ")

    if not final_video_path or not os.path.exists(final_video_path):
        print_error(f"Invalid video path: {final_video_path}")
        sys.exit(1)
    
    # Run Pipeline
    process_video_runner(
        video_file=str(final_video_path),
        model=model,
        lang=lang,
        translate_flag=True, # Always translate for now as per original
        embed_flag=True, # Always embed
        deepseek_flag=deepseek_flag,
        faster_flag=faster_flag,
        turbo_flag=turbo_flag,
        embedding_method=embedding_method,
        video_title=video_title,
        output_dir=output_dir,
        resume=not no_resume,
        video_source=video_source,
        target_lang=target_lang if 'target_lang' in locals() else None
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[Process cancelled by user]")
        sys.exit(0)
    except Exception as e:
        log.critical("Unhandled exception occurred:")
        log.critical(traceback.format_exc())
        console.print_exception(show_locals=False)
        sys.exit(1)
