/* Genera EntregaFinal_Grupo1_RutasGAM.docx */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  ImageRun, PageBreak, ExternalHyperlink, Header, Footer, PageNumber,
} = require("docx");

const FIG = (name) => path.join(__dirname, "..", "figuras", name);
const AZUL = "1F4E79";
const GRIS = "595959";

const MARGIN = 1417; // ~2.5 cm

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 320, after: 160, line: 360 },
    children: [new TextRun({ text, bold: true, color: AZUL, size: 28 })],
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 120, line: 360 },
    children: [new TextRun({ text, bold: true, color: "222222", size: 25 })],
  });
}
function p(runsOrText, opts = {}) {
  const children = typeof runsOrText === "string"
    ? [new TextRun({ text: runsOrText, size: 24 })]
    : runsOrText;
  return new Paragraph({
    spacing: { after: 160, line: 360, lineRule: "auto" },
    alignment: opts.align || AlignmentType.JUSTIFIED,
    children,
  });
}
function b(text) { return new TextRun({ text, bold: true, size: 24 }); }
function i(text) { return new TextRun({ text, italics: true, size: 24 }); }
function t(text) { return new TextRun({ text, size: 24 }); }

function caption(text) {
  return new Paragraph({
    spacing: { after: 220, before: 60 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text, italics: true, size: 20, color: GRIS })],
  });
}

const DIMS = {
  "01_velocidades_por_fuente.png": [1334, 731],
  "02_red_paradas_importantes.png": [1382, 1006],
  "03_importancia_paradas.png": [1602, 1058],
  "04_rutas_astar.png": [2682, 802],
  "05_simulacion_tiempos.png": [2510, 833],
  "06_metricas_exito.png": [2320, 995],
  "07_validacion_extendida.png": [1184, 657],
  "08_sensibilidad_velocidades.png": [1184, 656],
};

function figure(name, widthPx, text) {
  const data = fs.readFileSync(FIG(name));
  const [dw, dh] = DIMS[name] || [1200, 700];
  const w = widthPx;
  const h = Math.round((dh / dw) * w);
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 120, after: 40 },
      children: [new ImageRun({ type: "png", data, transformation: { width: w, height: h } })],
    }),
    caption(text),
  ];
}

function cell(text, opts = {}) {
  return new TableCell({
    width: { size: opts.width || 2000, type: WidthType.DXA },
    shading: opts.header ? { type: ShadingType.CLEAR, fill: AZUL } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({
      alignment: opts.align || AlignmentType.LEFT,
      children: [new TextRun({
        text, size: opts.size || 19, bold: !!opts.header,
        color: opts.header ? "FFFFFF" : "000000",
      })],
    })],
  });
}

function table(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map((hd, idx) => cell(hd, { header: true, width: widths[idx], align: AlignmentType.CENTER })),
      }),
      ...rows.map((r) => new TableRow({
        children: r.map((val, idx) => cell(String(val), { width: widths[idx] })),
      })),
    ],
  });
}

// ---------------------------------------------------------------------------
// PORTADA
// ---------------------------------------------------------------------------
const portada = [
  new Paragraph({ spacing: { after: 900 }, children: [] }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 300 },
    children: [new ImageRun({
      type: "png",
      data: fs.readFileSync(path.join(__dirname, "lead_logo.png")),
      transformation: { width: 137, height: 78 },
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 },
    children: [new TextRun({ text: "BCD5105 · Modelado Matemático", size: 24, color: GRIS })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 100, before: 400 },
    children: [new TextRun({ text: "Entrega final del proyecto integrador", bold: true, size: 40, color: AZUL })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 500 },
    children: [new TextRun({
      text: "Optimización de rutas de transporte público en el GAM mediante teoría de grafos",
      bold: true, size: 30,
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 100 },
    children: [new TextRun({ text: "Carril temático #3 — Optimización de rutas de transporte público", italics: true, size: 24 })],
  }),
  new Paragraph({ spacing: { after: 600 }, children: [] }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 60 },
    children: [new TextRun({ text: "Integrantes (Grupo 1)", bold: true, size: 24 })],
  }),
  ...["Siloé Campos", "Jason Corrau", "Gabriel Corrales", "David Mora"].map((n) => new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 40 },
    children: [new TextRun({ text: n, size: 24 })],
  })),
  new Paragraph({ spacing: { after: 400 }, children: [] }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 40 },
    children: [new TextRun({ text: "Profesor: Jordy Alfaro Brenes", size: 24 })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 40 },
    children: [new TextRun({ text: "Lead University · II Cuatrimestre 2026", size: 24 })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 40 },
    children: [new TextRun({ text: "Miércoles 19 de agosto de 2026", size: 24 })],
  }),
  new Paragraph({ spacing: { after: 500 }, children: [] }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [
      new TextRun({ text: "Repositorio público: ", size: 22 }),
      new ExternalHyperlink({
        link: "https://github.com/GRUPO1-BCD5105/rutas-gam",
        children: [new TextRun({ text: "github.com/GRUPO1-BCD5105/rutas-gam", size: 22, color: "2563EB", underline: {} })],
      }),
    ],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 60 },
    children: [new TextRun({ text: "(Reemplazar por el enlace real antes de subir el PDF al campus virtual)", size: 18, italics: true, color: "C0392B" })],
  }),
  new Paragraph({ children: [new PageBreak()] }),
];

module.exports = { portada, h1, h2, p, b, i, t, caption, figure, cell, table, Document, Packer, TextRun, Paragraph, HeadingLevel, AlignmentType, PageBreak, Header, Footer, PageNumber, MARGIN, AZUL, GRIS };
