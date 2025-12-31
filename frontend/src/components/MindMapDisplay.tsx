import { Network, Download } from 'lucide-react';
import styles from './MindMapDisplay.module.css';
import { Box } from './Box';

interface MindMapDisplayProps {
  svgContent: string | null;
  isGenerating: boolean;
}

export function MindMapDisplay({
  svgContent,
  isGenerating,
}: MindMapDisplayProps) {
  if (!svgContent && !isGenerating) {
    return null;
  }

  const handleDownload = () => {
    if (!svgContent) return;

    const blob = new Blob([svgContent], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `mindmap-${Date.now()}.svg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <Box header="Mind-map Visualization" icon={Network}>
      <div className={styles.container}>
        {isGenerating ? (
          <div className={styles.loading}>
            <div className={styles.spinner}></div>
            <p>Generating mind-map...</p>
          </div>
        ) : (
          <>
            <div
              className={styles.svgContainer}
              dangerouslySetInnerHTML={{ __html: svgContent || '' }}
            />
            <button
              onClick={handleDownload}
              className={styles.downloadButton}
              aria-label="Download mind-map as SVG"
            >
              <Download className={styles.icon} />
              <span>Download SVG</span>
            </button>
          </>
        )}
      </div>
    </Box>
  );
}
