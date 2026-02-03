"""
Audio Enhancement Utilities
Uses FFmpeg to denoise and normalize audio for better transcription accuracy.
"""
import os
import subprocess
from utils.system.ui import print_step, print_substep, print_success, print_warning

def enhance_audio(input_path: str, output_path: str = None) -> str:
    """
    Enhance audio using FFmpeg filters:
    1. afftdn: FFT-based noise reduction (removes hiss/background noise)
    2. dynaudnorm: Dynamic audio normalization (levels out volume)
    
    Args:
        input_path: Path to input audio file
        output_path: Path to save enhanced audio (default: input_enhanced.wav)
        
    Returns:
        str: Path to enhanced audio file
    """
    if not output_path:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_enhanced{ext}"
        
    print_step(2, 3, "Enhancing Audio Quality")
    print_substep("Applying filters: Denoise (FFT) + Normalization")
    
    # FFmpeg filter chain
    # afftdn=nf=-25: Noise floor at -25dB (removes constant background noise)
    # dynaudnorm: Dynamic normalization (boosts quiet parts, lowers loud parts)
    audio_filter = "afftdn=nf=-25,dynaudnorm=f=150:g=15"
    
    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-af', audio_filter,
        '-c:a', 'pcm_s16le', # Wav format
        '-ar', '16000',      # Whisper expects 16kHz
        output_path
    ]
    
    try:
        # Run conversion
        subprocess.run(
            cmd, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL, 
            check=True
        )
        print_success(f"Audio enhanced: {os.path.basename(output_path)}")
        return output_path
        
    except subprocess.CalledProcessError:
        print_warning("Audio enhancement failed (FFmpeg error). Using original audio.")
        return input_path
    except Exception as e:
        print_warning(f"Audio enhancement error: {e}. Using original audio.")
        return input_path
