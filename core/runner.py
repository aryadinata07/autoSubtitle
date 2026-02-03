"""
Core Runner Module
Handles the main orchestration logic for subtitle generation.
"""
import os
import sys
from pathlib import Path

# Utilities (Lazy import where possible, but some commonly used ones here)
from utils.system.ui import (
    print_header, print_info, print_error, print_warning, 
    print_success, print_substep, print_summary, ask_question,
    print_step
)

# Constants
SCRIPT_DIR = Path(__file__).parent.parent

def get_processing_directory():
    """Get or create hidden processing directory"""
    proc_dir = SCRIPT_DIR / ".processing"
    proc_dir.mkdir(exist_ok=True)
    # Force hide on Windows
    if os.name == 'nt':
        os.system(f'attrib +h "{proc_dir}"')
    return proc_dir

def get_output_directory():
    """Get or create output directory"""
    output_dir = SCRIPT_DIR / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir

def determine_translation_direction(detected_lang):
    """
    Determine source and target language based on detected language
    Default rule: 
    - If detected == 'id' -> Translate to 'en'
    - If detected != 'id' -> Translate to 'id' (Default target)
    """
    if detected_lang == 'id':
        return 'id', 'en'
    else:
        return detected_lang, 'id'

def process_video_runner(video_file, model, lang, translate_flag, embed_flag, deepseek_flag, 
                  faster_flag, turbo_flag, embedding_method, video_title, output_dir, 
                  resume=True, video_source=None, target_lang=None):
    """
    Process video with subtitle generation (Public Interface)
    """
    # Lazy imports
    # Lazy imports
    from utils.system.checkpoint import CheckpointManager
    from utils.media.media import extract_audio, embed_subtitle_to_video
    from utils.ai.transcriber import transcribe_audio
    from utils.system.error_handler import handle_transcription_error, handle_translation_error, handle_video_error
    from utils.ai.timing import adjust_subtitle_timing, optimize_subtitle_gaps, analyze_sentence_structure
    from utils.ai.translator import translate_subtitles
    from utils.media.subtitle_creator import get_subtitle_styling
    import pysrt
    
    # Resolve output directory
    if output_dir is None:
        output_dir = get_output_directory()
    
    # Overwrite Protection
    if embed_flag:
        video_stem = Path(video_file).stem
        expected_output = output_dir / f"{video_stem}_with_subtitle.mp4"
        
        if expected_output.exists():
            print_warning(f"Output file already exists: {expected_output.name}")
            should_overwrite = ask_question("Do you want to overwrite it?")
            
            if not should_overwrite:
                import time
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                print_substep(f"Avoiding overwrite. Will save as: {video_stem}_with_subtitle_{timestamp}.mp4")
                
                backup_name = output_dir / f"{video_stem}_with_subtitle_backup_{timestamp}.mp4"
                try:
                    expected_output.rename(backup_name)
                    print_success(f"Renamed existing file to: {backup_name.name}")
                except Exception as e:
                    print_error(f"Failed to rename file: {e}")
                    sys.exit(1)

    try:
        # Step 0: Initial Validation
        if not os.path.exists(video_file):
            raise FileNotFoundError(f"Video file not found: {video_file}")

        # Initialize checkpoint
        checkpoint = CheckpointManager(video_file) if resume else None
        
        # Check for existing checkpoint
        existing_checkpoint = None
        if checkpoint:
            existing_checkpoint = checkpoint.load()
            if existing_checkpoint:
                print_warning(f"Found previous progress for: {Path(video_file).name}")
                print_substep(f"Last completed step: {existing_checkpoint.get('step', 'unknown')}")
                print_substep("Resuming from checkpoint...")

        # --- Step 1: Audio Extraction --- 
        processing_dir = get_processing_directory()
        audio_path = str(processing_dir / "temp_audio.wav")
        audio_path = extract_audio(video_file, audio_path)

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Failed to extract audio: {audio_path}")
            
        # Audio Enhancement (Premium Mode Only)
        from core.config import load_config
        config = load_config()
        if config.get('FIDELITY_MODE') == 'premium':
            from utils.media.audio_enhancer import enhance_audio
            audio_path = enhance_audio(audio_path)

        # --- Step 2: Transcription ---
        result = None
        detected_lang = lang or "unknown"
        
        if existing_checkpoint and existing_checkpoint.get('step') in ['transcription', 'translation', 'embedding']:
            print_substep("Loading transcription from checkpoint...")
            try:
                result = existing_checkpoint['data'].get('transcription')
                detected_lang = result.get("language", detected_lang)
                print_success(f"Transcription loaded (language: {detected_lang})")
            except:
                 print_warning("Checkpoint corrupt, re-running transcription")
        
        if not result:
            try:
                # --- PREMIUM: Deep Hearing (Two-Stage) ---
                initial_prompt = None
                from core.config import load_config
                config = load_config()
                
                # Check Premium Mode
                if config.get('FIDELITY_MODE') == 'premium' and deepseek_flag:
                    print_step(2, 3, "Deep Hearing™: Two-Stage Transcription Plan")
                    
                    # 1. Draft Pass (Tiny Model)
                    print_substep("Stage 1/2: Draft Transcription (Scanning Context...)")
                    draft_result = transcribe_audio(audio_path, model_size="tiny", language=lang, use_faster=faster_flag, turbo_mode=True)
                    draft_text = " ".join([s['text'] for s in draft_result['segments']])
                    
                    # 2. Context Analysis (Extract Glossary)
                    from utils.ai.context_analyzer import analyze_video_context
                    deepseek_key = config.get('DEEPSEEK_API_KEY')
                    
                    # Infer Title for Context
                    title_context = video_title if video_title else Path(video_file).stem
                    print_substep("Stage 2/2: Extracting Acoustic Glossary...")
                    
                    # Analyze (Re-using context analyzer, which now returns glossary)
                    ai_context = analyze_video_context(title_context, draft_text, deepseek_key)
                    
                    if ai_context and ai_context.get('glossary'):
                        # Build Prompt
                        # Format: "Keywords: Term1, Term2, Term3."
                        terms = list(ai_context['glossary'].keys())
                        initial_prompt = f"Keywords: {', '.join(terms)}."
                        print_success(f"Deep Hearing: Biasing Whisper with {len(terms)} keywords")
                    else:
                        print_substep("No glossary terms found, proceeding normally.")
                
                # --- Final Transcription ---
                print_substep("Running Final High-Fidelity Transcription...")
                result = transcribe_audio(
                    audio_path, model, lang, 
                    use_faster=faster_flag, 
                    turbo_mode=turbo_flag, 
                    initial_prompt=initial_prompt
                )
                
                detected_lang = result.get("language", "unknown")
                
                # AI Timing Adjustment
                if deepseek_flag:
                    deepseek_key = config.get('DEEPSEEK_API_KEY')
                    
                    if deepseek_key:
                        structure_analysis = analyze_sentence_structure(result["segments"], deepseek_key)
                        result["segments"] = adjust_subtitle_timing(result["segments"], structure_analysis)
                    else:
                        result["segments"] = adjust_subtitle_timing(result["segments"])
                else:
                    result["segments"] = adjust_subtitle_timing(result["segments"])
                
                result["segments"] = optimize_subtitle_gaps(result["segments"])
                
                if checkpoint:
                    checkpoint.save('transcription', {
                        'transcription': result,
                        'detected_lang': detected_lang,
                        'model_size': model,
                        'language': lang
                    })
            except Exception as e:
                handle_transcription_error(e)

        # --- Step 3: Translation ---
        translated_subs = None
        if translate_flag:
            # Create temporary subtitle in memory
            temp_subs = pysrt.SubRipFile()
            
            for i, segment in enumerate(result["segments"], start=1):
                start_sec = segment["start"]
                end_sec = segment["end"]
                
                # Convert to pysrt format
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
                        "hours": start_hours, "minutes": start_minutes, "seconds": start_seconds, "milliseconds": start_millis
                    },
                    end={
                        "hours": end_hours, "minutes": end_minutes, "seconds": end_seconds, "milliseconds": end_millis
                    },
                    text=text
                )
                temp_subs.append(sub)
            
            # Check checkpoint for translation
            if existing_checkpoint and existing_checkpoint.get('step') in ['translation', 'embedding']:
                print_substep("Loading translation from checkpoint...")
                try:
                    translated_subs = pysrt.SubRipFile()
                    for sub_data in existing_checkpoint['data']['translated_subs']:
                        sub = pysrt.SubRipItem(
                            index=sub_data['index'],
                            start=sub_data['start'],
                            end=sub_data['end'],
                            text=sub_data['text']
                        )
                        translated_subs.append(sub)
                    source_lang = existing_checkpoint['data'].get('source_lang', detected_lang)
                    target_lang = existing_checkpoint['data'].get('target_lang', target_lang)
                    print_success(f"Translation loaded ({source_lang} -> {target_lang})")
                except:
                    print_warning("Checkpoint translation data invalid, re-translating...")
                    translated_subs = None

            if not translated_subs:
                # Perform Translation
                if not target_lang or target_lang == 'ask':
                    # Interactive Ask (Just-in-Time)
                    from utils.system.ui import ask_target_language
                    target_lang = ask_target_language(detected_lang)
                    source_lang = detected_lang
                else:
                    # Respect explicit target language
                    source_lang = detected_lang
                    
                deepseek_key = None
                if deepseek_flag:
                    from core.config import load_config
                    config = load_config()
                    deepseek_key = config.get('DEEPSEEK_API_KEY')
                
                if source_lang == target_lang:
                    print_info("Translation", f"Skipping translation ({source_lang} -> {target_lang})")
                    translated_subs = temp_subs
                else: 
                    try:
                        translated_subs = translate_subtitles(
                            temp_subs, 
                            source_lang, 
                            target_lang,
                            use_deepseek=deepseek_flag,
                            deepseek_api_key=deepseek_key,
                            video_title=video_title
                        )
                    
                    # Save checkpoint
                        if checkpoint:
                            # Serialize
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
            
            # Apply Styling
            style = get_subtitle_styling(video_file)
            for sub in translated_subs:
                text = sub.text.strip()
                styling = (
                    f"{{\\fs{style['font_size']}\\b0\\c&HFFFFFF&\\3c&H000000&"
                    f"\\bord{style['outline']}\\shad{style['shadow']}\\a{style['alignment']}"
                    f"\\MarginV={style['margin_v']}}}"
                )
                sub.text = f"{styling}{text}"
            
            # Save Temp SRT
            temp_srt = str(processing_dir / f"temp_subtitle_{target_lang}.srt")
            if os.path.exists(temp_srt):
                os.remove(temp_srt)
            translated_subs.save(temp_srt, encoding="utf-8")
            
            # --- Step 4: Embedding ---
            video_filename = Path(video_file).stem
            output_video_name = f"{video_filename}_with_subtitle.mp4"
            output_video_path = str(output_dir / output_video_name)
            
            if existing_checkpoint and existing_checkpoint.get('step') == 'embedding':
                if os.path.exists(output_video_path):
                     print_substep("Video already processed, skipping embedding...")
                     output_video = output_video_path
                     print_success(f"Using existing video: {output_video}")
                else:
                    try:
                        output_video = embed_subtitle_to_video(video_file, temp_srt, output_path=output_video_path, method=embedding_method)
                    except Exception as e:
                        handle_video_error(e)
            else:
                 try:
                    output_video = embed_subtitle_to_video(video_file, temp_srt, output_path=output_video_path, method=embedding_method)
                    if checkpoint:
                        checkpoint.save('embedding', {
                            'transcription': result,
                            'detected_lang': detected_lang,
                            'output_video': output_video,
                            'completed': True
                        })
                 except Exception as e:
                    handle_video_error(e)

            # Cleanup Temp SRT
            if os.path.exists(temp_srt):
                os.remove(temp_srt)
                print_substep("Cleaned up temporary subtitle file")
            
            # Final Summary
            summary_data = {
                "Input video": video_file,
                "Output video": output_video,
                "Language": f"{detected_lang} -> {target_lang.upper()}",
                "Total subtitles": len(result['segments'])
            }
            print_summary(summary_data)
            
            if checkpoint:
                checkpoint.clear()
                print_substep("Checkpoint cleared")
            
            return output_video

    except KeyboardInterrupt:
        print_warning("\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n{str(e)}")
        sys.exit(1)
        
    finally:
        # Cleanup audio
        if 'audio_path' in locals() and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                print_substep("Cleaned up temporary audio file")
            except:
                pass
        
        # Cleanup enhanced audio if exists
        if 'audio_path' in locals():
            enhanced_path = str(Path(audio_path).parent / "temp_audio_enhanced.wav")
            if os.path.exists(enhanced_path):
                try: os.remove(enhanced_path); print_substep("Cleaned up enhanced audio file")
                except: pass

        # Helper method for temp audio cleaning
        processing_dir = SCRIPT_DIR / ".processing"
        if processing_dir.exists():
            import shutil
            try:
                # Remove all files in processing dir
                for item in processing_dir.iterdir():
                    if item.is_file():
                        item.unlink()
                # Optionally remove the dir itself if really empty
                # processing_dir.rmdir() 
                print_substep("Cleaned up processing directory")
            except Exception as e:
                # print_warning(f"Cleanup warning: {e}")
                pass
