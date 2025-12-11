"""DeepSeek AI translation implementation"""
from openai import OpenAI
from tqdm import tqdm
from .ui import print_substep, print_warning


def get_video_context(subs, sample_size=5):
    """Get video context from first few subtitles to understand the topic"""
    sample_texts = []
    for i, sub in enumerate(subs[:sample_size]):
        sample_texts.append(sub.text)
    return " ".join(sample_texts)


def translate_batch_with_deepseek(texts, source_lang, target_lang, api_key, context=""):
    """
    Translate multiple texts in one request using DeepSeek API
    
    Features:
    - Batch processing (10 subtitles per request)
    - Context-aware translation
    - Natural and conversational output
    """
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
            timeout=60.0  # Add timeout to prevent hanging
        )
        
        lang_map = {
            'en': 'English',
            'id': 'Indonesian'
        }
        
        source_name = lang_map.get(source_lang, source_lang)
        target_name = lang_map.get(target_lang, target_lang)
        
        # Create numbered list for batch translation
        numbered_texts = "\n".join([f"{i+1}. {text}" for i, text in enumerate(texts)])
        
        context_info = f"\n\nVideo context: {context}" if context else ""
        
        prompt = f"""Translate the following subtitle texts from {source_name} to {target_name}.
These are video subtitles, so translate naturally and conversationally (not too formal or stiff).
Keep the same numbering format in your response.{context_info}

{numbered_texts}

Return only the numbered translations, nothing else."""
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a professional subtitle translator. Translate naturally and conversationally, maintaining the casual tone of spoken language. Avoid overly formal or stiff translations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,  # Slightly higher for more natural language
            max_tokens=2000
        )
        
        # Parse response to extract translations
        response_text = response.choices[0].message.content.strip()
        translations = []
        
        for line in response_text.split('\n'):
            line = line.strip()
            if line and len(line) > 0 and line[0].isdigit():
                # Remove number prefix (e.g., "1. " or "1) ")
                parts = line.split('.', 1)
                if len(parts) > 1:
                    translations.append(parts[1].strip())
                else:
                    parts = line.split(')', 1)
                    if len(parts) > 1:
                        translations.append(parts[1].strip())
        
        # If parsing failed, return original texts
        if len(translations) != len(texts):
            return texts
        
        return translations
    except Exception as e:
        # Return original texts if API call fails
        print(f"DeepSeek API error: {str(e)}")
        return texts


def translate_with_deepseek(subs, source_lang, target_lang, api_key):
    """
    Translate subtitles using DeepSeek AI
    
    Features:
    - More natural and conversational
    - Context-aware translation
    - Batch processing (10x faster)
    - Understands video topic
    """
    # Get video context from first few subtitles
    print_substep("Analyzing video context...")
    context = get_video_context(subs, sample_size=5)
    
    # Batch processing for DeepSeek
    batch_size = 10
    total_batches = (len(subs) + batch_size - 1) // batch_size
    
    print_substep(f"Processing {len(subs)} subtitles in {total_batches} batches...")
    
    from tqdm import tqdm
    import time
    
    with tqdm(total=len(subs), desc="      Translating", unit="subtitle", ncols=80) as pbar:
        for i in range(0, len(subs), batch_size):
            batch = subs[i:i + batch_size]
            texts = [sub.text for sub in batch]
            batch_num = i // batch_size + 1
            
            try:
                # Add small delay to avoid rate limiting
                if i > 0:
                    time.sleep(0.5)
                
                translations = translate_batch_with_deepseek(
                    texts,
                    source_lang,
                    target_lang,
                    api_key,
                    context=context if i == 0 else ""  # Only send context on first batch
                )
                
                # Apply translations
                for j, sub in enumerate(batch):
                    if j < len(translations):
                        sub.text = translations[j]
                    pbar.update(1)
                    
            except Exception as e:
                print_warning(f"Failed to translate batch {batch_num}: {str(e)}")
                # Keep original text if translation fails
                pbar.update(len(batch))
    
    return subs
