"""Google Translate implementation"""
from deep_translator import GoogleTranslator
from tqdm import tqdm
from .ui import print_warning


def translate_with_google(subs, source_lang, target_lang):
    """
    Translate subtitles using Google Translate
    
    Features:
    - Free, no API key needed
    - Fast and reliable
    - Good for basic translation
    """
    translator = GoogleTranslator(source=source_lang, target=target_lang)
    
    for sub in tqdm(subs, desc="      Translating", unit="subtitle", ncols=80):
        try:
            original_text = sub.text
            translated_text = translator.translate(original_text)
            sub.text = translated_text
        except Exception as e:
            print_warning(f"Failed to translate: {original_text[:50]}...")
            # Keep original text if translation fails
            pass
    
    return subs
