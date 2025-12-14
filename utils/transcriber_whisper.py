"""Regular Whisper transcription implementation"""
import os
import whisper
from .ui import print_step, print_substep, print_success, print_error


def transcribe_audio_whisper(audio_path, model_size="base", language=None, turbo_mode=False):
    """
    Transcribe audio using regular Whisper
    
    Features:
    - Standard Whisper implementation
    - Reliable and well-tested
    - Good accuracy
    - Turbo Mode: 2-3x faster with greedy decoding
    
    Args:
        audio_path: Path to audio file
        model_size: Model size (tiny, base, small, medium, large)
        language: Language code (en, id, or None for auto-detect)
        turbo_mode: Enable turbo mode (greedy decoding, faster but slightly less accurate for noisy audio)
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    mode_info = " [TURBO MODE]" if turbo_mode else ""
    print_step(2, 3, f"Loading Whisper model ({model_size}){mode_info}")
    print_substep("This may take a while on first run (downloading model)...")
    model = whisper.load_model(model_size)
    print_success("Model loaded successfully")
    
    if turbo_mode:
        print_substep("Turbo Mode: Greedy decoding enabled (2-3x faster)")
    
    print_substep(f"Transcribing audio...")
    print_substep(f"Language: {language if language else 'auto-detect'}")
    print_substep(f"Please wait, this may take a few minutes...")
    
    # Transcribe with progress callback
    try:
        # Configure parameters based on mode
        if turbo_mode:
            # TURBO MODE: Greedy decoding for maximum speed
            # beam_size=None means greedy (fastest)
            # best_of=1 means no sampling (deterministic)
            result = model.transcribe(
                audio_path,
                language=language,
                verbose=False,
                fp16=False,
                beam_size=None,  # Greedy decoding (fastest)
                best_of=1,       # No sampling
                temperature=0.0  # Deterministic
            )
        else:
            # STANDARD MODE: Beam search for maximum accuracy
            result = model.transcribe(
                audio_path,
                language=language,
                verbose=False,  # Hide detailed output
                fp16=False  # Better compatibility
            )
    except Exception as e:
        print_error("Transcription failed!")
        print_substep(f"Error: {str(e)}")
        print_substep("\nPossible solutions:")
        print_substep("1. Make sure ffmpeg is installed and in PATH")
        print_substep("2. Restart your terminal/PowerShell")
        print_substep("3. Try: refreshenv (if using Chocolatey)")
        raise
    
    print_success("Transcription complete!")
    print_substep(f"Detected language: {result.get('language', 'unknown')}")
    print_substep(f"Total segments: {len(result['segments'])}")
    return result
