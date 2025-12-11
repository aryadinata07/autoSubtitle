"""Subtitle translation utilities - Main interface"""
from .ui import print_step, print_substep, print_success, print_warning
from .translator_google import translate_with_google
from .translator_deepseek import translate_with_deepseek


def translate_subtitles(subs, source_lang, target_lang, use_deepseek=False, deepseek_api_key=None):
    """
    Translate subtitle entries using selected translator
    
    Args:
        subs: Subtitle entries to translate
        source_lang: Source language code (en, id)
        target_lang: Target language code (en, id)
        use_deepseek: Use DeepSeek AI (True) or Google Translate (False)
        deepseek_api_key: DeepSeek API key (required if use_deepseek=True)
    """
    translator_name = "DeepSeek AI" if use_deepseek else "Google Translate"
    print_step(3, 3, f"Translating subtitles ({source_lang.upper()} → {target_lang.upper()})")
    print_substep(f"Using: {translator_name}")
    print_substep("Please wait, this may take a while...")
    
    # Check DeepSeek API key
    if use_deepseek:
        if not deepseek_api_key:
            print_warning("DeepSeek API key not found, falling back to Google Translate")
            use_deepseek = False
    
    # Translate using selected method
    if use_deepseek:
        subs = translate_with_deepseek(subs, source_lang, target_lang, deepseek_api_key)
    else:
        subs = translate_with_google(subs, source_lang, target_lang)
    
    print_success("Translation complete!")
    return subs


def determine_translation_direction(detected_lang):
    """Determine translation direction based on detected language"""
    if detected_lang in ["en", "english"]:
        return "en", "id"
    elif detected_lang in ["id", "indonesian"]:
        return "id", "en"
    else:
        # Default: assume English and translate to Indonesian
        return "en", "id"
