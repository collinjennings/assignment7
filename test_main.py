import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import logging

# Import functions from main.py
from main import (
    setup_logging,
    create_directory,
    is_valid_url,
    generate_qr_code,
    main
)


class TestSetupLogging:
    """Test cases for setup_logging function"""
    
    def test_setup_logging_configures_basic_config(self):
        """Test that logging is configured with correct settings"""
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging()
            mock_basic_config.assert_called_once()
            call_kwargs = mock_basic_config.call_args[1]
            assert call_kwargs['level'] == logging.INFO
            assert '%(asctime)s - %(levelname)s - %(message)s' in call_kwargs['format']


class TestCreateDirectory:
    """Test cases for create_directory function"""
    
    def test_create_directory_success(self, tmp_path):
        """Test successful directory creation"""
        test_dir = tmp_path / "test_qr_codes"
        create_directory(test_dir)
        assert test_dir.exists()
        assert test_dir.is_dir()
    
    def test_create_directory_nested_paths(self, tmp_path):
        """Test creating nested directory structure"""
        test_dir = tmp_path / "level1" / "level2" / "level3"
        create_directory(test_dir)
        assert test_dir.exists()
    
    def test_create_directory_already_exists(self, tmp_path):
        """Test that existing directory doesn't raise error"""
        test_dir = tmp_path / "existing_dir"
        test_dir.mkdir()
        create_directory(test_dir)  # Should not raise exception
        assert test_dir.exists()
    
    def test_create_directory_failure(self):
        """Test handling of directory creation failure"""
        with patch.object(Path, 'mkdir', side_effect=PermissionError("Permission denied")):
            with pytest.raises(SystemExit) as exc_info:
                create_directory(Path("/invalid/path"))
            assert exc_info.value.code == 1


class TestIsValidUrl:
    """Test cases for is_valid_url function"""
    
    def test_valid_http_url(self):
        """Test validation of valid HTTP URL"""
        assert is_valid_url("http://example.com") is True
    
    def test_valid_https_url(self):
        """Test validation of valid HTTPS URL"""
        assert is_valid_url("https://github.com/user") is True
    
    def test_valid_url_with_path(self):
        """Test validation of URL with path"""
        assert is_valid_url("https://example.com/path/to/page") is True
    
    def test_valid_url_with_query_params(self):
        """Test validation of URL with query parameters"""
        assert is_valid_url("https://example.com?param=value&other=123") is True
    
    def test_invalid_url_no_protocol(self):
        """Test that URL without protocol is invalid"""
        assert is_valid_url("example.com") is False
    
    def test_invalid_url_empty_string(self):
        """Test that empty string is invalid"""
        assert is_valid_url("") is False
    
    def test_invalid_url_malformed(self):
        """Test that malformed URL is invalid"""
        assert is_valid_url("not a url at all") is False
    
    def test_invalid_url_logs_error(self, caplog):
        """Test that invalid URL logs an error message"""
        with caplog.at_level(logging.ERROR):
            is_valid_url("invalid_url")
            assert "Invalid URL provided" in caplog.text


class TestGenerateQrCode:
    """Test cases for generate_qr_code function"""
    
    def test_generate_qr_code_success(self, tmp_path):
        """Test successful QR code generation"""
        test_url = "https://github.com/test"
        test_path = tmp_path / "test_qr.png"
        
        generate_qr_code(test_url, test_path)
        
        assert test_path.exists()
        # Verify it's a file with content
        assert test_path.stat().st_size > 0
    
    def test_generate_qr_code_with_custom_colors(self, tmp_path):
        """Test QR code generation with custom colors"""
        test_url = "https://example.com"
        test_path = tmp_path / "colored_qr.png"
        
        generate_qr_code(test_url, test_path, fill_color='blue', back_color='yellow')
        
        assert test_path.exists()
    
    def test_generate_qr_code_invalid_url(self, tmp_path):
        """Test that invalid URL doesn't create QR code"""
        test_url = "not_a_valid_url"
        test_path = tmp_path / "should_not_exist.png"
        
        generate_qr_code(test_url, test_path)
        
        assert not test_path.exists()
    
    def test_generate_qr_code_logs_success(self, tmp_path, caplog):
        """Test that successful generation logs info message"""
        test_url = "https://github.com/test"
        test_path = tmp_path / "test_qr.png"
        
        with caplog.at_level(logging.INFO):
            generate_qr_code(test_url, test_path)
            assert "QR code successfully saved" in caplog.text
    
    def test_generate_qr_code_handles_save_error(self, tmp_path, caplog):
        """Test error handling when saving QR code fails"""
        test_url = "https://github.com/test"
        test_path = tmp_path / "test_qr.png"
        
        with patch('qrcode.QRCode.make_image', side_effect=Exception("Save error")):
            with caplog.at_level(logging.ERROR):
                generate_qr_code(test_url, test_path)
                assert "An error occurred" in caplog.text


class TestMain:
    """Test cases for main function"""
    
    @patch('main.generate_qr_code')
    @patch('main.create_directory')
    @patch('main.setup_logging')
    def test_main_default_url(self, mock_logging, mock_create_dir, mock_generate):
        """Test main function with default URL"""
        with patch('sys.argv', ['main.py']):
            main()
            
            mock_logging.assert_called_once()
            mock_create_dir.assert_called_once()
            mock_generate.assert_called_once()
            
            # Check that generate_qr_code was called with default URL
            call_args = mock_generate.call_args[0]
            assert call_args[0] == 'https://github.com/kaw393939'
    
    @patch('main.generate_qr_code')
    @patch('main.create_directory')
    @patch('main.setup_logging')
    def test_main_custom_url(self, mock_logging, mock_create_dir, mock_generate):
        """Test main function with custom URL argument"""
        test_url = "https://example.com/custom"
        with patch('sys.argv', ['main.py', '--url', test_url]):
            main()
            
            # Check that generate_qr_code was called with custom URL
            call_args = mock_generate.call_args[0]
            assert call_args[0] == test_url
    
    @patch('main.generate_qr_code')
    @patch('main.create_directory')
    @patch('main.setup_logging')
    @patch('main.datetime')
    def test_main_creates_timestamped_filename(self, mock_datetime, mock_logging, 
                                               mock_create_dir, mock_generate):
        """Test that main creates QR code with timestamped filename"""
        mock_now = MagicMock()
        mock_now.strftime.return_value = '20231225120000'
        mock_datetime.now.return_value = mock_now
        
        with patch('sys.argv', ['main.py']):
            main()
            
            # Check the path passed to generate_qr_code
            call_args = mock_generate.call_args[0]
            qr_path = call_args[1]
            assert 'QRCode_20231225120000.png' in str(qr_path)