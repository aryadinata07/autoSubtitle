"""Voice dubbing utilities for video"""
import os
import subprocess
from .ui import print_step, print_substep, print_success, print_error, print_warning


def generate_tts_gtts(text, output_path, lang='id'):
    """Generate TTS audio using gTTS (Google Text-to-Speech)"""
    try:
        from gtts import gTTS
        # Use slow=True for better pronunciation, especially for Indonesian
        tts = gTTS(text=text, lang=lang, slow=True)
        tts.save(output_path)
        return True
    except Exception as e:
        print_error(f"gTTS error: {str(e)}")
        return False


def generate_tts_piper(text, output_path, lang='id'):
    """Generate TTS audio using pyttsx3 (offline TTS)"""
    try:
        # Use pyttsx3 as alternative (offline TTS)
        import pyttsx3
        
        engine = pyttsx3.init()
        
        # Set properties first
        engine.setProperty('rate', 130)  # Slower speed for better clarity (default is 200)
        engine.setProperty('volume', 1.0)  # Volume
        
        # Set voice based on language
        voices = engine.getProperty('voices')
        voice_set = False
        
        # Try to find appropriate voice
        for voice in voices:
            voice_name_lower = voice.name.lower()
            # For Indonesian, try to find Indonesian voice
            if lang == 'id':
                if 'indonesia' in voice_name_lower or 'id-id' in voice_name_lower:
                    engine.setProperty('voice', voice.id)
                    voice_set = True
                    print_substep(f"Using voice: {voice.name}")
                    break
            # For English, prefer female voice for better clarity
            elif lang == 'en':
                if 'zira' in voice_name_lower or 'hazel' in voice_name_lower:
                    engine.setProperty('voice', voice.id)
                    voice_set = True
                    print_substep(f"Using voice: {voice.name}")
                    break
        
        # If no specific voice found, use default
        if not voice_set and voices:
            engine.setProperty('voice', voices[0].id)
            print_substep(f"Using default voice: {voices[0].name}")
        
        # Save to file
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        
        return True
            
    except ImportError:
        print_error("pyttsx3 not found!")
        print_substep("Please install: pip install pyttsx3")
        return False
    except Exception as e:
        print_error(f"TTS error: {str(e)}")
        return False


def create_dubbed_audio(segments, method='gtts', target_lang='id'):
    """
    Create dubbed audio from subtitle segments
    
    Args:
        segments: List of subtitle segments with text, start, end times
        method: TTS method ('gtts' or 'piper')
        target_lang: Target language code
    
    Returns:
        Path to generated audio file
    """
    print_step(3, 4, f"Generating voice dubbing ({method.upper()})")
    
    import tempfile
    from pydub import AudioSegment
    from pydub.silence import detect_silence
    
    # Create temporary directory for audio chunks
    temp_dir = tempfile.mkdtemp()
    audio_chunks = []
    
    print_substep(f"Processing {len(segments)} segments...")
    
    for i, segment in enumerate(segments):
        text = segment['text'].strip()
        start_time = segment['start'] * 1000  # Convert to milliseconds
        end_time = segment['end'] * 1000
        duration = end_time - start_time
        
        if not text:
            continue
        
        # Generate TTS for this segment
        chunk_path = os.path.join(temp_dir, f"chunk_{i}.mp3")
        
        if method == 'gtts':
            success = generate_tts_gtts(text, chunk_path, target_lang)
        elif method == 'piper':
            success = generate_tts_piper(text, chunk_path, target_lang)
        else:
            print_error(f"Unknown TTS method: {method}")
            return None
        
        if not success:
            continue
        
        # Load generated audio
        try:
            audio = AudioSegment.from_file(chunk_path)
            
            # Don't adjust speed - let audio play at natural pace
            # If audio is longer than subtitle duration, that's okay
            # The overlay will handle it naturally
            
            # Add to chunks with timing
            audio_chunks.append({
                'audio': audio,
                'start': start_time,
                'end': end_time
            })
            
        except Exception as e:
            print_warning(f"Failed to process chunk {i}: {str(e)}")
            continue
    
    if not audio_chunks:
        print_error("No audio chunks generated!")
        return None
    
    print_substep("Merging audio chunks...")
    
    # Get total duration from last segment
    total_duration = max(chunk['end'] for chunk in audio_chunks)
    
    # Create silent base audio
    final_audio = AudioSegment.silent(duration=total_duration)
    
    # Overlay all chunks at their respective positions
    for chunk in audio_chunks:
        final_audio = final_audio.overlay(chunk['audio'], position=chunk['start'])
    
    # Export final audio
    output_path = "dubbed_audio.wav"
    final_audio.export(output_path, format="wav")
    
    # Cleanup temp files
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    print_success(f"Dubbed audio created: {output_path}")
    return output_path


def mix_audio_with_video(video_path, dubbed_audio_path, output_path=None, original_volume=0.1):
    """
    Mix dubbed audio with video, reducing original audio volume
    
    Args:
        video_path: Path to input video
        dubbed_audio_path: Path to dubbed audio
        output_path: Path to output video
        original_volume: Volume of original audio (0.0 to 1.0, default 0.1 = 10%)
    """
    if output_path is None:
        base_name = os.path.splitext(video_path)[0]
        output_path = f"{base_name}_dubbed.mp4"
    
    print_step(4, 4, "Mixing dubbed audio with video")
    
    # FFmpeg command to mix audio
    # Lower original audio volume and add dubbed audio
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-i', dubbed_audio_path,
        '-filter_complex',
        f'[0:a]volume={original_volume}[a1];[a1][1:a]amix=inputs=2:duration=first[aout]',
        '-map', '0:v',
        '-map', '[aout]',
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-y',
        output_path
    ]
    
    print_substep("Processing video with dubbed audio...")
    
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            print_error(f"FFmpeg error: {result.stderr}")
            raise Exception("Failed to mix audio with video")
        
        print_success(f"Dubbed video saved to {output_path}")
        return output_path
        
    except FileNotFoundError:
        print_error("ffmpeg not found!")
        print_substep("Please make sure ffmpeg is installed and in PATH")
        raise
    except Exception as e:
        print_error(f"Error mixing audio: {str(e)}")
        raise
