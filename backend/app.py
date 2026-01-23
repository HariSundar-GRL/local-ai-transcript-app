import logging
import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pdf_extractor import PDFExtractor
from transcription import TranscriptionService

load_dotenv()

# Configure logging with timestamp
LOG_FILE = Path(__file__).parent / "app_debug.log"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class CleanRequest(BaseModel):
    text: str
    system_prompt: str | None = None


class MindMapRequest(BaseModel):
    text: str


class PDFExtractRequest(BaseModel):
    page_number: int
    paragraph_index: int


service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uses OpenAI-compatible API (Ollama, OpenAI, LM Studio, etc.). Configure via .env file."""
    global service
    logger.info("🚀 Starting AI Transcript App...")

    try:
        service = TranscriptionService(
            whisper_model=os.getenv("WHISPER_MODEL"),
            llm_base_url=os.getenv("LLM_BASE_URL"),
            llm_api_key=os.getenv("LLM_API_KEY"),
            llm_model=os.getenv("LLM_MODEL"),
        )
        logger.info("✅ Ready!")
    except Exception as e:
        logger.error(f"Failed to initialize service: {e}", exc_info=True)
        raise
    yield


app = FastAPI(title="AI Transcript App", lifespan=lifespan)

# CORS for localhost development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server (Vite)
        "http://localhost:3001",  # Vite alternative port
        "http://localhost:3002",  # Vite alternative port
        "http://localhost:5173",  # Vite default alternative
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/status")
async def get_status():
    return {
        "status": "ready" if service else "initializing",
        "whisper_model": os.getenv("WHISPER_MODEL"),
        "llm_model": os.getenv("LLM_MODEL"),
        "llm_base_url": os.getenv("LLM_BASE_URL"),
    }


@app.get("/api/system-prompt")
async def get_system_prompt():
    if not service:
        raise HTTPException(status_code=503, detail="Service not ready")

    return {"default_prompt": service.get_default_system_prompt()}


@app.post("/api/transcribe")
async def transcribe_audio(audio: Annotated[UploadFile, File()]):
    logger.debug(f"Transcription request received for file: {audio.filename}")

    if not service:
        logger.error("Service not ready for transcription request")
        raise HTTPException(
            status_code=503, detail="Service not ready, still initializing models"
        )

    suffix = os.path.splitext(audio.filename)[1] or ".webm"
    logger.debug(f"Audio file suffix: {suffix}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name
        logger.debug(
            f"Audio saved to temp file: {tmp_path}, size: {len(content)} bytes"
        )

    try:
        raw_text = service.transcribe(tmp_path)
        logger.info(f"Transcription successful, text length: {len(raw_text)}")
        return {"success": True, "text": raw_text}

    except Exception as e:
        logger.error(
            f"Transcription error for file {audio.filename}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Transcription failed: {str(e)}"
        ) from e

    finally:
        # Always clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
            logger.debug(f"Cleaned up temp file: {tmp_path}")


@app.post("/api/clean")
async def clean_text(request: CleanRequest):
    logger.debug(f"Clean text request received, text length: {len(request.text)}")

    if not service:
        logger.error("Service not ready for clean text request")
        raise HTTPException(status_code=503, detail="Service not ready")

    try:
        cleaned_text = service.clean_with_llm(
            request.text, system_prompt=request.system_prompt
        )
        logger.info(f"Text cleaning successful, output length: {len(cleaned_text)}")
        return {"success": True, "text": cleaned_text}

    except Exception as e:
        logger.error(f"LLM cleaning error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Cleaning failed: {str(e)}") from e


@app.post("/api/mindmap")
async def generate_mindmap(request: MindMapRequest):
    logger.debug(
        f"Mind-map generation request received, text length: {len(request.text)}"
    )

    if not service:
        logger.error("Service not ready for mind-map generation request")
        raise HTTPException(status_code=503, detail="Service not ready")

    try:
        dot_code = service.generate_mindmap(request.text)
        logger.debug(f"DOT code generated, length: {len(dot_code)}")

        # Convert DOT to SVG using graphviz
        import subprocess

        result = subprocess.run(
            ["dot", "-Tsvg"], input=dot_code.encode(), capture_output=True, timeout=10
        )

        if result.returncode != 0:
            logger.error(f"Graphviz conversion failed: {result.stderr.decode()}")
            raise Exception(f"Graphviz error: {result.stderr.decode()}")

        svg_content = result.stdout.decode()
        logger.info(
            f"Mind-map SVG generated successfully, size: {len(svg_content)} bytes"
        )
        return {"success": True, "svg": svg_content, "dot": dot_code}

    except FileNotFoundError:
        logger.error("Graphviz not found - install it: apt-get install graphviz")
        raise HTTPException(
            status_code=500,
            detail="Graphviz not installed. Please install graphviz on the system.",
        ) from None
    except Exception as e:
        logger.error(f"Mind-map generation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Mind-map generation failed: {str(e)}"
        ) from e


@app.post("/api/pdf/info")
async def get_pdf_info(pdf: Annotated[UploadFile, File()]):
    """Get information about a PDF file (page count, paragraphs per page)."""
    logger.debug(f"PDF info request received for file: {pdf.filename}")

    if not pdf.filename or not pdf.filename.lower().endswith(".pdf"):
        logger.warning(f"Invalid file type rejected: {pdf.filename}")
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only PDF files are accepted."
        )

    # Save to temp file
    suffix = ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await pdf.read()
        tmp.write(content)
        tmp_path = tmp.name
        logger.debug(f"PDF saved to temp file: {tmp_path}, size: {len(content)} bytes")

    try:
        info = PDFExtractor.get_pdf_info(tmp_path)
        logger.info(f"PDF info extracted successfully: {info}")
        return {"success": True, "info": info}

    except FileNotFoundError:
        logger.error(f"PDF file not found: {tmp_path}")
        raise HTTPException(status_code=404, detail="PDF file not found") from None
    except Exception as e:
        logger.error(
            f"PDF info extraction error for {pdf.filename}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to read PDF: {str(e)}"
        ) from e

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
            logger.debug(f"Cleaned up temp file: {tmp_path}")


@app.post("/api/pdf/extract")
async def extract_pdf_paragraph(
    pdf: Annotated[UploadFile, File()],
    page_number: int,
    paragraph_index: int,
):
    """
    Extract a specific paragraph from a PDF file and return it as transcript text.
    The paragraph can then be cleaned/processed like audio transcriptions.
    """
    if not pdf.filename or not pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only PDF files are accepted."
        )

    # Save to temp file
    suffix = ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await pdf.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        paragraph_text = PDFExtractor.extract_paragraph(
            tmp_path, page_number, paragraph_index
        )

        return {
            "success": True,
            "text": paragraph_text,
            "source": {
                "type": "pdf",
                "filename": pdf.filename,
                "page": page_number,
                "paragraph": paragraph_index,
            },
        }

    except (FileNotFoundError, IndexError, ValueError) as e:
        logger.error(
            f"PDF extraction error for {pdf.filename} (page {page_number}, para {paragraph_index}): {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"PDF processing error for {pdf.filename}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to extract paragraph: {str(e)}"
        ) from e

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
            logger.debug(f"Cleaned up temp file: {tmp_path}")


@app.post("/api/pdf/extract-page")
async def extract_pdf_page(
    pdf: Annotated[UploadFile, File()],
    page_number: int,
):
    """
    Extract all text from a specific page of a PDF file.
    """
    if not pdf.filename or not pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only PDF files are accepted."
        )

    # Save to temp file
    suffix = ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await pdf.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        page_text = PDFExtractor.extract_page(tmp_path, page_number)

        return {
            "success": True,
            "text": page_text,
            "source": {
                "type": "pdf",
                "filename": pdf.filename,
                "page": page_number,
                "extraction_mode": "page",
            },
        }

    except (FileNotFoundError, IndexError, ValueError) as e:
        logger.error(
            f"PDF page extraction error for {pdf.filename} (page {page_number}): {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"PDF processing error for {pdf.filename}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to extract page: {str(e)}"
        ) from e

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
            logger.debug(f"Cleaned up temp file: {tmp_path}")


@app.post("/api/pdf/extract-all")
async def extract_pdf_all(
    pdf: Annotated[UploadFile, File()],
):
    """
    Extract all text from all pages of a PDF file.
    """
    if not pdf.filename or not pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only PDF files are accepted."
        )

    # Save to temp file
    suffix = ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await pdf.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        all_text = PDFExtractor.extract_all(tmp_path)

        return {
            "success": True,
            "text": all_text,
            "source": {
                "type": "pdf",
                "filename": pdf.filename,
                "extraction_mode": "all",
            },
        }

    except (FileNotFoundError, ValueError) as e:
        logger.error(
            f"PDF full extraction error for {pdf.filename}: {e}", exc_info=True
        )
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"PDF processing error for {pdf.filename}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to extract PDF: {str(e)}"
        ) from e

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
            logger.debug(f"Cleaned up temp file: {tmp_path}")
