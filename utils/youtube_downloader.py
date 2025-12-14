"""YouTube video downloader utilities"""
import os
from yt_dlp import YoutubeDL
from tqdm import tqdm
from .ui import print_step, print_substep, print_success, print_error


class DownloadProgressBar:
    """Progress bar for yt-dlp download"""
    def __init__(self):
        self.pbar = None
    
    def __call__(self, d):
        if d['status'] == 'downloading':
            if self.pbar is None:
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                if total > 0:
                    self.pbar = tqdm(
                        total=total,
                        unit='B',
                        unit_scale=True,
                        unit_divisor=1024,
                        desc='      Downloading',
                        ncols=80
                    )
            
            if self.pbar:
                downloaded = d.get('downloaded_bytes', 0)
                self.pbar.n = downloaded
                self.pbar.refresh()
        
        elif d['status'] == 'finished':
            if self.pbar:
                self.pbar.close()
                self.pbar = None


def download_youtube_video(url, output_path="downloads"):
    """
    Download YouTube video in best quality
    
    Args:
        url: YouTube video URL
        output_path: Output directory for downloaded video
    
    Returns:
        Tuple of (downloaded_file_path, video_title)
    """
    print_step(1, 4, "Downloading YouTube video")
    print_substep(f"URL: {url}")
    
    # Create output directory if not exists
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    # Progress bar instance
    progress_bar = DownloadProgressBar()
    
    # yt-dlp options
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'quiet': True,  # Suppress yt-dlp output
        'no_warnings': True,  # Suppress warnings
        'progress_hooks': [progress_bar],
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            print_substep("Fetching video info...")
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'video')
            duration = info.get('duration', 0)
            
            print_substep(f"Title: {video_title}")
            print_substep(f"Duration: {duration // 60}:{duration % 60:02d}")
            
            # Download video
            ydl.download([url])
            
            # Get downloaded file path
            downloaded_file = ydl.prepare_filename(info)
            
            print_success(f"Video downloaded: {downloaded_file}")
            return downloaded_file, video_title
            
    except Exception as e:
        print_error(f"Failed to download video: {str(e)}")
        print_substep("\n[SOLUTION] YouTube download failed. Please:")
        print_substep("1. Download video manually from:")
        print_substep("   - y2mate.com (recommended)")
        print_substep("   - savefrom.net")
        print_substep("   - ssyoutube.com (add 'ss' before youtube.com)")
        print_substep("2. Then process with: autosub -l 'video.mp4' -default")
        raise


def is_youtube_url(url):
    """Check if URL is a YouTube URL"""
    youtube_domains = ['youtube.com', 'youtu.be', 'www.youtube.com', 'm.youtube.com']
    return any(domain in url.lower() for domain in youtube_domains)
