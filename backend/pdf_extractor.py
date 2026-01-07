#!/usr/bin/env python3
"""
PDF text extraction utilities.
Extracts specific paragraphs from PDF files for transcript processing.
"""

from pathlib import Path

from pypdf import PdfReader


class PDFExtractor:
    """Extracts text from PDF files, paragraph by paragraph."""

    @staticmethod
    def extract_paragraph(pdf_path: str, page_number: int, paragraph_index: int) -> str:
        """
        Extract a specific paragraph from a PDF page.

        Args:
            pdf_path: Path to the PDF file
            page_number: Page number (1-indexed for user, converted to 0-indexed)
            paragraph_index: Paragraph index on that page (1-indexed for user)

        Returns:
            The extracted paragraph text

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            IndexError: If page or paragraph index is out of range
            ValueError: If invalid parameters provided
        """
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if page_number < 1:
            raise ValueError(f"Page number must be >= 1, got {page_number}")

        if paragraph_index < 1:
            raise ValueError(f"Paragraph index must be >= 1, got {paragraph_index}")

        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)

            # Convert to 0-indexed
            page_idx = page_number - 1

            if page_idx >= total_pages:
                raise IndexError(
                    f"Page {page_number} out of range. PDF has {total_pages} pages"
                )

            page = reader.pages[page_idx]
            text = page.extract_text()

            if not text or not text.strip():
                raise ValueError(f"No text found on page {page_number}")

            # Split into paragraphs (separated by double newlines or single newlines)
            # Clean up the text first
            paragraphs = PDFExtractor._split_into_paragraphs(text)

            if not paragraphs:
                raise ValueError(f"No paragraphs found on page {page_number}")

            # Convert to 0-indexed
            para_idx = paragraph_index - 1

            if para_idx >= len(paragraphs):
                raise IndexError(
                    f"Paragraph {paragraph_index} out of range. "
                    f"Page {page_number} has {len(paragraphs)} paragraphs"
                )

            return paragraphs[para_idx]

        except Exception as e:
            if isinstance(e, (FileNotFoundError, IndexError, ValueError)):
                raise
            raise ValueError(f"Error processing PDF: {str(e)}") from e

    @staticmethod
    def _split_into_paragraphs(text: str) -> list[str]:
        """
        Split text into paragraphs.
        Handles various paragraph separation patterns in PDFs.

        Args:
            text: Raw text extracted from PDF

        Returns:
            List of paragraph strings
        """
        import re

        # First, try to split by double newlines (common paragraph separator)
        if "\n\n" in text:
            paragraphs = text.split("\n\n")
            paragraphs = [" ".join(p.split()) for p in paragraphs if p.strip()]
            if len(paragraphs) > 1:
                return paragraphs

        # If that doesn't work, try splitting by single newlines
        # but merge lines that don't end with sentence terminators
        lines = text.split("\n")
        paragraphs = []
        current = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # If current is empty, start new paragraph
            if not current:
                current = line
            # If previous line ends with sentence terminator and this line starts
            # with capital or number, start new paragraph
            elif (current.rstrip()[-1:] in ".!?") and (
                line[0:1].isupper() or line[0:1].isdigit()
            ):
                paragraphs.append(current)
                current = line
            # Otherwise, continue current paragraph
            else:
                current += " " + line

        # Add last paragraph
        if current:
            paragraphs.append(current)

        # If still only one paragraph, try to split by sentence-ending patterns
        # followed by capital letters (more aggressive)
        if len(paragraphs) == 1 and len(paragraphs[0]) > 500:
            text = paragraphs[0]
            # Split on ". " followed by capital letter or number
            sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', text)

            # Group sentences into paragraphs (roughly 3-5 sentences each)
            paragraphs = []
            current = ""
            sentence_count = 0

            for sentence in sentences:
                if sentence_count < 3:
                    current += " " + sentence if current else sentence
                    sentence_count += 1
                else:
                    if current:
                        paragraphs.append(current.strip())
                    current = sentence
                    sentence_count = 1

            if current:
                paragraphs.append(current.strip())

        return paragraphs if paragraphs else [text.strip()]

    @staticmethod
    def get_pdf_info(pdf_path: str) -> dict:
        """
        Get basic information about a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary with PDF metadata
        """
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        reader = PdfReader(pdf_path)
        info = {
            "num_pages": len(reader.pages),
            "metadata": reader.metadata,
            "pages": [],
        }

        # Get paragraph counts for each page
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            paragraphs = PDFExtractor._split_into_paragraphs(text) if text else []
            info["pages"].append(
                {
                    "page_number": page_num,
                    "num_paragraphs": len(paragraphs),
                    "has_text": bool(text and text.strip()),
                }
            )

        return info

    @staticmethod
    def extract_page(pdf_path: str, page_number: int) -> str:
        """
        Extract all text from a specific page.

        Args:
            pdf_path: Path to the PDF file
            page_number: Page number (1-indexed)

        Returns:
            All text from the page

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            IndexError: If page number is out of range
            ValueError: If invalid parameters provided
        """
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if page_number < 1:
            raise ValueError(f"Page number must be >= 1, got {page_number}")

        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)

            # Convert to 0-indexed
            page_idx = page_number - 1

            if page_idx >= total_pages:
                raise IndexError(
                    f"Page {page_number} out of range. PDF has {total_pages} pages"
                )

            page = reader.pages[page_idx]
            text = page.extract_text()

            if not text or not text.strip():
                raise ValueError(f"No text found on page {page_number}")

            # Clean up the text - normalize whitespace
            text = " ".join(text.split())
            return text

        except Exception as e:
            if isinstance(e, (FileNotFoundError, IndexError, ValueError)):
                raise
            raise ValueError(f"Error processing PDF: {str(e)}") from e

    @staticmethod
    def extract_all(pdf_path: str) -> str:
        """
        Extract all text from all pages of a PDF.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            All text from the PDF

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If PDF has no text or other errors
        """
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)

            if total_pages == 0:
                raise ValueError("PDF has no pages")

            all_text = []
            for page_num in range(total_pages):
                page = reader.pages[page_num]
                text = page.extract_text()
                if text and text.strip():
                    # Normalize whitespace
                    text = " ".join(text.split())
                    all_text.append(text)

            if not all_text:
                raise ValueError("No text found in PDF")

            # Join all pages with double space
            return "  ".join(all_text)

        except Exception as e:
            if isinstance(e, (FileNotFoundError, ValueError)):
                raise
            raise ValueError(f"Error processing PDF: {str(e)}") from e
