"""Utilities for subtitle generation"""
from .audio_extractor import extract_audio
from .transcriber import transcribe_audio
from .subtitle_creator import create_srt
from .translator import translate_subtitles, determine_translation_direction
from .translator_google import translate_with_google
from .translator_deepseek import translate_with_deepseek
from .video_embedder import embed_subtitle_to_video
from .youtube_downloader import download_youtube_video, is_youtube_url
from .timing_adjuster import adjust_subtitle_timing, optimize_subtitle_gaps
from .checkpoint import CheckpointManager, cleanup_old_checkpoints
from .error_handler import (
    SubtitleError,
    TranscriptionError,
    TranslationError,
    VideoProcessingError,
    DownloadError,
    handle_transcription_error,
    handle_translation_error,
    handle_video_error,
)

__all__ = [
    "extract_audio",
    "transcribe_audio",
    "create_srt",
    "translate_subtitles",
    "determine_translation_direction",
    "translate_with_google",
    "translate_with_deepseek",
    "embed_subtitle_to_video",
    "download_youtube_video",
    "is_youtube_url",
    "adjust_subtitle_timing",
    "optimize_subtitle_gaps",
    "CheckpointManager",
    "cleanup_old_checkpoints",
    "SubtitleError",
    "TranscriptionError",
    "TranslationError",
    "VideoProcessingError",
    "DownloadError",
    "handle_transcription_error",
    "handle_translation_error",
    "handle_video_error",
]
