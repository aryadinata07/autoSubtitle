"""Subtitle timing adjustment utilities"""
import os
from dotenv import load_dotenv


def adjust_subtitle_timing(segments):
    """
    Smart timing adjustment with collision detection.
    
    Filosofi: Percaya pada akurasi Whisper word_timestamps, 
    tapi pastikan subtitle cukup lama untuk dibaca dan tidak overlap.
    
    Args:
        segments: List of subtitle segments with start, end, text
    
    Returns:
        Adjusted segments
    """
    load_dotenv()
    
    # HAPUS delay statis karena merusak akurasi Whisper
    min_duration = float(os.getenv('SUBTITLE_MIN_DURATION', '1.0'))
    max_duration = float(os.getenv('SUBTITLE_MAX_DURATION', '6.0'))
    
    adjusted_segments = []
    
    for i, segment in enumerate(segments):
        start = segment['start']
        end = segment['end']
        text = segment['text']
        
        # Logic 1: Pastikan durasi minimal (agar mata sempat baca)
        current_duration = end - start
        if current_duration < min_duration:
            potential_end = start + min_duration
        else:
            potential_end = end
        
        # Logic 2: Collision Detection - Cek subtitle berikutnya
        if i < len(segments) - 1:
            next_start = segments[i + 1]['start']
            
            # Jika perpanjangan waktu menabrak subtitle berikutnya
            if potential_end > next_start:
                # Potong tepat sebelum subtitle berikutnya, beri gap kecil
                potential_end = next_start - 0.05
                
                # Safety: jangan sampai waktu jadi mundur
                if potential_end < start:
                    potential_end = start + 0.1
        
        end = potential_end
        
        # Logic 3: Limit max duration (biar gak nggantung kalau hening lama)
        if (end - start) > max_duration:
            end = start + max_duration
        
        adjusted_segments.append({
            'start': round(start, 3),  # Rounding biar file SRT rapi
            'end': round(end, 3),
            'text': text
        })
    
    return adjusted_segments


def optimize_subtitle_gaps(segments, min_gap=0.1):
    """
    Fungsi ini sudah tidak diperlukan karena adjust_subtitle_timing
    sudah handle collision detection. Dibiarkan return segments agar
    tidak error jika dipanggil dari main.py
    """
    return segments
