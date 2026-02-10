interface ExportOptions {
  filename: string;
  format: 'png' | 'pdf';
}

// Type declarations for CDN-loaded libraries
declare global {
  interface Window {
    html2canvas: any;
    jspdf: {
      jsPDF: any;
    };
  }
}

/**
 * Export dashboard as PNG or PDF using browser screenshot
 * Captures the exact rendered layout with proper dimensions
 */
export const exportDashboardScreenshot = async (
  options: ExportOptions
): Promise<Blob> => {
  const { filename, format } = options;

  // Find the main dashboard container
  const dashboardContainer = document.querySelector('[data-dashboard-container]') as HTMLElement;
  if (!dashboardContainer) {
    throw new Error('Dashboard container not found');
  }

  // Find the scrollable widget area
  const scrollableArea = dashboardContainer.querySelector('[data-dashboard-grid-container]') as HTMLElement;
  if (!scrollableArea) {
    throw new Error('Dashboard grid container not found');
  }

  // Get the actual rendered width (excluding scrollbar)
  const actualWidth = scrollableArea.clientWidth;

  // Store original styles for restoration
  const originalStyles = {
    container: {
      height: dashboardContainer.style.height,
      overflow: dashboardContainer.style.overflow,
    },
    scrollArea: {
      height: scrollableArea.style.height,
      maxHeight: scrollableArea.style.maxHeight,
      overflow: scrollableArea.style.overflow,
      width: scrollableArea.style.width,
    }
  };

  // Hide elements marked for export exclusion (buttons, action menus, etc.)
  const excludedElements = document.querySelectorAll('[data-export-exclude]');
  const originalDisplays: string[] = [];
  excludedElements.forEach((el, index) => {
    originalDisplays[index] = (el as HTMLElement).style.display;
    (el as HTMLElement).style.display = 'none';
  });

  try {
    // Modify styles for clean export
    // Keep exact width, expand height, hide scrollbars
    scrollableArea.style.width = `${actualWidth}px`; // Lock to current width
    scrollableArea.style.height = 'auto'; // Expand to show all content
    scrollableArea.style.maxHeight = 'none';
    scrollableArea.style.overflow = 'hidden'; // Hide scrollbars
    
    dashboardContainer.style.height = 'auto';
    dashboardContainer.style.overflow = 'visible';

    // Wait for layout to settle
    await new Promise(resolve => setTimeout(resolve, 500));

    // Check if html2canvas is loaded
    if (!window.html2canvas) {
      throw new Error('html2canvas library is required. Add <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script> to index.html');
    }

    // Capture the screenshot
    const canvas = await window.html2canvas(dashboardContainer, {
      scale: 2, // 2x for high quality
      useCORS: true,
      allowTaint: false,
      backgroundColor: '#f9fafb', // Match your app background
      logging: false,
      windowWidth: actualWidth,
      scrollY: 0,
      scrollX: 0,
      width: actualWidth, // Use actual width, not expanded
    });

    // Convert to blob based on format
    let blob: Blob;
    
    if (format === 'png') {
      blob = await new Promise<Blob>((resolve, reject) => {
        canvas.toBlob((b) => {
          if (b) resolve(b);
          else reject(new Error('Failed to create PNG blob'));
        }, 'image/png', 1.0);
      });
    } else if (format === 'pdf') {
      // Check if jsPDF is loaded
      if (!window.jspdf || !window.jspdf.jsPDF) {
        throw new Error('jsPDF library is required');
      }
      
      // Convert canvas to PDF with proper sizing
      const imgData = canvas.toDataURL('image/png');
      const imgWidth = canvas.width;
      const imgHeight = canvas.height;
      
      // Calculate PDF dimensions (convert px to mm at 96 DPI)
      const pdfWidth = imgWidth * 0.264583; // px to mm
      const pdfHeight = imgHeight * 0.264583;
      
      const { jsPDF } = window.jspdf;
      const pdf = new jsPDF({
        orientation: imgWidth > imgHeight ? 'landscape' : 'portrait',
        unit: 'mm',
        format: [pdfWidth, pdfHeight],
      });
      
      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight, '', 'FAST');
      blob = pdf.output('blob');
    } else {
      throw new Error(`Unsupported format: ${format}`);
    }

    return blob;
  } finally {
    // Restore all original styles
    dashboardContainer.style.height = originalStyles.container.height;
    dashboardContainer.style.overflow = originalStyles.container.overflow;
    
    scrollableArea.style.height = originalStyles.scrollArea.height;
    scrollableArea.style.maxHeight = originalStyles.scrollArea.maxHeight;
    scrollableArea.style.overflow = originalStyles.scrollArea.overflow;
    scrollableArea.style.width = originalStyles.scrollArea.width;

    // Restore hidden elements
    excludedElements.forEach((el, index) => {
      (el as HTMLElement).style.display = originalDisplays[index];
    });
  }
};

/**
 * Download a blob as a file
 */
export const downloadBlob = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};
