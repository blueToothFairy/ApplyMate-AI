import PDFDocument from 'pdfkit';

export function renderResumePdfBuffer({ title = 'Tailored CV', resumeText = '' }) {
  return new Promise((resolve, reject) => {
    const doc = new PDFDocument({ margin: 48, size: 'A4' });
    const chunks = [];
    doc.on('data', chunk => chunks.push(chunk));
    doc.on('error', reject);
    doc.on('end', () => resolve(Buffer.concat(chunks)));

    doc.fontSize(18).text(title, { underline: true });
    doc.moveDown();
    doc.fontSize(10).text(resumeText || 'No resume content available.', {
      align: 'left',
      lineGap: 3,
    });
    doc.end();
  });
}
