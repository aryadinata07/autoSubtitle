"""Audio transcription utilities - Main interface"""
from .ui import print_step, print_substep, print_success, print_warning


def transcribe_audio(audio_path, model_size="base", language=None, use_faster=False, turbo_mode=False):
    """
    Transcribe audio using selected Whisper implementation
    
    Args:
        audio_path: Path to audio file
        model_size: Model size (tiny, base, small, medium, large, distil-small, distil-medium, distil-large)
        language: Language code (en, id, or None for auto-detect)
        use_faster: Use Faster-Whisper (True) or regular Whisper (False)
        turbo_mode: Enable turbo mode for faster transcription (only for Faster-Whisper)
    """
    if use_faster:
        try:
            from .transcriber_faster import transcribe_audio_faster
            return transcribe_audio_faster(audio_path, model_size, language, turbo_mode=turbo_mode)
        except ImportError:
            print_warning("faster-whisper not installed, falling back to regular Whisper")
            print_substep("Install with: pip install faster-whisper")
            from .transcriber_whisper import transcribe_audio_whisper
            return transcribe_audio_whisper(audio_path, model_size, language, turbo_mode=turbo_mode)
    else:
        from .transcriber_whisper import transcribe_audio_whisper
        return transcribe_audio_whisper(audio_path, model_size, language, turbo_mode=turbo_mode)

