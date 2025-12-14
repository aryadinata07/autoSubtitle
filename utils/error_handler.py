"""Enhanced error handling with helpful messages"""
from .ui import print_error, print_substep, print_warning


class SubtitleError(Exception):
    """Base exception for subtitle generation errors"""
    
    def __init__(self, message, solution=None, help_url=None):
        self.message = message
        self.solution = solution
        self.help_url = help_url
        super().__init__(self.message)
    
    def display(self):
        """Display error with helpful information"""
        print_error(self.message)
        
        if self.solution:
            print_substep("\n[SOLUTION]")
            if isinstance(self.solution, list):
                for i, sol in enumerate(self.solution, 1):
                    print_substep(f"{i}. {sol}")
            else:
                print_substep(self.solution)
        
        if self.help_url:
            print_substep(f"\n[MORE INFO] {self.help_url}")


class TranscriptionError(SubtitleError):
    """Error during transcription"""
    pass


class TranslationError(SubtitleError):
    """Error during translation"""
    pass


class VideoProcessingError(SubtitleError):
    """Error during video processing"""
    pass


class DownloadError(SubtitleError):
    """Error during video download"""
    pass


def handle_transcription_error(error):
    """Handle transcription errors with helpful messages"""
    error_msg = str(error).lower()
    
    if 'cuda' in error_msg or 'gpu' in error_msg:
        raise TranscriptionError(
            "GPU/CUDA error detected",
            solution=[
                "Script will automatically retry with CPU mode",
                "Or set CUDA_VISIBLE_DEVICES=-1 to force CPU mode",
                "Check if NVIDIA drivers are up to date"
            ]
        )
    
    elif 'memory' in error_msg or 'out of memory' in error_msg:
        raise TranscriptionError(
            "Out of memory error",
            solution=[
                "Try smaller model: --model tiny or --model base",
                "Close other applications to free up RAM",
                "For long videos, consider splitting into parts"
            ]
        )
    
    elif 'audio' in error_msg or 'ffmpeg' in error_msg:
        raise TranscriptionError(
            "Audio extraction failed",
            solution=[
                "Check if FFmpeg is installed: ffmpeg -version",
                "Make sure video file is not corrupted",
                "Try re-downloading the video"
            ]
        )
    
    else:
        raise TranscriptionError(
            f"Transcription failed: {error}",
            solution=[
                "Try different model size: --model base",
                "Check if audio is clear and not corrupted",
                "Try with --turbo flag for faster processing"
            ]
        )


def handle_translation_error(error):
    """Handle translation errors with helpful messages"""
    error_msg = str(error).lower()
    
    if 'api' in error_msg or 'key' in error_msg:
        raise TranslationError(
            "API key error",
            solution=[
                "Check DEEPSEEK_API_KEY in .env file",
                "Get API key from: https://platform.deepseek.com/",
                "Or use Google Translate (free, no API key needed)"
            ]
        )
    
    elif 'rate limit' in error_msg or 'quota' in error_msg:
        raise TranslationError(
            "API rate limit exceeded",
            solution=[
                "Wait a few minutes and try again",
                "Or use Google Translate as fallback",
                "Check your API quota at DeepSeek dashboard"
            ]
        )
    
    elif 'network' in error_msg or 'connection' in error_msg:
        raise TranslationError(
            "Network connection error",
            solution=[
                "Check your internet connection",
                "Try again in a few moments",
                "Or use Google Translate (works offline-ish)"
            ]
        )
    
    else:
        raise TranslationError(
            f"Translation failed: {error}",
            solution=[
                "Try Google Translate instead of DeepSeek",
                "Check your internet connection",
                "Verify API key is correct"
            ]
        )


def handle_video_error(error):
    """Handle video processing errors with helpful messages"""
    error_msg = str(error).lower()
    
    if 'ffmpeg' in error_msg:
        raise VideoProcessingError(
            "FFmpeg error",
            solution=[
                "Check if FFmpeg is installed: ffmpeg -version",
                "Make sure FFmpeg is in PATH",
                "Try reinstalling FFmpeg"
            ]
        )
    
    elif 'codec' in error_msg or 'format' in error_msg:
        raise VideoProcessingError(
            "Video format/codec error",
            solution=[
                "Try converting video to MP4 first",
                "Use different encoding method: --fast or --standard",
                "Check if video file is corrupted"
            ]
        )
    
    elif 'permission' in error_msg or 'access' in error_msg:
        raise VideoProcessingError(
            "File permission error",
            solution=[
                "Check if output directory is writable",
                "Close video file if it's open in another program",
                "Run with administrator privileges if needed"
            ]
        )
    
    else:
        raise VideoProcessingError(
            f"Video processing failed: {error}",
            solution=[
                "Check if video file is valid and not corrupted",
                "Try different encoding method",
                "Make sure enough disk space available"
            ]
        )
