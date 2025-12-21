"""Checkpoint system for progress saving and recovery"""
import json
import os
from pathlib import Path
from datetime import datetime


class CheckpointManager:
    """Manage checkpoints for resume capability"""
    
    def __init__(self, video_path, checkpoint_dir=None):
        """
        Initialize checkpoint manager
        
        Args:
            video_path: Path to video being processed
            checkpoint_dir: Directory to store checkpoints (default: .checkpoints/)
        """
        self.video_path = Path(video_path)
        self.video_name = self.video_path.stem
        
        # Checkpoint directory
        if checkpoint_dir is None:
            # Use script directory for checkpoints
            script_dir = Path(__file__).parent.parent
            checkpoint_dir = script_dir / '.checkpoints'
        
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        
        # Checkpoint file for this video
        self.checkpoint_file = self.checkpoint_dir / f"{self.video_name}.json"
    
    def save(self, step, data):
        """
        Save checkpoint
        
        Args:
            step: Current step name (e.g., 'transcription', 'translation')
            data: Data to save (dict)
        """
        checkpoint = {
            'video_path': str(self.video_path),
            'video_name': self.video_name,
            'step': step,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, indent=2, ensure_ascii=False)
    
    def load(self):
        """
        Load checkpoint if exists
        
        Returns:
            dict: Checkpoint data or None if not exists
        """
        if not self.checkpoint_file.exists():
            return None
        
        try:
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def exists(self):
        """Check if checkpoint exists"""
        return self.checkpoint_file.exists()
    
    def clear(self):
        """Delete checkpoint file"""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
    
    def get_step(self):
        """Get current step from checkpoint"""
        checkpoint = self.load()
        return checkpoint['step'] if checkpoint else None


def cleanup_old_checkpoints(max_age_days=7):
    """
    Clean up old checkpoint files
    
    Args:
        max_age_days: Delete checkpoints older than this many days
    """
    import time
    
    script_dir = Path(__file__).parent.parent
    checkpoint_dir = script_dir / '.checkpoints'
    
    if not checkpoint_dir.exists():
        return
    
    current_time = time.time()
    max_age_seconds = max_age_days * 86400
    
    for checkpoint_file in checkpoint_dir.glob('*.json'):
        file_age = current_time - checkpoint_file.stat().st_mtime
        if file_age > max_age_seconds:
            checkpoint_file.unlink()


def list_checkpoints():
    """
    List all available checkpoints
    
    Returns:
        list: List of checkpoint data dicts, sorted by timestamp (newest first)
    """
    script_dir = Path(__file__).parent.parent
    checkpoint_dir = script_dir / '.checkpoints'
    
    if not checkpoint_dir.exists():
        return []
    
    checkpoints = []
    
    for checkpoint_file in checkpoint_dir.glob('*.json'):
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                checkpoints.append(data)
        except Exception:
            continue
    
    # Sort by timestamp (newest first)
    checkpoints.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return checkpoints
