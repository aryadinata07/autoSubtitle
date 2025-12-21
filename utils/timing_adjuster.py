"""Subtitle timing adjustment utilities - Semantic Bridge Version"""
import os
from dotenv import load_dotenv


def is_sentence_ending(text):
    """
    Cek apakah teks diakhiri tanda baca penutup kalimat.
    DeepSeek biasanya sangat rapi memberi tanda baca.
    
    Returns:
        True jika kalimat sudah selesai (ada titik/tanda tanya/seru)
        False jika kalimat masih gantung (belum selesai)
    """
    text = text.strip()
    if not text:
        return True
    
    # Cek karakter terakhir: Titik, Tanya, Seru, Kutip tutup, atau kurung tutup
    return text[-1] in ['.', '?', '!', '"', '"', ')', ']', '…']


def adjust_subtitle_timing(segments, structure_analysis=None):
    """
    Smart timing adjustment dengan Linguistic Bridging.
    
    Filosofi:
    - Gunakan kecerdasan DeepSeek untuk deteksi kalimat gantung (structure_analysis)
    - Jika kalimat belum selesai (CONTINUES), TAHAN subtitle
    
    Args:
        segments: List of subtitle segments with start, end, text
        structure_analysis: Optional list of 'COMPLETE'/'CONTINUES' statuses
    
    Returns:
        Adjusted segments
    """
    load_dotenv()
    
    min_duration = float(os.getenv('SUBTITLE_MIN_DURATION', '1.5'))
    max_duration = float(os.getenv('SUBTITLE_MAX_DURATION', '8.0'))
    gap_settings = float(os.getenv('SUBTITLE_GAP', '0.1'))
    
    # NEW: Minimum reading time based on text length (characters per second)
    min_reading_speed = 15
    
    adjusted_segments = []
    
    for i, segment in enumerate(segments):
        start = segment['start']
        end = segment['end']
        text = segment['text']
        
        # Calculate minimum duration
        text_length = len(text)
        min_reading_duration = text_length / min_reading_speed
        effective_min_duration = max(min_duration, min_reading_duration)
        
        # LOGIC: Cek subtitle berikutnya
        if i < len(segments) - 1:
            next_start = segments[i + 1]['start']
            silence_gap = next_start - end
            
            # CEK KONDISI GANTUNG (LINGUISTIC BRIDGE)
            sentence_incomplete = False
            
            # Prioritas 1: AI Analysis (DeepSeek)
            if structure_analysis and i < len(structure_analysis):
                status = structure_analysis[i]
                if status == 'CONTINUES':
                    sentence_incomplete = True
            
            # Prioritas 2: Heuristic Fallback (jika AI tidak ada)
            else:
                sentence_incomplete = not is_sentence_ending(text)
            
            # KONDISI 1: Kalimat Gantung
            # Jika AI bilang 'CONTINUES', kita bridge gap-nya walaupun agak jauh (max 4 detik)
            if sentence_incomplete and silence_gap < 4.0:
                potential_end = next_start - gap_settings
                if (potential_end - start) <= max_duration:
                    end = potential_end
                else:
                    end = start + max_duration
            
            # KONDISI 2: Jeda Pendek Biasa (Napas)
            elif silence_gap < 1.5:
                potential_end = next_start - gap_settings
                if (potential_end - start) <= max_duration:
                    end = potential_end
            
            # KONDISI 3: Overlap
            elif silence_gap <= 0:
                end = next_start - gap_settings
            
            # KONDISI 4: Ensure minimum reading time
            if (end - start) < effective_min_duration:
                potential_end = start + effective_min_duration
                if potential_end < next_start - gap_settings:
                    end = potential_end
                else:
                    end = next_start - gap_settings
        
        else:
            # Subtitle Terakhir
            if (end - start) < effective_min_duration:
                end = start + effective_min_duration
        
        # Final Safety Check
        if end <= start:
            end = start + effective_min_duration
        
        adjusted_segments.append({
            'start': round(start, 3),
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
