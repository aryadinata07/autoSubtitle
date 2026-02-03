"""
Audio transcription utilities - Main interface
Consolidates Faster-Whisper and Regular Whisper implementations.
"""
import os
from typing import Optional, Dict, Any

from utils.system.ui import print_step, print_substep, print_success, print_warning, print_error

# Map distil models to actual model names
DISTIL_MAP = {
    'distil-small': 'distil-whisper/distil-small.en',
    'distil-medium': 'distil-whisper/distil-medium.en',
    'distil-large': 'distil-whisper/distil-large-v3'
}

def transcribe_audio(
    audio_path: str, 
    model_size: str = "base", 
    language: Optional[str] = None, 
    use_faster: bool = False, 
    turbo_mode: bool = False,
    initial_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transcribe audio using selected Whisper implementation (Standard or Faster-Whisper).

    Args:
        audio_path (str): Path to audio file.
        model_size (str): Model size (tiny, base, small, medium, large, distil-small, distil-medium, distil-large).
        language (Optional[str]): Language code (e.g., 'en', 'id') or None for auto-detect.
        use_faster (bool): Use Faster-Whisper (True) or regular Whisper (False).
        turbo_mode (bool): Enable turbo mode for faster transcription.
        initial_prompt (Optional[str]): Optional text to guide the model (context/keywords).

    Returns:
        Dict[str, Any]: Dictionary containing 'text' (full text), 'segments' (list of dicts), and 'language'.
    """
    if use_faster:
        try:
            return _transcribe_faster(audio_path, model_size, language, turbo_mode, initial_prompt)
        except (ImportError, OSError) as e:
            # Handle both import errors and DLL errors (PyTorch issues)
            if "DLL" in str(e) or "torch" in str(e):
                print_warning("PyTorch DLL error detected, falling back to regular Whisper")
            else:
                print_warning("faster-whisper not installed, falling back to regular Whisper")
                print_substep("Install with: pip install faster-whisper")
            return _transcribe_whisper(audio_path, model_size, language, turbo_mode, initial_prompt)
    else:
        return _transcribe_whisper(audio_path, model_size, language, turbo_mode, initial_prompt)


def _transcribe_faster(audio_path, model_size, language, turbo_mode, initial_prompt):
    """Internal implementation using Faster-Whisper"""
    # Lazy imports
    from faster_whisper import WhisperModel
    from tqdm import tqdm
    import subprocess

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    # Check if using distil model
    is_distil = model_size.startswith('distil-')
    actual_model = DISTIL_MAP.get(model_size, model_size)
    display_name = model_size
    
    mode_info = " [TURBO MODE]" if turbo_mode else ""
    print_step(2, 3, f"Loading Faster-Whisper model ({display_name}){mode_info}")
    print_substep("This may take a while on first run (downloading model)...")
    
    if is_distil:
        print_substep("Using Distil-Whisper (6x faster, 50% smaller)")
    else:
        print_substep("Using optimized CTranslate2 backend (4-5x faster)...")
    
    if turbo_mode:
        print_substep("Turbo Mode: Greedy search enabled (3x faster)")
    
    # Load model with CPU or GPU
    force_cpu = os.environ.get('CUDA_VISIBLE_DEVICES') == '-1'
    
    if force_cpu:
        print_substep("Forcing CPU mode (CUDA_VISIBLE_DEVICES=-1)")
        model = WhisperModel(actual_model, device="cpu", compute_type="int8")
    else:
        # Check for GPU/cuDNN
        cudnn_available = False
        try:
            # Check if torch + cuda works (proxy for system capability)
            import torch
            cudnn_available = torch.cuda.is_available()
        except:
            pass
        
        if not cudnn_available:
            print_substep("GPU not available or no cuDNN, using CPU mode")
            model = WhisperModel(actual_model, device="cpu", compute_type="int8")
        else:
            try:
                model = WhisperModel(actual_model, device="cuda", compute_type="float16")
                print_substep("Using GPU acceleration")
            except Exception as e:
                print_substep(f"GPU initialization failed: {str(e)[:50]}...")
                print_substep("Falling back to CPU mode")
                model = WhisperModel(actual_model, device="cpu", compute_type="int8")
    
    print_success("Model loaded successfully")
    print_substep(f"Transcribing audio...")
    print_substep(f"Language: {language if language else 'auto-detect'}")
    if initial_prompt:
        print_substep(f"Deep Hearing: using glossary bias ({len(initial_prompt)} chars)")
    
    # VAD settings
    from dotenv import load_dotenv
    load_dotenv()
    vad_min_silence = int(os.getenv('VAD_MIN_SILENCE_MS', '700'))
    
    # Parameters
    if turbo_mode:
        beam_size = 1
        best_of = 1
        temperature = 0.0
    else:
        beam_size = 5
        best_of = 5
        temperature = 0.0
    
    retry_with_cpu = False
    
    try:
        segments, info = model.transcribe(
            audio_path,
            language=language,
            beam_size=beam_size,
            best_of=best_of,
            temperature=temperature,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=vad_min_silence),
            word_timestamps=True,
            initial_prompt=initial_prompt
        )
        
        result_segments = []
        # Need to iterate generator to trigger processing
        print_substep("Processing segments...")
        for segment in tqdm(segments, desc="      Transcribing", unit="segment", ncols=80):
            result_segments.append({
                'start': segment.start,
                'end': segment.end,
                'text': segment.text.strip()
            })
            
        detected_lang = info.language if hasattr(info, 'language') else 'unknown'
        
    except Exception as e:
        error_msg = str(e).lower()
        if 'cudnn' in error_msg or 'cuda' in error_msg:
            retry_with_cpu = True
        else:
            print_error("Transcription failed!")
            raise e
            
    if retry_with_cpu:
        print_error("GPU/cuDNN error detected! Retrying with CPU mode...")
        model = WhisperModel(actual_model, device="cpu", compute_type="int8")
        
        segments, info = model.transcribe(
            audio_path,
            language=language,
            beam_size=beam_size,
            best_of=best_of,
            temperature=temperature,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=vad_min_silence),
            word_timestamps=True,
            initial_prompt=initial_prompt
        )
        
        result_segments = []
        for segment in tqdm(segments, desc="      Transcribing (Retry)", unit="segment", ncols=80):
            result_segments.append({
                'start': segment.start,
                'end': segment.end,
                'text': segment.text.strip()
            })
        detected_lang = info.language
    
    print_success("Transcription complete!")
    return {
        'language': detected_lang,
        'segments': result_segments
    }


def _transcribe_whisper(audio_path, model_size, language, turbo_mode, initial_prompt):
    """Internal implementation using Regular Whisper"""
    import whisper
    from tqdm import tqdm
    
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    mode_info = " [TURBO MODE]" if turbo_mode else ""
    print_step(2, 3, f"Loading Whisper model ({model_size}){mode_info}")
    
    model = whisper.load_model(model_size)
    print_success("Model loaded successfully")
    
    print_substep(f"Transcribing audio...")
    print_substep(f"Language: {language if language else 'auto-detect'}")
    if initial_prompt:
        print_substep(f"Deep Hearing: using glossary bias")
    
    try:
        # Fake progress bar since regular whisper doesn't expose one easily
        # or we just use it as a spinner context
        with tqdm(total=100, desc="      Transcribing", unit="%", ncols=80) as pbar:
            if turbo_mode:
                result = model.transcribe(
                    audio_path,
                    language=language,
                    verbose=False,
                    fp16=False,
                    beam_size=None,
                    best_of=1,
                    temperature=0.0,
                    initial_prompt=initial_prompt
                )
            else:
                result = model.transcribe(
                    audio_path,
                    language=language,
                    verbose=False,
                    fp16=False,
                    initial_prompt=initial_prompt
                )
            pbar.update(100)
            
    except Exception as e:
        print_error(f"Transcription failed: {e}")
        raise e
    
    print_success("Transcription complete!")
    return result
