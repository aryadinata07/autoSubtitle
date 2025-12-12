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


def adjust_subtitle_timing(segments):
    """
    Smart timing adjustment dengan Linguistic Bridging.
    
    Filosofi:
    - Gunakan kecerdasan DeepSeek untuk deteksi kalimat gantung
    - Jika kalimat belum selesai (tidak ada titik), TAHAN subtitle
    - Ini mengatasi "dramatic pause" yang tidak bisa diselesaikan timing saja
    
    Args:
        segments: List of subtitle segments with start, end, text
    
    Returns:
        Adjusted segments
    """
    load_dotenv()
    
    min_duration = float(os.getenv('SUBTITLE_MIN_DURATION', '1.0'))
    max_duration = float(os.getenv('SUBTITLE_MAX_DURATION', '7.0'))
    gap_settings = float(os.getenv('SUBTITLE_GAP', '0.05'))
    
    adjusted_segments = []
    
    for i, segment in enumerate(segments):
        start = segment['start']
        end = segment['end']
        text = segment['text']
        
        # LOGIC: Cek subtitle berikutnya
        if i < len(segments) - 1:
            next_start = segments[i + 1]['start']
            silence_gap = next_start - end
            
            # Cek apakah kalimat ini 'Gantung' (Belum ada titik/tanda baca akhir)
            # Ini kekuatan DeepSeek: Dia tau struktur kalimat
            sentence_incomplete = not is_sentence_ending(text)
            
            # KONDISI 1: Kalimat Gantung (Linguistic Bridge)
            # Walaupun orangnya diam 3 detik, kalau kalimat belum titik, TAHAN text-nya
            if sentence_incomplete and silence_gap < 3.0:
                # Extend sampai subtitle berikutnya mulai
                potential_end = next_start - gap_settings
                
                # Batasi dengan max duration biar gak aneh kalau heningnya kelamaan
                if (potential_end - start) <= max_duration:
                    end = potential_end
                else:
                    end = start + max_duration
            
            # KONDISI 2: Jeda Pendek Biasa (Napas)
            # Kalimat mungkin udah selesai, tapi jedanya pendek banget (< 1 detik)
            # Sambung aja biar mata gak capek kedip
            elif silence_gap < 1.0:
                potential_end = next_start - gap_settings
                if (potential_end - start) <= max_duration:
                    end = potential_end
            
            # KONDISI 3: Overlap
            elif silence_gap <= 0:
                end = next_start - gap_settings
        
        else:
            # Subtitle Terakhir
            if (end - start) < min_duration:
                end = start + min_duration
        
        # Final Safety Check
        if end <= start:
            end = start + min_duration
        
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
