import { useState, useRef } from 'react';
import { FileText, Upload, FileCheck } from 'lucide-react';
import styles from './PDFUpload.module.css';
import { Box } from './Box';

interface PDFInfo {
  num_pages: number;
  pages: Array<{
    page_number: number;
    num_paragraphs: number;
    has_text: boolean;
  }>;
}

interface PDFUploadProps {
  onExtract: (text: string, source: any) => void;
}

type ExtractionMode = 'paragraph' | 'page' | 'all';

export function PDFUpload({ onExtract }: PDFUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [pdfInfo, setPdfInfo] = useState<PDFInfo | null>(null);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [paragraphIndex, setParagraphIndex] = useState<number>(1);
  const [extractionMode, setExtractionMode] =
    useState<ExtractionMode>('paragraph');
  const [isLoading, setIsLoading] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert('Please select a PDF file');
      return;
    }

    setSelectedFile(file);
    setPdfInfo(null);
    setPageNumber(1);
    setParagraphIndex(1);

    // Get PDF info
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('pdf', file);

      const response = await fetch('/api/pdf/info', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to read PDF info');
      }

      const data = await response.json();
      setPdfInfo(data.info);
    } catch (error) {
      console.error('Error reading PDF:', error);
      alert('Failed to read PDF file. Please try another file.');
      setSelectedFile(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExtract = async () => {
    if (!selectedFile || !pdfInfo) return;

    setIsExtracting(true);
    try {
      const formData = new FormData();
      formData.append('pdf', selectedFile);

      let endpoint = '/api/pdf/extract';
      let queryParams = '';

      if (extractionMode === 'paragraph') {
        queryParams = `?page_number=${pageNumber}&paragraph_index=${paragraphIndex}`;
      } else if (extractionMode === 'page') {
        endpoint = '/api/pdf/extract-page';
        queryParams = `?page_number=${pageNumber}`;
      } else if (extractionMode === 'all') {
        endpoint = '/api/pdf/extract-all';
      }

      const response = await fetch(`${endpoint}${queryParams}`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to extract text');
      }

      const data = await response.json();
      onExtract(data.text, data.source);
    } catch (error: any) {
      console.error('Error extracting text:', error);
      alert(error.message || 'Failed to extract text from PDF');
    } finally {
      setIsExtracting(false);
    }
  };

  const currentPageInfo = pdfInfo?.pages.find(
    (p) => p.page_number === pageNumber
  );

  return (
    <Box header="PDF Paragraph Extraction" icon={FileText}>
      <div className={styles.pdfUpload}>
        <div className={styles.uploadSection}>
          <div className={styles.fileInputWrapper}>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handleFileSelect}
              className={styles.fileInput}
              id="pdf-upload"
            />
            <label htmlFor="pdf-upload">
              <button
                className={styles.fileButton}
                onClick={() => fileInputRef.current?.click()}
                disabled={isLoading}
                type="button"
              >
                {isLoading ? (
                  <>
                    <div className={styles.spinner}></div>
                    <span>Loading PDF...</span>
                  </>
                ) : (
                  <>
                    <Upload size={20} />
                    <span>Select PDF File</span>
                  </>
                )}
              </button>
            </label>
          </div>

          {selectedFile && (
            <div className={styles.fileName}>
              <FileCheck size={16} />
              <span>{selectedFile.name}</span>
            </div>
          )}
        </div>

        {pdfInfo && (
          <>
            <div className={styles.pdfInfo}>
              <div className={styles.infoTitle}>
                <FileText size={18} />
                PDF Information
              </div>
              <div className={styles.infoGrid}>
                <div className={styles.infoItem}>
                  <strong>Total Pages:</strong> {pdfInfo.num_pages}
                </div>
                <div className={styles.infoItem}>
                  <strong>Current Page Paragraphs:</strong>{' '}
                  {currentPageInfo?.num_paragraphs || 0}
                </div>
              </div>
            </div>

            <div className={styles.selectionSection}>
              <div className={styles.inputGroup}>
                <label htmlFor="extraction-mode">Extraction Mode</label>
                <select
                  id="extraction-mode"
                  value={extractionMode}
                  onChange={(e) =>
                    setExtractionMode(e.target.value as ExtractionMode)
                  }
                  className={styles.modeSelect}
                >
                  <option value="paragraph">Single Paragraph</option>
                  <option value="page">Full Page</option>
                  <option value="all">Whole PDF</option>
                </select>
              </div>

              {extractionMode === 'paragraph' && (
                <>
                  <div className={styles.inputRow}>
                    <div className={styles.inputGroup}>
                      <label htmlFor="page-number">Page Number</label>
                      <input
                        id="page-number"
                        type="number"
                        min="1"
                        max={pdfInfo.num_pages}
                        value={pageNumber}
                        onChange={(e) =>
                          setPageNumber(
                            Math.max(1, parseInt(e.target.value) || 1)
                          )
                        }
                      />
                    </div>

                    <div className={styles.inputGroup}>
                      <label htmlFor="paragraph-index">Paragraph Index</label>
                      <input
                        id="paragraph-index"
                        type="number"
                        min="1"
                        max={currentPageInfo?.num_paragraphs || 1}
                        value={paragraphIndex}
                        onChange={(e) =>
                          setParagraphIndex(
                            Math.max(1, parseInt(e.target.value) || 1)
                          )
                        }
                      />
                    </div>
                  </div>

                  <p className={styles.hint}>
                    Page {pageNumber} has {currentPageInfo?.num_paragraphs || 0}{' '}
                    paragraph(s)
                  </p>
                </>
              )}

              {extractionMode === 'page' && (
                <>
                  <div className={styles.inputGroup}>
                    <label htmlFor="page-number-single">Page Number</label>
                    <input
                      id="page-number-single"
                      type="number"
                      min="1"
                      max={pdfInfo.num_pages}
                      value={pageNumber}
                      onChange={(e) =>
                        setPageNumber(
                          Math.max(1, parseInt(e.target.value) || 1)
                        )
                      }
                    />
                  </div>

                  <p className={styles.hint}>
                    Will extract all text from page {pageNumber}
                  </p>
                </>
              )}

              {extractionMode === 'all' && (
                <p className={styles.hint}>
                  Will extract all text from all {pdfInfo.num_pages} pages
                </p>
              )}

              <button
                className={styles.extractButton}
                onClick={handleExtract}
                disabled={isExtracting || !currentPageInfo?.has_text}
              >
                {isExtracting ? (
                  <>
                    <div className={styles.spinner}></div>
                    <span>Extracting...</span>
                  </>
                ) : (
                  <>
                    <FileText size={20} />
                    <span>
                      {extractionMode === 'paragraph' && 'Extract Paragraph'}
                      {extractionMode === 'page' && 'Extract Page'}
                      {extractionMode === 'all' && 'Extract Whole PDF'}
                    </span>
                  </>
                )}
              </button>
            </div>
          </>
        )}
      </div>
    </Box>
  );
}
