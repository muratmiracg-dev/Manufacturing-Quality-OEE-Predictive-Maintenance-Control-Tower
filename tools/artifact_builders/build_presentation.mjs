import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const repoRoot = path.resolve(process.argv[2] ?? ".");
const outputPath = path.join(
  repoRoot,
  "deliverables/presentation/Manufacturing_Control_Tower_Executive_Deck.pptx",
);
const renderDirectory = path.join(repoRoot, "tmp/presentation-build");

const C = {
  ink: "#0B131A",
  ink2: "#13212B",
  steel: "#334155",
  gray: "#94A3B8",
  pale: "#E8EDF2",
  cream: "#F5F2EA",
  white: "#FFFFFF",
  orange: "#FF6B00",
  orangePale: "#FFF0E5",
  teal: "#00A6A6",
  green: "#2DBE8C",
  red: "#E63946",
  yellow: "#F6C453",
  blue: "#1D6F8A",
};

const sourceNotes = [];

async function readImageBlob(imagePath) {
  const bytes = await fs.readFile(imagePath);
  return bytes.buffer.slice(
    bytes.byteOffset,
    bytes.byteOffset + bytes.byteLength,
  );
}

function parseCsv(csvText) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let index = 0; index < csvText.length; index += 1) {
    const character = csvText[index];
    const nextCharacter = csvText[index + 1];
    if (character === '"' && quoted && nextCharacter === '"') {
      field += '"';
      index += 1;
    } else if (character === '"') {
      quoted = !quoted;
    } else if (character === "," && !quoted) {
      row.push(field);
      field = "";
    } else if (character === "\n" && !quoted) {
      row.push(field);
      rows.push(row);
      row = [];
      field = "";
    } else if (character !== "\r" || quoted) {
      field += character;
    }
  }
  if (field.length || row.length) {
    row.push(field);
    rows.push(row);
  }
  return rows;
}

function csvObjects(text) {
  const rows = parseCsv(text);
  const header = rows[0];
  return rows.slice(1).filter((row) => row.some(Boolean)).map((row) =>
    Object.fromEntries(header.map((column, index) => [column, row[index]])),
  );
}

function addShape(slide, geometry, position, fill, lineFill = "none") {
  return slide.shapes.add({
    geometry,
    position,
    fill,
    line: {
      style: "solid",
      fill: lineFill,
      width: lineFill === "none" ? 0 : 1,
    },
    ...(geometry === "roundRect"
      ? { borderRadius: "rounded-xl", shadow: "shadow-sm" }
      : {}),
  });
}

function addText(
  slide,
  text,
  position,
  {
    fontSize = 18,
    color = C.ink,
    bold = false,
    alignment = "left",
    verticalAlignment = "top",
    typeface = "Aptos",
    autoFit = "shrinkText",
    insets = { top: 0, right: 0, bottom: 0, left: 0 },
  } = {},
) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontSize,
    color,
    bold,
    alignment,
    verticalAlignment,
    typeface,
    autoFit,
    wrap: "square",
    insets,
  };
  return shape;
}

function addHeader(slide, eyebrow, title, page) {
  addShape(
    slide,
    "rect",
    { left: 0, top: 0, width: 1280, height: 12 },
    C.orange,
  );
  addText(
    slide,
    eyebrow.toUpperCase(),
    { left: 52, top: 27, width: 760, height: 22 },
    { fontSize: 12, color: C.teal, bold: true },
  );
  addText(
    slide,
    title,
    { left: 52, top: 51, width: 1130, height: 52 },
    { fontSize: 38, color: C.ink, bold: true, typeface: "Aptos Display" },
  );
  addText(
    slide,
    String(page).padStart(2, "0"),
    { left: 1191, top: 39, width: 40, height: 32 },
    { fontSize: 13, color: C.gray, bold: true, alignment: "right" },
  );
}

function addFooter(slide, text = "Deterministic synthetic data • Recommendation only") {
  addShape(
    slide,
    "rect",
    { left: 52, top: 683, width: 1176, height: 1 },
    C.pale,
  );
  addText(
    slide,
    text,
    { left: 52, top: 691, width: 1120, height: 18 },
    { fontSize: 10, color: C.gray },
  );
}

function addCard(
  slide,
  position,
  label,
  value,
  {
    accent = C.orange,
    fill = C.white,
    valueColor = C.ink,
    labelColor = C.steel,
    valueSize = 30,
    note = "",
  } = {},
) {
  addShape(slide, "roundRect", position, fill, C.pale);
  addShape(
    slide,
    "rect",
    { left: position.left, top: position.top, width: 8, height: position.height },
    accent,
  );
  addText(
    slide,
    label.toUpperCase(),
    {
      left: position.left + 20,
      top: position.top + 14,
      width: position.width - 32,
      height: 22,
    },
    { fontSize: 11, color: labelColor, bold: true },
  );
  addText(
    slide,
    value,
    {
      left: position.left + 20,
      top: position.top + 38,
      width: position.width - 32,
      height: note ? position.height - 72 : position.height - 52,
    },
    {
      fontSize: valueSize,
      color: valueColor,
      bold: true,
      verticalAlignment: "middle",
      typeface: "Aptos Display",
    },
  );
  if (note) {
    addText(
      slide,
      note,
      {
        left: position.left + 20,
        top: position.top + position.height - 29,
        width: position.width - 32,
        height: 17,
      },
      { fontSize: 10, color: C.gray },
    );
  }
}

async function addImagePanel(slide, imageBytes, position, alt, caption = "") {
  addShape(slide, "roundRect", position, C.white, C.pale);
  slide.images.add({
    blob: imageBytes,
    contentType: "image/png",
    alt,
    fit: "contain",
    position: {
      left: position.left + 12,
      top: position.top + 12,
      width: position.width - 24,
      height: position.height - (caption ? 45 : 24),
    },
  });
  if (caption) {
    addText(
      slide,
      caption,
      {
        left: position.left + 18,
        top: position.top + position.height - 28,
        width: position.width - 36,
        height: 18,
      },
      { fontSize: 10, color: C.gray, alignment: "center" },
    );
  }
}

function addCallout(slide, position, title, body, accent = C.teal) {
  addShape(slide, "roundRect", position, C.ink2, accent);
  addText(
    slide,
    title.toUpperCase(),
    {
      left: position.left + 18,
      top: position.top + 15,
      width: position.width - 36,
      height: 22,
    },
    { fontSize: 12, color: accent, bold: true },
  );
  addText(
    slide,
    body,
    {
      left: position.left + 18,
      top: position.top + 43,
      width: position.width - 36,
      height: position.height - 56,
    },
    { fontSize: 16, color: C.white, bold: false, verticalAlignment: "middle" },
  );
}

function addBulletList(slide, items, position, color = C.steel, size = 17) {
  addText(
    slide,
    items.map((item) => `• ${item}`).join("\n"),
    position,
    { fontSize: size, color, verticalAlignment: "top" },
  );
}

function addNotes(slide, page, sources, talkTrack = "") {
  const block = [
    talkTrack,
    "",
    "[Sources]",
    ...sources.map((source) => `- ${source}`),
  ].join("\n");
  slide.speakerNotes.textFrame.setText(block);
  slide.speakerNotes.setVisible(true);
  sourceNotes.push(`Slide ${page}\n${sources.map((source) => `- ${source}`).join("\n")}`);
}

function pct(value, digits = 2) {
  return `${(Number(value) * 100).toFixed(digits)}%`;
}

function number(value, digits = 0) {
  return Number(value).toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function addTableRow(
  slide,
  y,
  values,
  widths,
  {
    x = 52,
    height = 38,
    header = false,
    fills = [],
    textColors = [],
    fontSize = 14,
  } = {},
) {
  let left = x;
  values.forEach((value, index) => {
    const fill = fills[index] ?? (header ? C.ink : index % 2 ? C.white : C.cream);
    addShape(
      slide,
      "rect",
      { left, top: y, width: widths[index], height },
      fill,
      C.pale,
    );
    addText(
      slide,
      String(value),
      {
        left: left + 10,
        top: y + 7,
        width: widths[index] - 20,
        height: height - 12,
      },
      {
        fontSize,
        color: textColors[index] ?? (header ? C.white : C.ink),
        bold: header,
        verticalAlignment: "middle",
      },
    );
    left += widths[index];
  });
}

async function main() {
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.mkdir(renderDirectory, { recursive: true });

  const metrics = JSON.parse(
    await fs.readFile(
      path.join(repoRoot, "artifacts/results/pipeline_metrics.json"),
      "utf8",
    ),
  );
  const capability = csvObjects(
    await fs.readFile(
      path.join(repoRoot, "artifacts/results/process_capability.csv"),
      "utf8",
    ),
  );
  const localShap = csvObjects(
    await fs.readFile(
      path.join(repoRoot, "artifacts/results/shap_local_explanations.csv"),
      "utf8",
    ),
  ).slice(0, 4);

  const figureNames = [
    "oee_monthly_trend.png",
    "downtime_pareto.png",
    "process_capability.png",
    "spc_xbar.png",
    "model_calibration.png",
    "oot_confusion_matrix.png",
    "shap_global_importance.png",
    "maintenance_priority.png",
    "feature_drift.png",
  ];
  const images = Object.fromEntries(
    await Promise.all(
      figureNames.map(async (name) => [
        name,
        await readImageBlob(path.join(repoRoot, "artifacts/figures", name)),
      ]),
    ),
  );

  const presentation = Presentation.create({
    slideSize: { width: 1280, height: 720 },
  });
  const kpi = metrics.executive_kpis;
  const oot = metrics.model.oot_metrics;
  const validation = metrics.model.validation_metrics;

  // 1 — title
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.ink;
    addShape(
      slide,
      "rect",
      { left: 0, top: 0, width: 18, height: 720 },
      C.orange,
    );
    addText(
      slide,
      "MANUFACTURING",
      { left: 72, top: 64, width: 620, height: 34 },
      { fontSize: 15, color: C.teal, bold: true },
    );
    addText(
      slide,
      "Quality, OEE &\nPredictive Maintenance\nControl Tower",
      { left: 72, top: 125, width: 790, height: 245 },
      {
        fontSize: 56,
        color: C.white,
        bold: true,
        typeface: "Aptos Display",
      },
    );
    addText(
      slide,
      "A governed, recommendation-only decision system built on deterministic synthetic plant data.",
      { left: 76, top: 397, width: 700, height: 72 },
      { fontSize: 22, color: C.pale },
    );
    const labels = [
      ["OEE", C.orange],
      ["SPC", C.teal],
      ["SHAP", C.green],
      ["HUMAN GATE", C.yellow],
    ];
    labels.forEach(([label, color], index) => {
      addShape(
        slide,
        "roundRect",
        { left: 78 + index * 166, top: 505, width: 146, height: 48 },
        C.ink2,
        color,
      );
      addText(
        slide,
        label,
        { left: 78 + index * 166, top: 518, width: 146, height: 22 },
        {
          fontSize: 13,
          color,
          bold: true,
          alignment: "center",
        },
      );
    });
    addShape(
      slide,
      "roundRect",
      { left: 900, top: 110, width: 286, height: 430 },
      C.ink2,
      C.steel,
    );
    [
      ["4", "production lines", C.orange],
      ["12", "machines", C.teal],
      ["98,460", "CTQ measurements", C.green],
      ["24h", "failure horizon", C.yellow],
    ].forEach(([value, label, color], index) => {
      addText(
        slide,
        value,
        { left: 942, top: 148 + index * 94, width: 200, height: 44 },
        { fontSize: 34, color, bold: true, alignment: "center" },
      );
      addText(
        slide,
        label,
        { left: 938, top: 189 + index * 94, width: 208, height: 22 },
        { fontSize: 13, color: C.pale, alignment: "center" },
      );
    });
    addText(
      slide,
      "Executive deck • July 2026",
      { left: 76, top: 656, width: 360, height: 22 },
      { fontSize: 11, color: C.gray },
    );
    addNotes(
      slide,
      1,
      [
        "artifacts/results/pipeline_metrics.json",
        "src/manufacturing_ct/synthetic.py",
      ],
      "Open with the decision boundary: this is a portfolio-grade synthetic control tower, not an autonomous plant-control system.",
    );
  }

  // 2 — executive result
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.cream;
    addHeader(slide, "Executive result", "The plant clears the OEE target—model burden needs attention", 2);
    addText(
      slide,
      `${pct(kpi.oee)} OEE combines strong availability with a quality constraint; the model captures ${pct(oot.recall)} of 24-hour failures but sends more OOT alerts than the validation capacity cap.`,
      { left: 52, top: 115, width: 1160, height: 58 },
      { fontSize: 21, color: C.steel, bold: true },
    );
    const cards = [
      ["OEE", pct(kpi.oee), C.orange, "A × P × Q"],
      ["Quality / FPY", pct(kpi.fpy), C.green, "first-pass good"],
      ["Unplanned stop", `${number(kpi.unplanned_downtime_hours, 0)} h`, C.red, "synthetic period"],
      ["OOT PR-AUC", oot.pr_auc.toFixed(3), C.teal, `${(oot.pr_auc / oot.positive_rate).toFixed(2)}× baseline`],
      ["OOT recall", pct(oot.recall), C.blue, `${number(metrics.monitoring.alarm_quality.missed_failures)} misses`],
    ];
    cards.forEach(([label, value, accent, note], index) =>
      addCard(
        slide,
        { left: 52 + index * 237, top: 202, width: 217, height: 122 },
        label,
        value,
        { accent, note, valueSize: 29 },
      ),
    );
    addCallout(
      slide,
      { left: 52, top: 360, width: 365, height: 235 },
      "Operations",
      "Availability is 98.36%, yet 2,466 unplanned downtime hours remain. Electrical and minor stops dominate the Pareto.",
      C.orange,
    );
    addCallout(
      slide,
      { left: 457, top: 360, width: 365, height: 235 },
      "Quality",
      `FPY is ${pct(kpi.fpy)}. PRD-A has the lowest long-term Ppk (${Number(capability[0].ppk).toFixed(2)}), making it the first capability investigation.`,
      C.green,
    );
    addCallout(
      slide,
      { left: 862, top: 360, width: 365, height: 235 },
      "Model control",
      `OOT alert rate is ${pct(oot.alert_rate)}, above the 40% review-capacity design cap. Treat it as an operational watch item, not hidden model success.`,
      C.teal,
    );
    addFooter(slide);
    addNotes(slide, 2, [
      "artifacts/results/pipeline_metrics.json",
      "artifacts/results/process_capability.csv",
      "artifacts/results/downtime_pareto.csv",
    ]);
  }

  // 3 — synthetic plant
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.cream;
    addHeader(slide, "Data design", "A deterministic plant with enough structure to stress every layer", 3);
    addText(
      slide,
      "Four production lines • three machines per line • four products • three shifts",
      { left: 52, top: 112, width: 800, height: 26 },
      { fontSize: 18, color: C.steel, bold: true },
    );
    ["LINE-A", "LINE-B", "LINE-C", "LINE-D"].forEach((line, lineIndex) => {
      const y = 154 + lineIndex * 108;
      addShape(
        slide,
        "roundRect",
        { left: 52, top: y, width: 770, height: 84 },
        C.white,
        C.pale,
      );
      addShape(
        slide,
        "rect",
        { left: 52, top: y, width: 120, height: 84 },
        [C.orange, C.teal, C.green, C.blue][lineIndex],
      );
      addText(
        slide,
        line,
        { left: 66, top: y + 28, width: 90, height: 28 },
        { fontSize: 17, color: C.white, bold: true, alignment: "center" },
      );
      for (let machine = 0; machine < 3; machine += 1) {
        const machineNumber = lineIndex * 3 + machine + 1;
        addShape(
          slide,
          "roundRect",
          { left: 205 + machine * 175, top: y + 17, width: 145, height: 50 },
          C.pale,
          C.gray,
        );
        addText(
          slide,
          `MC-${String(machineNumber).padStart(2, "0")}`,
          { left: 205 + machine * 175, top: y + 31, width: 145, height: 22 },
          { fontSize: 15, color: C.ink, bold: true, alignment: "center" },
        );
      }
    });
    addCard(
      slide,
      { left: 866, top: 150, width: 360, height: 108 },
      "Production shifts",
      number(metrics.dataset.production_shift_rows),
      { accent: C.orange, note: "8-hour machine-shift grain" },
    );
    addCard(
      slide,
      { left: 866, top: 278, width: 360, height: 108 },
      "Quality measurements",
      number(metrics.dataset.quality_measurement_rows),
      { accent: C.green, note: "n=5 CTQ subgroups" },
    );
    addCard(
      slide,
      { left: 866, top: 406, width: 360, height: 108 },
      "Downtime events",
      number(metrics.dataset.downtime_event_rows),
      { accent: C.red, note: "planned / unplanned taxonomy" },
    );
    addCallout(
      slide,
      { left: 866, top: 534, width: 360, height: 102 },
      "Reproducibility",
      `Seed ${metrics.seed} • ${metrics.period.start} to ${metrics.period.end}`,
      C.teal,
    );
    addFooter(slide);
    addNotes(slide, 3, [
      "artifacts/results/pipeline_metrics.json",
      "artifacts/results/pipeline_config.json",
      "docs/data_contract.md",
    ]);
  }

  // 4 — architecture
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.cream;
    addHeader(slide, "Architecture", "One governed feature set, five decision layers", 4);
    const nodes = [
      ["SYNTHETIC\nGENERATOR", "plant events + sensors", C.orange],
      ["KPI + SPC", "OEE, quality, reliability", C.green],
      ["TEMPORAL ML", "calibration + threshold", C.teal],
      ["SHAP + POLICY", "reason codes + economics", C.blue],
      ["FASTAPI", "recommendation only", C.red],
    ];
    nodes.forEach(([title, body, accent], index) => {
      const x = 44 + index * 247;
      addShape(
        slide,
        "roundRect",
        { left: x, top: 154, width: 205, height: 132 },
        C.white,
        accent,
      );
      addShape(
        slide,
        "rect",
        { left: x, top: 154, width: 205, height: 8 },
        accent,
      );
      addText(
        slide,
        title,
        { left: x + 18, top: 181, width: 169, height: 48 },
        { fontSize: 17, color: C.ink, bold: true, alignment: "center" },
      );
      addText(
        slide,
        body,
        { left: x + 14, top: 241, width: 177, height: 27 },
        { fontSize: 11, color: C.gray, alignment: "center" },
      );
      if (index < nodes.length - 1) {
        addText(
          slide,
          "→",
          { left: x + 207, top: 199, width: 40, height: 38 },
          { fontSize: 30, color: C.gray, bold: true, alignment: "center" },
        );
      }
    });
    addText(
      slide,
      "DATA PLANE",
      { left: 52, top: 344, width: 150, height: 22 },
      { fontSize: 12, color: C.teal, bold: true },
    );
    [
      ["PostgreSQL", "normalized schema + analytical views"],
      ["PBIP + Excel", "decision-ready semantic and formula layers"],
      ["Artifacts", "metrics, figures, model bundle, reports"],
    ].forEach(([title, body], index) => {
      const x = 52 + index * 395;
      addCallout(
        slide,
        { left: x, top: 378, width: 360, height: 100 },
        title,
        body,
        [C.teal, C.orange, C.green][index],
      );
    });
    addText(
      slide,
      "OPERATIONS PLANE",
      { left: 52, top: 525, width: 180, height: 22 },
      { fontSize: 12, color: C.orange, bold: true },
    );
    addBulletList(
      slide,
      [
        "Docker Compose and Kubernetes deployment profiles",
        "Prometheus metrics, alert rules and Grafana dashboard provisioning",
        "CI, CodeQL, dependency audit, container scan and ownership controls",
      ],
      { left: 52, top: 557, width: 1120, height: 88 },
      C.steel,
      17,
    );
    addFooter(slide);
    addNotes(slide, 4, [
      "docs/architecture.md",
      "docs/adr/001-recommendation-only-boundary.md",
      "sql/schema.sql",
      "src/manufacturing_ct/api.py",
      "docker-compose.yml",
      "k8s/",
      "monitoring/",
    ]);
  }

  // 5 — OEE
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.cream;
    addHeader(slide, "OEE", "Stable line trends, with performance as the main OEE limiter", 5);
    await addImagePanel(
      slide,
      images["oee_monthly_trend.png"],
      { left: 48, top: 133, width: 820, height: 405 },
      "Monthly OEE trend by production line",
      "Monthly OEE by line • computed from planned time, runtime and first-pass good units",
    );
    [
      ["Availability", pct(kpi.availability), C.teal],
      ["Performance", pct(kpi.performance), C.orange],
      ["Quality", pct(kpi.quality_rate), C.green],
    ].forEach(([label, value, accent], index) =>
      addCard(
        slide,
        { left: 898, top: 141 + index * 126, width: 330, height: 104 },
        label,
        value,
        { accent, valueSize: 32 },
      ),
    );
    addCallout(
      slide,
      { left: 48, top: 565, width: 370, height: 86 },
      "Definition",
      "OEE = Availability × Performance × Quality",
      C.orange,
    );
    addCallout(
      slide,
      { left: 438, top: 565, width: 390, height: 86 },
      "Interpretation",
      "Performance has the largest mathematical gap to 100%.",
      C.teal,
    );
    addCallout(
      slide,
      { left: 848, top: 565, width: 380, height: 86 },
      "Boundary",
      "OEE is descriptive; it does not authorize production actions.",
      C.green,
    );
    addFooter(slide);
    addNotes(slide, 5, [
      "artifacts/results/pipeline_metrics.json",
      "artifacts/results/oee_monthly_line.csv",
      "artifacts/figures/oee_monthly_trend.png",
      "docs/reference_crosswalk.md",
    ]);
  }

  // 6 — downtime/reliability
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.cream;
    addHeader(slide, "Downtime & reliability", "Electrical events and minor stops explain 70.53% of downtime", 6);
    await addImagePanel(
      slide,
      images["downtime_pareto.png"],
      { left: 48, top: 134, width: 790, height: 410 },
      "Downtime Pareto chart",
      "Duration bars and cumulative-share line",
    );
    addCard(
      slide,
      { left: 870, top: 142, width: 358, height: 108 },
      "MTBF",
      `${number(kpi.mtbf_hours, 2)} h`,
      { accent: C.teal, note: "operating hours / failures" },
    );
    addCard(
      slide,
      { left: 870, top: 270, width: 358, height: 108 },
      "MTTR",
      `${number(kpi.mttr_hours, 2)} h`,
      { accent: C.orange, note: "repair hours / failures" },
    );
    addCard(
      slide,
      { left: 870, top: 398, width: 358, height: 108 },
      "Failure events",
      number(kpi.failure_count),
      { accent: C.red, note: "across 12 machines" },
    );
    addCallout(
      slide,
      { left: 48, top: 570, width: 555, height: 82 },
      "Pareto priority",
      "Start with electrical root causes and recurring minor stops.",
      C.orange,
    );
    addCallout(
      slide,
      { left: 623, top: 570, width: 605, height: 82 },
      "Reliability boundary",
      "Metrics describe the synthetic history; maintenance still requires planner approval.",
      C.teal,
    );
    addFooter(slide);
    addNotes(slide, 6, [
      "artifacts/results/downtime_pareto.csv",
      "artifacts/results/reliability_metrics.csv",
      "artifacts/results/pipeline_metrics.json",
      "artifacts/figures/downtime_pareto.png",
    ]);
  }

  // 7 — quality/capability
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.cream;
    addHeader(slide, "Quality & capability", "PRD-A is the long-term capability watch item", 7);
    await addImagePanel(
      slide,
      images["process_capability.png"],
      { left: 48, top: 136, width: 690, height: 355 },
      "Capability comparison by product",
      "Cp/Cpk use within variation; Pp/Ppk use overall variation",
    );
    addTableRow(slide, 145, ["Product", "Cpk", "Ppk"], [180, 125, 125], {
      x: 775,
      header: true,
      height: 42,
    });
    capability.forEach((row, index) => {
      addTableRow(
        slide,
        187 + index * 54,
        [row.product_id, Number(row.cpk).toFixed(2), Number(row.ppk).toFixed(2)],
        [180, 125, 125],
        {
          x: 775,
          height: 54,
          fills:
            row.product_id === "PRD-A"
              ? [C.orangePale, C.orangePale, C.orangePale]
              : [C.white, C.white, C.white],
          textColors:
            row.product_id === "PRD-A"
              ? [C.red, C.red, C.red]
              : [C.ink, C.ink, C.ink],
        },
      );
    });
    const qualityCards = [
      ["FPY", pct(kpi.fpy), C.green],
      ["Scrap", pct(kpi.scrap_rate), C.red],
      ["Rework", pct(kpi.rework_rate), C.orange],
      ["COPQ", number(kpi.copq, 0), C.teal],
    ];
    qualityCards.forEach(([label, value, accent], index) =>
      addCard(
        slide,
        { left: 48 + index * 297, top: 530, width: 272, height: 112 },
        label,
        value,
        { accent, valueSize: index === 3 ? 27 : 31 },
      ),
    );
    addFooter(slide);
    addNotes(slide, 7, [
      "artifacts/results/process_capability.csv",
      "artifacts/results/pipeline_metrics.json",
      "artifacts/figures/process_capability.png",
      "https://www.itl.nist.gov/div898/handbook/pmc/section1/pmc16.htm",
    ]);
  }

  // 8 — SPC
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.cream;
    addHeader(slide, "Statistical process control", "Chart selection follows data type—not convenience", 8);
    await addImagePanel(
      slide,
      images["spc_xbar.png"],
      { left: 48, top: 135, width: 760, height: 378 },
      "X-bar chart with documented alarm signals",
      "Fixed n=5 CTQ subgroup means • control limits estimated from baseline behavior",
    );
    const selections = [
      ["X-bar/R", "CTQ dimension", "fixed n=5"],
      ["I-MR", "roughness", "one observation"],
      ["p", "defective proportion", "variable lot"],
      ["u", "defects / unit", "variable units"],
    ];
    addTableRow(slide, 145, ["Chart", "Signal", "Sample"], [122, 176, 154], {
      x: 824,
      header: true,
      height: 40,
      fontSize: 13,
    });
    selections.forEach((row, index) =>
      addTableRow(slide, 185 + index * 59, row, [122, 176, 154], {
        x: 824,
        height: 59,
        fontSize: 13,
      }),
    );
    addCallout(
      slide,
      { left: 48, top: 546, width: 575, height: 105 },
      "Do not conflate",
      "Control limits estimate process behavior. LSL/USL are engineering requirements used for capability.",
      C.red,
    );
    addCallout(
      slide,
      { left: 650, top: 546, width: 578, height: 105 },
      "Alarm rules",
      "Beyond 3σ • 2 of 3 beyond 2σ • 4 of 5 beyond 1σ • 8 points on one side.",
      C.teal,
    );
    addFooter(slide);
    addNotes(slide, 8, [
      "artifacts/results/spc_metadata.json",
      "artifacts/results/spc_xbar_r.csv",
      "artifacts/figures/spc_xbar.png",
      "docs/spc_methodology.md",
      "https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc3.htm",
    ]);
  }

  // 9 — temporal model design
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.cream;
    addHeader(slide, "Model development", "Every model decision is made before the out-of-time window", 9);
    const parts = [
      ["MODEL FIT", "Jan–Sep 2024", "9,828 rows", C.blue],
      ["CALIBRATION", "Oct–Nov 2024", "2,160 rows", C.teal],
      ["VALIDATION", "Dec 2024–Feb 2025", "3,204 rows", C.orange],
      ["OUT-OF-TIME", "Mar–Jun 2025", "4,356 rows", C.red],
    ];
    parts.forEach(([label, dates, rows, accent], index) => {
      const x = 52 + index * 296;
      addShape(
        slide,
        "roundRect",
        { left: x, top: 165, width: 264, height: 145 },
        C.white,
        accent,
      );
      addShape(
        slide,
        "rect",
        { left: x, top: 165, width: 264, height: 10 },
        accent,
      );
      addText(
        slide,
        label,
        { left: x + 18, top: 193, width: 228, height: 26 },
        { fontSize: 16, color: accent, bold: true, alignment: "center" },
      );
      addText(
        slide,
        dates,
        { left: x + 18, top: 231, width: 228, height: 27 },
        { fontSize: 14, color: C.ink, bold: true, alignment: "center" },
      );
      addText(
        slide,
        rows,
        { left: x + 18, top: 270, width: 228, height: 20 },
        { fontSize: 12, color: C.gray, alignment: "center" },
      );
    });
    addText(
      slide,
      "DECISION GATES",
      { left: 52, top: 357, width: 240, height: 22 },
      { fontSize: 12, color: C.teal, bold: true },
    );
    addCallout(
      slide,
      { left: 52, top: 392, width: 360, height: 172 },
      "Leakage control",
      "Lagged and rolling features use past-only values. Labels look forward 24 hours; split boundaries are chronological.",
      C.teal,
    );
    addCallout(
      slide,
      { left: 460, top: 392, width: 360, height: 172 },
      "Calibration",
      "Sigmoid calibration is fitted on a dedicated window. OOT calibration is evaluated, never tuned.",
      C.orange,
    );
    addCallout(
      slide,
      { left: 868, top: 392, width: 360, height: 172 },
      "Threshold",
      `Validation selects ${metrics.model.threshold.threshold.toFixed(4)} under recall and review-capacity constraints. OOT stays untouched.`,
      C.red,
    );
    addBulletList(
      slide,
      [
        "Champion: random forest",
        "Challenger retained: logistic regression",
        "Class imbalance measured against the positive-rate PR baseline",
      ],
      { left: 52, top: 598, width: 1140, height: 58 },
      C.steel,
      15,
    );
    addFooter(slide);
    addNotes(slide, 9, [
      "artifacts/results/pipeline_metrics.json",
      "src/manufacturing_ct/modeling.py",
      "docs/governance/validation_report.md",
      "docs/adr/003-temporal-validation.md",
    ]);
  }

  // 10 — models
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.cream;
    addHeader(slide, "Champion / challenger", "Random forest wins narrowly; logistic regression remains the fallback", 10);
    const rf = metrics.model.candidate_summary.random_forest;
    const lr = metrics.model.candidate_summary.logistic_regression;
    addTableRow(
      slide,
      148,
      ["Candidate", "Val PR-AUC", "Val ROC-AUC", "Val Brier", "Selection score", "Status"],
      [240, 170, 170, 160, 190, 190],
      { x: 52, header: true, height: 46, fontSize: 13 },
    );
    addTableRow(
      slide,
      194,
      [
        "Random forest",
        rf.validation_at_0_5.pr_auc.toFixed(4),
        rf.validation_at_0_5.roc_auc.toFixed(4),
        rf.validation_at_0_5.brier_score.toFixed(4),
        rf.selection_score.toFixed(4),
        "CHAMPION",
      ],
      [240, 170, 170, 160, 190, 190],
      {
        x: 52,
        height: 58,
        fills: [C.orangePale, C.orangePale, C.orangePale, C.orangePale, C.orangePale, C.orange],
        textColors: [C.ink, C.ink, C.ink, C.ink, C.ink, C.white],
      },
    );
    addTableRow(
      slide,
      252,
      [
        "Logistic regression",
        lr.validation_at_0_5.pr_auc.toFixed(4),
        lr.validation_at_0_5.roc_auc.toFixed(4),
        lr.validation_at_0_5.brier_score.toFixed(4),
        lr.selection_score.toFixed(4),
        "CHALLENGER",
      ],
      [240, 170, 170, 160, 190, 190],
      {
        x: 52,
        height: 58,
        fills: [C.white, C.white, C.white, C.white, C.white, C.teal],
        textColors: [C.ink, C.ink, C.ink, C.ink, C.ink, C.white],
      },
    );
    addText(
      slide,
      "OOT CHAMPION PERFORMANCE",
      { left: 52, top: 364, width: 420, height: 24 },
      { fontSize: 12, color: C.teal, bold: true },
    );
    [
      ["PR-AUC", oot.pr_auc.toFixed(4), C.teal, `${(oot.pr_auc / oot.positive_rate).toFixed(2)}× positive rate`],
      ["ROC-AUC", oot.roc_auc.toFixed(4), C.blue, "rank discrimination"],
      ["Brier", oot.brier_score.toFixed(4), C.orange, "probability accuracy"],
      ["ECE", oot.ece_10_bin.toFixed(4), C.green, "10-bin calibration gap"],
    ].forEach(([label, value, accent, note], index) =>
      addCard(
        slide,
        { left: 52 + index * 296, top: 404, width: 272, height: 116 },
        label,
        value,
        { accent, note, valueSize: 29 },
      ),
    );
    addCallout(
      slide,
      { left: 52, top: 562, width: 567, height: 92 },
      "Validation threshold",
      `${metrics.model.threshold.threshold.toFixed(4)} • recall ${pct(validation.recall)} • alert rate ${pct(validation.alert_rate)}`,
      C.orange,
    );
    addCallout(
      slide,
      { left: 645, top: 562, width: 583, height: 92 },
      "OOT reality",
      `precision ${pct(oot.precision)} • recall ${pct(oot.recall)} • alert rate ${pct(oot.alert_rate)}`,
      C.red,
    );
    addFooter(slide);
    addNotes(slide, 10, [
      "artifacts/results/pipeline_metrics.json",
      "artifacts/results/oot_predictions.csv",
      "docs/governance/model_card.md",
      "docs/governance/validation_report.md",
    ]);
  }

  // 11 — calibration/confusion
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.cream;
    addHeader(slide, "Calibration & alarm quality", "Probability quality is acceptable; alert workload is the operational issue", 11);
    await addImagePanel(
      slide,
      images["model_calibration.png"],
      { left: 48, top: 137, width: 560, height: 403 },
      "Validation and OOT calibration curves",
      `OOT Brier ${oot.brier_score.toFixed(4)} • ECE ${oot.ece_10_bin.toFixed(4)}`,
    );
    await addImagePanel(
      slide,
      images["oot_confusion_matrix.png"],
      { left: 632, top: 137, width: 596, height: 403 },
      "Out-of-time confusion matrix",
      `TN ${oot.true_negative} • FP ${oot.false_positive} • FN ${oot.false_negative} • TP ${oot.true_positive}`,
    );
    [
      ["Alerts / day", number(metrics.monitoring.alarm_quality.alerts_per_day, 2), C.orange],
      ["Median lead", `${number(metrics.monitoring.alarm_quality.median_lead_time_hours)} h`, C.teal],
      ["Precision", pct(oot.precision), C.blue],
      ["Recall", pct(oot.recall), C.green],
    ].forEach(([label, value, accent], index) =>
      addCard(
        slide,
        { left: 48 + index * 297, top: 566, width: 272, height: 90 },
        label,
        value,
        { accent, valueSize: 25 },
      ),
    );
    addFooter(slide);
    addNotes(slide, 11, [
      "artifacts/results/calibration_curve.csv",
      "artifacts/results/oot_predictions.csv",
      "artifacts/figures/model_calibration.png",
      "artifacts/figures/oot_confusion_matrix.png",
      "artifacts/results/pipeline_metrics.json",
    ]);
  }

  // 12 — SHAP
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.cream;
    addHeader(slide, "Explainability", "Global drivers become local maintenance reason codes", 12);
    await addImagePanel(
      slide,
      images["shap_global_importance.png"],
      { left: 48, top: 137, width: 700, height: 430 },
      "SHAP global importance",
      "Mean absolute SHAP across 700 explained rows",
    );
    addCallout(
      slide,
      { left: 780, top: 137, width: 448, height: 92 },
      "Local example",
      `Risk ${pct(localShap[0].failure_probability)} • ${localShap[0].shift_id}`,
      C.orange,
    );
    localShap.forEach((row, index) => {
      addShape(
        slide,
        "roundRect",
        { left: 780, top: 248 + index * 67, width: 448, height: 54 },
        C.white,
        C.pale,
      );
      addText(
        slide,
        `${index + 1}`,
        { left: 792, top: 262 + index * 67, width: 30, height: 22 },
        { fontSize: 15, color: C.orange, bold: true, alignment: "center" },
      );
      addText(
        slide,
        row.reason_code,
        { left: 834, top: 257 + index * 67, width: 275, height: 25 },
        { fontSize: 14, color: C.ink, bold: true },
      );
      addText(
        slide,
        `SHAP ${Number(row.shap_value).toFixed(3)}`,
        { left: 1110, top: 257 + index * 67, width: 98, height: 25 },
        { fontSize: 12, color: C.teal, bold: true, alignment: "right" },
      );
    });
    addCallout(
      slide,
      { left: 48, top: 580, width: 1180, height: 78 },
      "Scope note",
      "SHAP explains the fitted base estimator. The sigmoid calibration layer changes probabilities and is outside attribution.",
      C.red,
    );
    addFooter(slide);
    addNotes(slide, 12, [
      "artifacts/results/shap_global_importance.csv",
      "artifacts/results/shap_local_explanations.csv",
      "artifacts/figures/shap_global_importance.png",
      "artifacts/results/pipeline_metrics.json",
      "src/manufacturing_ct/explain.py",
    ]);
  }

  // 13 — maintenance policy
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.cream;
    addHeader(slide, "Maintenance decision support", "Risk is prioritized only when economics and criticality agree", 13);
    await addImagePanel(
      slide,
      images["maintenance_priority.png"],
      { left: 48, top: 137, width: 760, height: 420 },
      "Latest OOT maintenance priority",
      "Expected net benefit = avoided synthetic loss − maintenance cost",
    );
    addCallout(
      slide,
      { left: 840, top: 137, width: 388, height: 155 },
      "Policy inputs",
      "Calibrated probability\n× asset criticality\n× estimated failure cost\n− maintenance cost",
      C.orange,
    );
    addCard(
      slide,
      { left: 840, top: 315, width: 184, height: 112 },
      "P1",
      String(metrics.decision_support.recommendation_counts.P1),
      { accent: C.red, note: "planner review" },
    );
    addCard(
      slide,
      { left: 1044, top: 315, width: 184, height: 112 },
      "Monitor",
      String(metrics.decision_support.recommendation_counts.MONITOR),
      { accent: C.teal, note: "no action" },
    );
    addCallout(
      slide,
      { left: 840, top: 452, width: 388, height: 105 },
      "Human gate",
      "Every recommendation requires maintenance-planner approval and current safety context.",
      C.red,
    );
    addCallout(
      slide,
      { left: 48, top: 575, width: 1180, height: 79 },
      "Explicit exclusion",
      "No CMMS, PLC or SCADA write path; the API cannot stop equipment, create work orders or approve maintenance.",
      C.yellow,
    );
    addFooter(slide);
    addNotes(slide, 13, [
      "artifacts/results/maintenance_priority.csv",
      "artifacts/results/policy_config.json",
      "artifacts/figures/maintenance_priority.png",
      "src/manufacturing_ct/policy.py",
      "docs/adr/001-recommendation-only-boundary.md",
    ]);
  }

  // 14 — delivery architecture
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.cream;
    addHeader(slide, "Delivery architecture", "The same governed record serves API, BI, reporting and operations", 14);
    addCallout(
      slide,
      { left: 457, top: 139, width: 366, height: 92 },
      "Governed analytical record",
      "PostgreSQL views + versioned artifacts + model bundle",
      C.orange,
    );
    const endpoints = [
      ["FASTAPI", "recommendation endpoint", 52, 284, C.red],
      ["PBIP", "semantic starter + DAX", 346, 284, C.teal],
      ["EXCEL", "formula decision workbook", 640, 284, C.green],
      ["PDF / PPT", "governance + executive", 934, 284, C.blue],
    ];
    endpoints.forEach(([title, body, x, y, accent]) => {
      addText(
        slide,
        "↓",
        { left: x + 102, top: 236, width: 40, height: 35 },
        { fontSize: 28, color: C.gray, bold: true, alignment: "center" },
      );
      addCallout(
        slide,
        { left: x, top: y, width: 244, height: 116 },
        title,
        body,
        accent,
      );
    });
    addText(
      slide,
      "OPERABILITY",
      { left: 52, top: 450, width: 220, height: 22 },
      { fontSize: 12, color: C.teal, bold: true },
    );
    [
      ["Docker Compose", "local integrated stack"],
      ["Kubernetes", "non-root API + HPA/PDB"],
      ["Prometheus", "service/model metrics"],
      ["Grafana", "provisioned dashboard"],
    ].forEach(([title, body], index) => {
      addShape(
        slide,
        "roundRect",
        { left: 52 + index * 296, top: 490, width: 270, height: 92 },
        C.white,
        C.pale,
      );
      addText(
        slide,
        title,
        { left: 69 + index * 296, top: 509, width: 236, height: 24 },
        { fontSize: 16, color: C.ink, bold: true, alignment: "center" },
      );
      addText(
        slide,
        body,
        { left: 69 + index * 296, top: 542, width: 236, height: 21 },
        { fontSize: 12, color: C.gray, alignment: "center" },
      );
    });
    addCallout(
      slide,
      { left: 52, top: 588, width: 1176, height: 76 },
      "Security controls",
      "CI • CodeQL • pip-audit • Trivy • Dependabot • CODEOWNERS • documented branch protection",
      C.orange,
    );
    addFooter(slide);
    addNotes(slide, 14, [
      "src/manufacturing_ct/api.py",
      "sql/schema.sql",
      "powerbi/ManufacturingControlTower.pbip",
      "deliverables/excel/Manufacturing_Control_Tower.xlsx",
      "docker-compose.yml",
      "k8s/",
      "monitoring/",
      ".github/workflows/",
    ]);
  }

  // 15 — monitoring
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.cream;
    addHeader(slide, "Monitoring", "Data quality passes; temporal drift is intentionally visible", 15);
    await addImagePanel(
      slide,
      images["feature_drift.png"],
      { left: 48, top: 137, width: 720, height: 430 },
      "Feature population stability index",
      "OOT versus model-fit reference distribution",
    );
    addCard(
      slide,
      { left: 800, top: 137, width: 205, height: 112 },
      "Data checks",
      `${metrics.monitoring.data_quality_checks_passed}/${metrics.monitoring.data_quality_checks_total}`,
      { accent: C.green, note: "pipeline gates" },
    );
    addCard(
      slide,
      { left: 1023, top: 137, width: 205, height: 112 },
      "Action PSI",
      String(metrics.monitoring.features_at_action_level),
      { accent: C.red, note: "review features" },
    );
    addCard(
      slide,
      { left: 800, top: 274, width: 428, height: 112 },
      "OOT alert rate",
      pct(oot.alert_rate),
      { accent: C.orange, note: "above 40% validation capacity cap" },
    );
    addCallout(
      slide,
      { left: 800, top: 414, width: 428, height: 153 },
      "Operational watch",
      "Large PSI values are expected from cumulative/time features across a later time window. Review meaning and redesign before promotion; do not silence the alert.",
      C.red,
    );
    addCallout(
      slide,
      { left: 48, top: 582, width: 1180, height: 76 },
      "Monitoring contract",
      "Model quality, feature drift, data quality and alert burden have separate thresholds and owners.",
      C.teal,
    );
    addFooter(slide);
    addNotes(slide, 15, [
      "artifacts/results/data_drift.csv",
      "artifacts/results/data_quality_checks.csv",
      "artifacts/results/pipeline_metrics.json",
      "artifacts/figures/feature_drift.png",
      "docs/monitoring_runbook.md",
      "monitoring/prometheus/rules.yml",
    ]);
  }

  // 16 — operating pilot
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.cream;
    addHeader(slide, "Governed adoption", "A proposed 90-day pilot keeps humans in the decision loop", 16);
    const phases = [
      ["0–30", "SHADOW MODE", "Score silently; validate data freshness, SPC false signals and planner interpretability.", C.teal],
      ["31–60", "ASSISTED REVIEW", "Expose ranked recommendations; record accept/reject decisions and reason codes.", C.orange],
      ["61–90", "CONTROL REVIEW", "Reassess threshold, workload, drift and synthetic economics before any promotion.", C.red],
    ];
    phases.forEach(([days, title, body, accent], index) => {
      const x = 52 + index * 395;
      addShape(
        slide,
        "roundRect",
        { left: x, top: 165, width: 360, height: 256 },
        C.white,
        accent,
      );
      addShape(
        slide,
        "ellipse",
        { left: x + 123, top: 188, width: 114, height: 114 },
        accent,
      );
      addText(
        slide,
        days,
        { left: x + 123, top: 222, width: 114, height: 42 },
        { fontSize: 27, color: C.white, bold: true, alignment: "center" },
      );
      addText(
        slide,
        title,
        { left: x + 28, top: 326, width: 304, height: 26 },
        { fontSize: 16, color: accent, bold: true, alignment: "center" },
      );
      addText(
        slide,
        body,
        { left: x + 28, top: 363, width: 304, height: 45 },
        { fontSize: 14, color: C.steel, alignment: "center" },
      );
    });
    addText(
      slide,
      "GO / NO-GO CRITERIA",
      { left: 52, top: 468, width: 260, height: 22 },
      { fontSize: 12, color: C.teal, bold: true },
    );
    [
      "Data-quality gates pass",
      "Alert workload fits planner capacity",
      "Failure capture and calibration remain acceptable",
      "Drift reviewed with documented disposition",
      "Safety and maintenance owners approve",
    ].forEach((item, index) => {
      addShape(
        slide,
        "roundRect",
        { left: 52 + index * 237, top: 511, width: 213, height: 78 },
        index === 4 ? C.orangePale : C.white,
        index === 4 ? C.orange : C.pale,
      );
      addText(
        slide,
        item,
        { left: 68 + index * 237, top: 530, width: 181, height: 42 },
        {
          fontSize: 13,
          color: index === 4 ? C.red : C.ink,
          bold: index === 4,
          alignment: "center",
          verticalAlignment: "middle",
        },
      );
    });
    addShape(
      slide,
      "roundRect",
      { left: 52, top: 604, width: 1176, height: 56 },
      C.ink2,
      C.red,
    );
    addText(
      slide,
      "BOUNDARY",
      { left: 70, top: 622, width: 120, height: 20 },
      { fontSize: 12, color: C.red, bold: true },
    );
    addText(
      slide,
      "This is a proposed pilot cadence, not evidence of real deployment or standard compliance.",
      { left: 200, top: 619, width: 1004, height: 25 },
      { fontSize: 15, color: C.white, verticalAlignment: "middle" },
    );
    addFooter(slide);
    addNotes(slide, 16, [
      "docs/monitoring_runbook.md",
      "docs/governance/incident_response.md",
      "docs/governance/risk_register.md",
      "docs/governance/threat_model.md",
      "docs/reference_crosswalk.md",
    ]);
  }

  // 17 — delivery matrix
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.cream;
    addHeader(slide, "Portfolio delivery layer", "Every reviewer can inspect outcomes and the evidence underneath", 17);
    const deliveries = [
      ["PYTHON + SQL", "Pipeline, tests, API, schema and analytical views", "REPRODUCE", C.blue],
      ["POWER BI PBIP", "Starter semantic model, DAX measures and report pages", "EXPLORE", C.teal],
      ["EXCEL", "Formula-based dashboard, model controls and planner", "SCENARIO", C.green],
      ["PPT + PDF", "Executive narrative and detailed governance evidence", "COMMUNICATE", C.orange],
      ["GITHUB", "CI, security scans, ownership and branch controls", "ASSURE", C.red],
      ["DOCUMENTATION", "Data contract, ADRs, model card and runbooks", "GOVERN", C.yellow],
    ];
    deliveries.forEach(([title, body, verb, accent], index) => {
      const col = index % 3;
      const row = Math.floor(index / 3);
      const x = 52 + col * 395;
      const y = 148 + row * 235;
      addShape(
        slide,
        "roundRect",
        { left: x, top: y, width: 360, height: 200 },
        C.white,
        accent,
      );
      addText(
        slide,
        verb,
        { left: x + 25, top: y + 22, width: 310, height: 22 },
        { fontSize: 11, color: accent, bold: true },
      );
      addText(
        slide,
        title,
        { left: x + 25, top: y + 57, width: 310, height: 36 },
        { fontSize: 23, color: C.ink, bold: true },
      );
      addText(
        slide,
        body,
        { left: x + 25, top: y + 112, width: 310, height: 60 },
        { fontSize: 15, color: C.steel, verticalAlignment: "middle" },
      );
    });
    addFooter(slide, "One deterministic evidence chain across code, analytics and communication");
    addNotes(slide, 17, [
      "README.md",
      "README_TR.md",
      "powerbi/",
      "deliverables/excel/Manufacturing_Control_Tower.xlsx",
      "deliverables/report/Manufacturing_Control_Tower_Governance_Report.pdf",
      ".github/",
      "docs/",
    ]);
  }

  // 18 — close
  {
    const slide = presentation.slides.add();
    slide.background.fill = C.ink;
    addShape(
      slide,
      "rect",
      { left: 0, top: 0, width: 1280, height: 14 },
      C.orange,
    );
    addText(
      slide,
      "MANUFACTURING DECISION SUPPORT",
      { left: 76, top: 78, width: 500, height: 28 },
      { fontSize: 14, color: C.teal, bold: true },
    );
    addText(
      slide,
      "Measure the factory.\nExplain the risk.\nKeep the human accountable.",
      { left: 76, top: 154, width: 850, height: 230 },
      {
        fontSize: 52,
        color: C.white,
        bold: true,
        typeface: "Aptos Display",
      },
    );
    addText(
      slide,
      `${pct(kpi.oee)} OEE  •  ${pct(kpi.fpy)} FPY  •  ${oot.pr_auc.toFixed(3)} OOT PR-AUC  •  ${pct(oot.recall)} recall`,
      { left: 80, top: 438, width: 910, height: 40 },
      { fontSize: 20, color: C.pale, bold: true },
    );
    addCallout(
      slide,
      { left: 80, top: 522, width: 1100, height: 90 },
      "Decision boundary",
      "Recommendation only • synthetic economics • human approval required • no autonomous maintenance execution",
      C.orange,
    );
    addText(
      slide,
      "Repository: github.com/muratmiracg-dev/Manufacturing-Quality-OEE-Predictive-Maintenance-Control-Tower",
      { left: 80, top: 660, width: 1100, height: 20 },
      { fontSize: 11, color: C.gray },
    );
    addNotes(slide, 18, [
      "artifacts/results/pipeline_metrics.json",
      "README.md",
      "docs/adr/001-recommendation-only-boundary.md",
    ]);
  }

  const inspection = await presentation.inspect({
    kind: "slide,textbox,shape,image,notes",
    search: "recommendation",
    maxChars: 10000,
  });
  console.log(inspection.ndjson);

  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    const png = await presentation.export({ slide, format: "png", scale: 1 });
    await fs.writeFile(
      path.join(renderDirectory, `${stem}.png`),
      new Uint8Array(await png.arrayBuffer()),
    );
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(
      path.join(renderDirectory, `${stem}.layout.json`),
      await layout.text(),
    );
  }
  const montage = await presentation.export({
    format: "webp",
    montage: true,
    scale: 1,
  });
  await fs.writeFile(
    path.join(renderDirectory, "deck-montage.webp"),
    new Uint8Array(await montage.arrayBuffer()),
  );
  await fs.writeFile(
    path.join(renderDirectory, "source-notes.txt"),
    `${sourceNotes.join("\n\n")}\n`,
    "utf8",
  );
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(outputPath);
  console.log(`Saved ${outputPath}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
