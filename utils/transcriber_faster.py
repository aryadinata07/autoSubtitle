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
        # Check if cuDNN is available before trying GPU
        import subprocess
        cudnn_available = False
        try:
            # Quick test to see if CUDA/cuDNN works
            result = subprocess.run(
                ['nvidia-smi'],
                capture_output=True,
                text=True,
                timeout=3
            )
            if result.returncode == 0:
                # NVIDIA GPU detected, but need to check cuDNN
                # Try to import torch to test CUDA availability
                try:
                    import torch
                    cudnn_available = torch.cuda.is_available()
                except:
                    cudnn_available = False
        except:
            pass
        
        if not cudnn_available:
            # No cuDNN, use CPU directly
            print_substep("GPU detected but cuDNN not available, using CPU mode")
            model = WhisperModel(model_size, device="cpu", compute_type="int8")
        else:
            try:
                # Try GPU with cuDNN
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
    
    # Transcribe with auto-retry on cuDNN errors
    result_segments = []
    detected_lang = 'unknown'
    retry_with_cpu = False
    
    try:
        segments, info = model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True,  # Voice activity detection
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        # Convert segments to list (error might happen here during iteration)
        try:
            for segment in segments:
                result_segments.append({
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text
                })
        except Exception as seg_error:
            # Check if it's a cuDNN error during segment iteration
            if 'cudnn' in str(seg_error).lower() or 'cuda' in str(seg_error).lower():
                retry_with_cpu = True
            else:
                raise
        
        detected_lang = info.language if hasattr(info, 'language') else 'unknown'
        
    except Exception as e:
        error_msg = str(e).lower()
        # Check if it's a cuDNN error
        if 'cudnn' in error_msg or 'cuda' in error_msg:
            retry_with_cpu = True
        else:
            # Other errors
            print_error("Transcription failed!")
            print_substep(f"Error: {str(e)}")
            print_substep("\nPossible solutions:")
            print_substep("1. Make sure ffmpeg is installed and in PATH")
            print_substep("2. Restart your terminal/PowerShell")
            print_substep("3. Try: refreshenv (if using Chocolatey)")
            raise
    
    # Retry with CPU if cuDNN error detected
    if retry_with_cpu:
        print_error("GPU/cuDNN error detected!")
        print_substep("Retrying with CPU mode...")
        
        # Reload model with CPU
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        print_substep("Model reloaded in CPU mode")
        
        # Retry transcription with CPU
        segments, info = model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True,
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
    
    print_success("Transcription complete!")
    print_substep(f"Detected language: {detected_lang}")
    print_substep(f"Total segments: {len(result_segments)}")
    
    return {
        'language': detected_lang,
        'segments': result_segments
    }
