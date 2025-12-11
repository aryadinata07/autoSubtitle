"""Faster Whisper transcription implementation"""
import os
from faster_whisper import WhisperModel
from .ui import print_step, print_substep, print_success, print_error


def transcribe_audio_faster(audio_path, model_size="base", language=None):
    """
    Transcribe audio using Faster-Whisper (optimized version)
    
    Features:
    - 4-5x faster than regular Whisper
    - Lower memory usage
    - Same accuracy
    - Uses CTranslate2 optimization
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    print_step(2, 3, f"Loading Faster-Whisper model ({model_size})")
    print_substep("This may take a while on first run (downloading model)...")
    print_substep("Using optimized CTranslate2 backend (4-5x faster)...")
    
    # Load model with CPU or GPU
    # Check if user wants to force CPU mode (for cuDNN issues)
    force_cpu = os.environ.get('CUDA_VISIBLE_DEVICES') == '-1'
    
    if force_cpu:
        print_substep("Forcing CPU mode (CUDA_VISIBLE_DEVICES=-1)")
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
    else:
        try:
            # Try GPU first
            model = WhisperModel(model_size, device="cuda", compute_type="float16")
            print_substep("Using GPU acceleration")
        except Exception as e:
            # Fallback to CPU if GPU fails
            print_substep(f"GPU initialization failed: {str(e)[:50]}...")
            print_substep("Falling back to CPU mode")
            model = WhisperModel(model_size, device="cpu", compute_type="int8")
    
    print_success("Model loaded successfully")
    
    print_substep(f"Transcribing audio...")
    print_substep(f"Language: {language if language else 'auto-detect'}")
    print_substep(f"Please wait, this may take a few minutes...")
    
    # Transcribe
    try:
        segments, info = model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True,  # Voice activity detection
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        # Convert segments to list
        result_segments = []
        for segment in segments:
            result_segments.append({
                'start': segment.start,
                'end': segment.end,
                'text': segment.text
            })
        
        detected_lang = info.language if hasattr(info, 'language') else 'unknown'
        
    except Exception as e:
        print_error("Transcription failed!")
        print_substep(f"Error: {str(e)}")
        print_substep("\nPossible solutions:")
        print_substep("1. Make sure ffmpeg is installed and in PATH")
        print_substep("2. Restart your terminal/PowerShell")
        print_substep("3. Try: refreshenv (if using Chocolatey)")
        raise
    
    print_success("Transcription complete!")
    print_substep(f"Detected language: {detected_lang}")
    print_substep(f"Total segments: {len(result_segments)}")
    
    return {
        'language': detected_lang,
        'segments': result_segments
    }
