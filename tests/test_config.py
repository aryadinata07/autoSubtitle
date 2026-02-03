"""Unit tests for configuration module (using unittest)"""
import os
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parents[1]))

from core.config import load_config, save_config, ENV_PATH

class TestConfig(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.TemporaryDirectory()
        self.env_path = Path(self.test_dir.name) / ".env"
        
        # Patch ENV_PATH
        self.patcher = patch('core.config.ENV_PATH', self.env_path)
        self.mock_env_path = self.patcher.start()
        
    def tearDown(self):
        """Clean up"""
        self.patcher.stop()
        self.test_dir.cleanup()

    def test_load_config_defaults(self):
        """Test loading config with defaults when env is missing"""
        # Ensure no env vars interfere
        with patch.dict(os.environ, {}, clear=True):
            config = load_config()
            self.assertEqual(config['WHISPER_MODE'], 'base')
            self.assertEqual(config['TURBO_MODE'], 'ask')
            self.assertEqual(config['SUBTITLE_GAP'], 0.1)

    def test_load_config_from_env(self):
        """Test loading config from environment variables"""
        # Create dummy .env content
        with open(self.env_path, 'w') as f:
            f.write("DEEPSEEK_API_KEY=test_key\n")
            f.write("TURBO_MODE=true\n")
            
        # Mock load_dotenv to actually load from our temp file setup
        # But core.config uses load_dotenv internally. 
        # Simpler: just mock os.environ directly as if dotenv loaded it.
        with patch.dict(os.environ, {
            'DEEPSEEK_API_KEY': 'test_key',
            'TURBO_MODE': 'true'
        }, clear=True):
            config = load_config()
            self.assertEqual(config['DEEPSEEK_API_KEY'], 'test_key')
            self.assertEqual(config['TURBO_MODE'], 'true')

    @patch('core.config.set_key')
    def test_save_config(self, mock_set_key):
        """Test saving configuration"""
        save_config('NEW_SETTING', 'value')
        
        mock_set_key.assert_called_once()
        args = mock_set_key.call_args
        self.assertEqual(args[0][1], 'NEW_SETTING')
        self.assertEqual(args[0][2], 'value')

if __name__ == '__main__':
    unittest.main()
