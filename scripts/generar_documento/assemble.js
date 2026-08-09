const fs = require("fs");
const path = require("path");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Footer, PageNumber } = require("docx");
const { portada, MARGIN } = require("./build_entrega_final.js");
const { body } = require("./build.js");

const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: "Times New Roman", size: 24 },
        paragraph: { spacing: { line: 360, lineRule: "auto" } },
      },
    },
  },
  sections: [
    {
      properties: {
        page: { margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN } },
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun({ text: "EntregaFinal_Grupo1_RutasGAM · ", size: 18, color: "888888" }),
              new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "888888" }),
            ],
          })],
        }),
      },
      children: [...portada, ...body],
    },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  const out = path.join(__dirname, "EntregaFinal_Grupo1_RutasGAM.docx");
  fs.writeFileSync(out, buffer);
  console.log("Escrito:", out, buffer.length, "bytes");
});
