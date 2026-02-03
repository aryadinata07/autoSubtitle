"""Unit tests for CLI module"""
import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parents[1]))

from core.cli import parse_arguments

class TestCLI(unittest.TestCase):
    
    def test_default_arguments(self):
        """Test parsing default arguments"""
        with patch.object(sys, 'argv', ['prog']):
            args = parse_arguments()
            self.assertEqual(args.model, 'base')
            self.assertIsNone(args.lang)
            self.assertFalse(args.deepseek)
            self.assertFalse(args.turbo)
            
    def test_custom_arguments(self):
        """Test parsing custom arguments"""
        test_args = ['prog', '--model', 'large', '--lang', 'id', '--deepseek', '--turbo']
        with patch.object(sys, 'argv', test_args):
            args = parse_arguments()
            self.assertEqual(args.model, 'large')
            self.assertEqual(args.lang, 'id')
            self.assertTrue(args.deepseek)
            self.assertTrue(args.turbo)
            
    def test_file_inputs(self):
        """Test file input arguments"""
        # Test local file
        with patch.object(sys, 'argv', ['prog', '--file', 'video.mp4']):
            args = parse_arguments()
            self.assertEqual(args.file, 'video.mp4')
            self.assertIsNone(args.youtube)
            
        # Test YouTube URL
        with patch.object(sys, 'argv', ['prog', '--youtube', 'http://youtube.com']):
            args = parse_arguments()
            self.assertEqual(args.youtube, 'http://youtube.com')
            self.assertIsNone(args.file)

if __name__ == '__main__':
    unittest.main()
