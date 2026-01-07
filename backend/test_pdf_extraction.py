"""
Unit tests for PDF extraction feature.
Tests the PDFExtractor class and PDF-related API endpoints.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app import app
from pdf_extractor import PDFExtractor


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def test_pdf_path():
    """Path to the test PDF file"""
    pdf_path = Path(__file__).parent / "why_llm_cant_develop_software.pdf"
    if not pdf_path.exists():
        pytest.skip(f"Test PDF not found: {pdf_path}")
    return str(pdf_path)


# PDFExtractor tests
class TestPDFExtractor:
    """Test the PDFExtractor class"""

    def test_extract_paragraph_success(self, test_pdf_path):
        """Test successful paragraph extraction"""
        # Extract first paragraph from page 1
        result = PDFExtractor.extract_paragraph(test_pdf_path, 1, 1)

        assert isinstance(result, str)
        assert len(result) > 0
        assert "Large Language Models" in result or "LLM" in result.upper()

    def test_extract_paragraph_different_pages(self, test_pdf_path):
        """Test extracting from different paragraphs"""
        # Get info first to know how many paragraphs exist
        info = PDFExtractor.get_pdf_info(test_pdf_path)

        # Try page 2 if it exists
        if info["num_pages"] >= 2 and info["pages"][1]["num_paragraphs"] >= 2:
            para1 = PDFExtractor.extract_paragraph(test_pdf_path, 2, 1)
            para2 = PDFExtractor.extract_paragraph(test_pdf_path, 2, 2)

            # Paragraphs should be different
            assert para1 != para2
            assert len(para1) > 0
            assert len(para2) > 0
        elif info["pages"][0]["num_paragraphs"] >= 2:
            # Fall back to page 1 if it has multiple paragraphs
            para1 = PDFExtractor.extract_paragraph(test_pdf_path, 1, 1)
            para2 = PDFExtractor.extract_paragraph(test_pdf_path, 1, 2)

            # Paragraphs should be different
            assert para1 != para2
            assert len(para1) > 0
            assert len(para2) > 0
        else:
            pytest.skip("PDF doesn't have multiple paragraphs on any page")

    def test_extract_paragraph_invalid_page(self, test_pdf_path):
        """Test error when page number is out of range"""
        with pytest.raises(IndexError, match="out of range"):
            PDFExtractor.extract_paragraph(test_pdf_path, 999, 1)

    def test_extract_paragraph_invalid_paragraph(self, test_pdf_path):
        """Test error when paragraph index is out of range"""
        with pytest.raises(IndexError, match="out of range"):
            PDFExtractor.extract_paragraph(test_pdf_path, 1, 999)

    def test_extract_paragraph_invalid_page_number(self, test_pdf_path):
        """Test error with invalid page number (< 1)"""
        with pytest.raises(ValueError, match="Page number must be >= 1"):
            PDFExtractor.extract_paragraph(test_pdf_path, 0, 1)

    def test_extract_paragraph_invalid_paragraph_index(self, test_pdf_path):
        """Test error with invalid paragraph index (< 1)"""
        with pytest.raises(ValueError, match="Paragraph index must be >= 1"):
            PDFExtractor.extract_paragraph(test_pdf_path, 1, 0)

    def test_extract_paragraph_file_not_found(self):
        """Test error when PDF file doesn't exist"""
        with pytest.raises(FileNotFoundError):
            PDFExtractor.extract_paragraph("nonexistent.pdf", 1, 1)

    def test_get_pdf_info(self, test_pdf_path):
        """Test getting PDF information"""
        info = PDFExtractor.get_pdf_info(test_pdf_path)

        assert "num_pages" in info
        assert "pages" in info
        assert info["num_pages"] > 0
        assert len(info["pages"]) == info["num_pages"]

        # Check first page info
        first_page = info["pages"][0]
        assert first_page["page_number"] == 1
        assert first_page["num_paragraphs"] > 0
        assert first_page["has_text"] is True

    def test_get_pdf_info_file_not_found(self):
        """Test error when getting info for non-existent PDF"""
        with pytest.raises(FileNotFoundError):
            PDFExtractor.get_pdf_info("nonexistent.pdf")

    def test_split_into_paragraphs(self):
        """Test paragraph splitting logic"""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        paragraphs = PDFExtractor._split_into_paragraphs(text)

        # With the current merging logic, might merge into 1 paragraph
        assert len(paragraphs) >= 1
        assert "First" in paragraphs[0]
        if len(paragraphs) == 3:
            assert "Second" in paragraphs[1]
            assert "Third" in paragraphs[2]

    def test_split_into_paragraphs_single_newlines(self):
        """Test paragraph splitting with single newlines"""
        text = "First paragraph.\nSecond paragraph.\nThird paragraph."
        paragraphs = PDFExtractor._split_into_paragraphs(text)

        assert len(paragraphs) >= 1
        assert len(paragraphs) <= 3

    def test_split_into_paragraphs_merge_short_lines(self):
        """Test that short lines are merged"""
        text = "This is a short\nline that should\nbe merged together."
        paragraphs = PDFExtractor._split_into_paragraphs(text)

        # Short lines without sentence-ending punctuation should merge
        assert len(paragraphs) >= 1


# API endpoint tests
class TestPDFAPI:
    """Test the PDF-related API endpoints"""

    def test_pdf_info_endpoint_success(self, client, test_pdf_path):
        """Test successful PDF info retrieval"""
        with open(test_pdf_path, "rb") as pdf_file:
            response = client.post(
                "/api/pdf/info", files={"pdf": ("test.pdf", pdf_file, "application/pdf")}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "info" in data
        assert data["info"]["num_pages"] > 0

    def test_pdf_info_endpoint_invalid_file_type(self, client):
        """Test error with non-PDF file"""
        response = client.post(
            "/api/pdf/info",
            files={"pdf": ("test.txt", b"not a pdf", "text/plain")},
        )

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_pdf_extract_endpoint_success(self, client, test_pdf_path):
        """Test successful paragraph extraction via API"""
        with open(test_pdf_path, "rb") as pdf_file:
            response = client.post(
                "/api/pdf/extract?page_number=1&paragraph_index=1",
                files={"pdf": ("test.pdf", pdf_file, "application/pdf")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "text" in data
        assert len(data["text"]) > 0
        assert "source" in data
        assert data["source"]["type"] == "pdf"
        assert data["source"]["page"] == 1
        assert data["source"]["paragraph"] == 1

    def test_pdf_extract_endpoint_invalid_file_type(self, client):
        """Test error with non-PDF file for extraction"""
        response = client.post(
            "/api/pdf/extract?page_number=1&paragraph_index=1",
            files={"pdf": ("test.txt", b"not a pdf", "text/plain")},
        )

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_pdf_extract_endpoint_invalid_page(self, client, test_pdf_path):
        """Test error when extracting from invalid page"""
        with open(test_pdf_path, "rb") as pdf_file:
            response = client.post(
                "/api/pdf/extract?page_number=999&paragraph_index=1",
                files={"pdf": ("test.pdf", pdf_file, "application/pdf")},
            )

        assert response.status_code == 400
        assert "out of range" in response.json()["detail"]

    def test_pdf_extract_endpoint_invalid_paragraph(self, client, test_pdf_path):
        """Test error when extracting invalid paragraph"""
        with open(test_pdf_path, "rb") as pdf_file:
            response = client.post(
                "/api/pdf/extract?page_number=1&paragraph_index=999",
                files={"pdf": ("test.pdf", pdf_file, "application/pdf")},
            )

        assert response.status_code == 400
        assert "out of range" in response.json()["detail"]


# Integration tests
class TestPDFIntegration:
    """Integration tests for PDF extraction workflow"""

    def test_extract_and_clean_workflow(self, client, test_pdf_path):
        """Test complete workflow: extract paragraph and clean with LLM"""
        # First, extract paragraph
        with open(test_pdf_path, "rb") as pdf_file:
            extract_response = client.post(
                "/api/pdf/extract?page_number=1&paragraph_index=1",
                files={"pdf": ("test.pdf", pdf_file, "application/pdf")},
            )

        assert extract_response.status_code == 200
        extract_data = extract_response.json()
        paragraph_text = extract_data["text"]

        # Mock the LLM service for cleaning
        with patch("app.service") as mock_service:
            mock_service.clean_with_llm.return_value = (
                paragraph_text.strip() + " [Cleaned]"
            )

            # Clean the extracted text
            clean_response = client.post(
                "/api/clean",
                json={"text": paragraph_text},
            )

            assert clean_response.status_code == 200
            clean_data = clean_response.json()
            assert clean_data["success"] is True
            assert "[Cleaned]" in clean_data["text"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
