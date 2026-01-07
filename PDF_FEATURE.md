# PDF Paragraph Extraction Feature

## Overview

The PDF paragraph extraction feature extends the local-ai-transcript app to accept PDF documents as input. Instead of transcribing audio, you can extract specific paragraphs from PDF files and process them through the same AI pipeline (cleaning, normalization, punctuation, mind-map generation).

## How It Works

### Workflow

1. **Upload PDF**: Select a PDF file using the upload button
2. **Get Info**: The app automatically reads the PDF and shows:
   - Total number of pages
   - Number of paragraphs on each page
3. **Select Paragraph**: Choose a specific page and paragraph index
4. **Extract**: The paragraph text is extracted and treated as a "transcript"
5. **Process**: The text goes through the same LLM cleaning pipeline as audio transcripts
6. **Generate Mind-map**: Optionally create a visual mind-map from the extracted text

### Backend Components

#### `pdf_extractor.py`

The core PDF extraction module containing the `PDFExtractor` class.

**Key Methods:**

- `extract_paragraph(pdf_path, page_number, paragraph_index)` - Extracts a specific paragraph
- `get_pdf_info(pdf_path)` - Returns PDF metadata (pages, paragraph counts)
- `_split_into_paragraphs(text)` - Intelligently splits text into paragraphs

**Features:**

- 1-indexed parameters for user convenience (converted internally to 0-indexed)
- Smart paragraph detection (handles double newlines, sentence endings)
- Merges short lines that are likely continuation of paragraphs
- Comprehensive error handling with descriptive messages

#### API Endpoints

**`POST /api/pdf/info`**

Get information about a PDF file.

Request:

```
multipart/form-data
- pdf: PDF file
```

Response:

```json
{
  "success": true,
  "info": {
    "num_pages": 1,
    "pages": [
      {
        "page_number": 1,
        "num_paragraphs": 5,
        "has_text": true
      }
    ]
  }
}
```

**`POST /api/pdf/extract?page_number={page}&paragraph_index={para}`**

Extract a specific paragraph from a PDF.

Request:

```
Query parameters:
- page_number: Page number (1-indexed)
- paragraph_index: Paragraph index on that page (1-indexed)

multipart/form-data:
- pdf: PDF file
```

Response:

```json
{
  "success": true,
  "text": "The extracted paragraph text...",
  "source": {
    "type": "pdf",
    "filename": "document.pdf",
    "page": 1,
    "paragraph": 1
  }
}
```

### Frontend Components

#### `PDFUpload.tsx`

React component for PDF upload and paragraph selection.

**Features:**

- File validation (PDF only)
- Automatic PDF info loading on file select
- Page and paragraph number inputs with validation
- Real-time feedback on available paragraphs
- Loading states during extraction
- Integration with existing transcript processing pipeline

**Props:**

- `onExtract: (text: string, source: any) => void` - Callback when paragraph is extracted

## Usage Example

### 1. Using the UI

1. Start the backend:

   ```bash
   cd backend
   uvicorn app:app --reload
   ```

2. Start the frontend:

   ```bash
   cd frontend
   npm run dev
   ```

3. In the browser:
   - Click "PDF Paragraph Extraction" section
   - Click "Select PDF File"
   - Choose your PDF
   - Select page and paragraph numbers
   - Click "Extract Paragraph"
   - The text appears in the transcription results
   - Use "Clean with LLM" or "Generate Mind-map" as usual

### 2. Using the API Directly

```python
import requests

# Get PDF info
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/pdf/info',
        files={'pdf': f}
    )
    info = response.json()
    print(f"Pages: {info['info']['num_pages']}")

# Extract paragraph
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/pdf/extract',
        files={'pdf': f},
        params={'page_number': 1, 'paragraph_index': 1}
    )
    data = response.json()
    print(f"Extracted: {data['text']}")

# Clean with LLM
response = requests.post(
    'http://localhost:8000/api/clean',
    json={'text': data['text']}
)
cleaned = response.json()
print(f"Cleaned: {cleaned['text']}")
```

### 3. Using Python Module Directly

```python
from pdf_extractor import PDFExtractor

# Get PDF information
info = PDFExtractor.get_pdf_info('document.pdf')
print(f"Total pages: {info['num_pages']}")
for page in info['pages']:
    print(f"Page {page['page_number']}: {page['num_paragraphs']} paragraphs")

# Extract specific paragraph
text = PDFExtractor.extract_paragraph('document.pdf', page_number=1, paragraph_index=1)
print(f"Extracted text: {text}")
```

## Testing

### Unit Tests

Comprehensive tests in `test_pdf_extraction.py`:

```bash
cd backend
pytest test_pdf_extraction.py -v
```

**Test Coverage:**

- PDFExtractor class methods
- Paragraph splitting logic
- API endpoints
- Error handling (invalid pages, paragraphs, files)
- Integration with LLM cleaning pipeline

**Test Results:** 18 passed, 1 skipped, 87% coverage of pdf_extractor.py

### Test PDF

A sample PDF `why_llm_cant_develop_software.pdf` is included for testing. You can create it with:

```bash
cd backend
python create_test_pdf.py
```

## Dependencies

Added to `pyproject.toml`:

```toml
dependencies = [
    ...
    "pypdf>=5.1.0",
]
```

Install with:

```bash
pip install pypdf
```

Or reinstall the package:

```bash
pip install -e ".[dev]"
```

## Error Handling

The feature includes comprehensive error handling:

- **File not found**: Clear error if PDF doesn't exist
- **Invalid page**: Error with total page count
- **Invalid paragraph**: Error with paragraph count for that page
- **No text**: Error if page has no extractable text
- **Invalid file type**: Rejects non-PDF files
- **Corrupted PDF**: Graceful error handling

## Limitations

1. **Text-based PDFs only**: Cannot extract from image-based or scanned PDFs (OCR not implemented)
2. **Paragraph detection**: Uses heuristics that work well for most PDFs but may need adjustment for unusual formatting
3. **Layout preservation**: Does not preserve complex layouts, tables, or multi-column text
4. **File size**: Large PDFs may take time to process

## Future Enhancements

- [ ] OCR support for scanned PDFs
- [ ] Extract all paragraphs from a page at once
- [ ] Preview paragraph before extraction
- [ ] Support for extracting from page ranges
- [ ] Better handling of tables and multi-column layouts
- [ ] Caching of PDF info to avoid re-parsing
- [ ] Download extracted paragraphs as text file
- [ ] Batch extraction from multiple PDFs

## Integration with Existing Features

The extracted PDF text integrates seamlessly with:

- **LLM Cleaning**: Normalize and punctuate extracted text
- **Mind-map Generation**: Visualize extracted content
- **System Prompts**: Custom prompts work with PDF text
- **Copy/Export**: Same functionality as audio transcripts

## Architecture Notes

The PDF feature follows the same architecture as the audio transcription:

1. **Input Source** → PDF file (instead of audio)
2. **Extraction** → Paragraph text (instead of Whisper transcription)
3. **Processing** → LLM cleaning (same pipeline)
4. **Output** → Cleaned text, mind-maps (same as audio)

This design allows PDF and audio inputs to be processed identically after extraction, maintaining code reuse and consistency.
