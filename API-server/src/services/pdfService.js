import PDFDocument from 'pdfkit';

function renderTextWithFormatting(doc, text, options = {}) {
  const parts = text.split(/(\*\*.*?\*\*)/g);
  const align = options.align || 'left';
  const lineGap = options.lineGap || 3;
  const paragraphGap = options.paragraphGap || 0;
  
  for (let i = 0; i < parts.length; i++) {
    const part = parts[i];
    if (part === '') continue;
    
    const isBold = part.startsWith('**') && part.endsWith('**');
    const content = isBold ? part.slice(2, -2) : part;
    
    if (isBold) {
      doc.font('Helvetica-Bold');
    } else {
      doc.font('Helvetica');
    }
    
    const isLast = (i === parts.length - 1);
    doc.text(content, {
      continued: !isLast,
      align,
      lineGap,
      paragraphGap
    });
  }
}

export function renderResumePdfBuffer({ title = 'Tailored CV', resumeText = '' }) {
  return new Promise((resolve, reject) => {
    const doc = new PDFDocument({ margin: 50, size: 'A4' });
    const chunks = [];
    doc.on('data', chunk => chunks.push(chunk));
    doc.on('error', reject);
    doc.on('end', () => resolve(Buffer.concat(chunks)));

    const originalLeft = doc.page.margins.left;

    let contentText = resumeText || 'No resume content available.';
    const lines = contentText.split(/\r?\n/);
    
    let isFirstLine = true;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const trimmed = line.trim();

      // Check if header
      const headerMatch = line.match(/^(#{1,6})\s+(.*)$/);
      if (headerMatch) {
        const level = headerMatch[1].length;
        const text = headerMatch[2];

        // Avoid orphans: check space remaining
        if (doc.y > doc.page.height - 100) {
          doc.addPage();
          isFirstLine = true;
        }

        if (level === 1) {
          if (!isFirstLine) doc.moveDown(1);
          doc.fontSize(20).font('Helvetica-Bold').fillColor('#0f172a');
          doc.text(text, { align: 'center' });
          doc.moveDown(0.4);
          // Underline divider
          doc.strokeColor('#cbd5e1').lineWidth(1.5)
             .moveTo(doc.page.margins.left, doc.y)
             .lineTo(doc.page.width - doc.page.margins.right, doc.y)
             .stroke();
          doc.moveDown(0.6);
        } else if (level === 2) {
          if (!isFirstLine) doc.moveDown(0.8);
          doc.fontSize(13).font('Helvetica-Bold').fillColor('#1e3a8a');
          doc.text(text);
          doc.moveDown(0.3);
          // Thin accent line
          doc.strokeColor('#e2e8f0').lineWidth(1)
             .moveTo(doc.page.margins.left, doc.y)
             .lineTo(doc.page.width - doc.page.margins.right, doc.y)
             .stroke();
          doc.moveDown(0.4);
        } else {
          if (!isFirstLine) doc.moveDown(0.6);
          doc.fontSize(11).font('Helvetica-Bold').fillColor('#1e293b');
          doc.text(text);
          doc.moveDown(0.3);
        }
        
        isFirstLine = false;
        continue;
      }

      // Check if list item
      const listMatch = line.match(/^(\s*)([*+-]|\d+\.)\s+(.*)$/);
      if (listMatch) {
        const spaces = listMatch[1].length;
        const marker = listMatch[2];
        const text = listMatch[3];
        
        const depth = Math.floor(spaces / 2);
        const bulletIndent = 12 + depth * 15;
        const textIndent = bulletIndent + 10;
        
        const bulletX = originalLeft + bulletIndent;
        const textX = originalLeft + textIndent;

        // Choose bullet symbol
        const bulletSymbol = (marker === '*' || marker === '-' || marker === '+') 
          ? (depth % 2 === 0 ? '•' : '◦')
          : marker;

        // Check page overflow
        if (doc.y > doc.page.height - 40) {
          doc.addPage();
        }

        doc.fontSize(10).fillColor('#334155');
        
        // Print bullet
        doc.page.margins.left = textX;
        doc.x = bulletX;
        doc.font('Helvetica').text(bulletSymbol + ' ', { continued: true });
        
        // Print text
        renderTextWithFormatting(doc, text);
        doc.moveDown(0.3);
        
        // Restore margin
        doc.page.margins.left = originalLeft;
        isFirstLine = false;
        continue;
      }

      // Check empty line
      if (trimmed === '') {
        doc.moveDown(0.2);
        continue;
      }

      // Normal paragraph
      if (doc.y > doc.page.height - 40) {
        doc.addPage();
      }

      doc.fontSize(10).fillColor('#334155');
      renderTextWithFormatting(doc, trimmed);
      doc.moveDown(0.4);
      isFirstLine = false;
    }

    doc.end();
  });
}
