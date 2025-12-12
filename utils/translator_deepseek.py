"""DeepSeek AI translation implementation - Optimized Version"""
from openai import OpenAI
from tqdm import tqdm
import time
from .ui import print_substep, print_warning, print_step


def get_video_context(subs, sample_size=5):
    """Get video context from first few subtitles to understand the topic"""
    sample_texts = []
    total = len(subs)
    
    # Sample dari awal
    indices = [i for i in range(min(sample_size, total))]
    
    # Tambah sample dari tengah untuk gambaran lebih lengkap
    if total > 20:
        indices.extend([total // 2, (total // 2) + 1])
    
    for i in indices:
        if i < total:
            sample_texts.append(subs[i].text)
    
    return " ".join(sample_texts)


def translate_batch_with_deepseek(texts, source_lang, target_lang, api_key, global_context="", prev_context=""):
    """
    Translate multiple texts with persistent context + sliding window
    
    Features:
    - Global context di setiap batch (no amnesia!)
    - Sliding window: kirim 1 kalimat terakhir batch sebelumnya
    - Natural Indonesian slang mode
    """
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
            timeout=90.0
        )
        
        lang_map = {
            'en': 'English',
            'id': 'Indonesian (Bahasa Gaul/Santai)',
            'ja': 'Japanese',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'zh': 'Chinese'
        }
        
        source_name = lang_map.get(source_lang, source_lang)
        target_name = lang_map.get(target_lang, target_lang)
        
        # Create numbered list
        numbered_texts = "\n".join([f"{i+1}. {text}" for i, text in enumerate(texts)])
        
        # Build context instruction
        context_instruction = ""
        if global_context:
            context_instruction += f"\n[Global Video Context]: {global_context}"
        if prev_context:
            context_instruction += f"\n[Previous Sentence]: ...{prev_context}"
        
        # System prompt: Strict line-by-line + Punctuation awareness
        system_prompt = f"""You are a professional subtitle translator.
Target: {target_name}.
Style: Natural, conversational, slang allowed.

CRITICAL RULES:
1. Translate LINE-BY-LINE. DO NOT MERGE LINES.
2. Even if a sentence is split across lines, keep it split.
3. OUTPUT MUST HAVE EXACTLY {len(texts)} LINES.
4. Return ONLY the numbered list (e.g. "1. translation").
5. PUNCTUATION MATTERS: If the input sentence is incomplete/continues to next line, DO NOT put a period (.) at the end. Only use periods/question marks/exclamation marks if the thought is completely finished.
6. No explanations, no extra text."""
        
        user_prompt = f"""Translate these {len(texts)} lines from {source_name} to {target_name}.
Keep the exact same number of lines. Do not merge text.
{context_instruction}

Input:
{numbered_texts}

Output ({len(texts)} lines):"""
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Lower untuk strict compliance
            max_tokens=4000
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # ROBUST PARSING: Regex-based line-by-line extraction
        translations = []
        import re
        
        for line in response_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Regex: Match "1. Text" or "1) Text" or "1 Text"
            match = re.match(r'^\d+[\.\)\s]+(.*)', line)
            if match:
                translation = match.group(1).strip()
                if translation:  # Only add non-empty translations
                    translations.append(translation)
        
        # RELAXED VALIDATION: Allow slight mismatch (DeepSeek might merge short subtitles)
        if len(translations) == 0:
            return texts
        
        # If count doesn't match, try to handle it gracefully
        if len(translations) != len(texts):
            # If we got fewer translations, pad with originals
            if len(translations) < len(texts):
                while len(translations) < len(texts):
                    translations.append(texts[len(translations)])
            # If we got more, truncate
            elif len(translations) > len(texts):
                translations = translations[:len(texts)]
        
        return translations
    
    except Exception as e:
        print(f"DeepSeek API error: {str(e)}")
        return texts


def translate_with_deepseek(subs, source_lang, target_lang, api_key, video_title=None):
    """
    Translate subtitles using DeepSeek AI with persistent context
    
    Features:
    - NO AMNESIA: Global context di setiap batch
    - Sliding window: Flow mulus antar batch
    - Natural Indonesian slang mode
    - Batch processing (10x faster)
    
    Args:
        subs: Subtitle entries
        source_lang: Source language code
        target_lang: Target language code
        api_key: DeepSeek API key
        video_title: Video title (optional, used as additional context)
    """
    print_step(3, 4, "Translating with DeepSeek AI...")
    
    # Get global video context
    context = get_video_context(subs)
    if video_title:
        context = f"Title: {video_title}. Content Summary: {context}"
    
    print_substep(f"Context loaded: {len(context)} chars")
    
    # Batch processing - Balanced size (not too big, not too small)
    batch_size = 8  # Sweet spot: fast enough, accurate enough
    total_batches = (len(subs) + batch_size - 1) // batch_size
    
    # Sliding window: simpan kalimat terakhir batch sebelumnya
    last_sentence_context = ""
    
    with tqdm(total=len(subs), desc="Translating", unit="sub", ncols=80) as pbar:
        for i in range(0, len(subs), batch_size):
            batch = subs[i:i + batch_size]
            texts = [sub.text for sub in batch]
            
            try:
                # Rate limiting
                if i > 0:
                    time.sleep(0.2)
                
                # PERBAIKAN FATAL: Kirim global_context di SETIAP batch
                translations = translate_batch_with_deepseek(
                    texts,
                    source_lang,
                    target_lang,
                    api_key,
                    global_context=context,  # Selalu kirim!
                    prev_context=last_sentence_context  # Sliding window
                )
                
                # Apply translations
                for j, sub in enumerate(batch):
                    if j < len(translations):
                        sub.text = translations[j]
                    pbar.update(1)
                
                # Update sliding window dengan kalimat terakhir batch ini
                if translations:
                    last_sentence_context = translations[-1]
            
            except Exception as e:
                print_warning(f"Batch failed: {str(e)}")
                pbar.update(len(batch))
    
    return subs
