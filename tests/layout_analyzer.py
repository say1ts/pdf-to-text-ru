import json
import pytest
from unittest.mock import patch, MagicMock
from src.recognizers.layout_analyzer import analyze_pdf, FileNotFoundError, InvalidJsonError
from src.settings import settings

@pytest.fixture
def mock_requests_post():
    return patch("src.recognizers.layout_analyzer.requests.post")

def test_analyze_pdf_success(mock_requests_post):
    file_path = "test.pdf"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "left": 10.0,
            "top": 20.0,
            "width": 100.0,
            "height": 50.0,
            "page_number": 1,
            "page_width": 595,
            "page_height": 842,
            "type": "text",
            "text": "Sample text"
        }
    ]
    mock_requests_post.return_value = mock_response
    
    result = analyze_pdf(file_path)
    
    assert len(result) == 1
    assert result[0]["type"] == "text"
    mock_requests_post.assert_called_once_with(
        settings.LAYOUT_ANALYZER_URL,
        files={'file': mock_response},
        timeout=settings.LAYOUT_ANALYZER_TIMEOUT
    )

def test_analyze_pdf_file_not_found(mock_requests_post):
    file_path = "nonexistent.pdf"
    mock_requests_post.side_effect = FileNotFoundError
    
    with pytest.raises(FileNotFoundError):
        analyze_pdf(file_path)

def test_analyze_pdf_invalid_json(mock_requests_post):
    file_path = "test.pdf"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
    mock_requests_post.return_value = mock_response
    
    with pytest.raises(InvalidJsonError):
        analyze_pdf(file_path)
        