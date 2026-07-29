import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const repoRoot = path.resolve(process.argv[2] ?? ".");
const outputPath = path.join(
  repoRoot,
  "deliverables/excel/Manufacturing_Control_Tower.xlsx",
);
const renderDirectory = path.join(
  repoRoot,
  "tmp/excel-renders",
);

const palette = {
  ink: "#101820",
  steel: "#334155",
  orange: "#FF6B00",
  teal: "#00A6A6",
  green: "#2DBE8C",
  red: "#E63946",
  cream: "#F5F2EA",
  white: "#FFFFFF",
  pale: "#E8EDF2",
  yellow: "#FFF2CC",
  blueInput: "#DDEBF7",
  gray: "#94A3B8",
};

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
  if (field.length > 0 || row.length > 0) {
    row.push(field);
    rows.push(row);
  }
  return rows;
}

function coerceCsvCell(value) {
  const trimmed = value.trim();
  if (trimmed === "") return null;
  if (/^-?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$/.test(trimmed)) {
    return Number(trimmed);
  }
  if (trimmed === "True") return true;
  if (trimmed === "False") return false;
  return value;
}

async function importCsv(workbook, fileName, sheetName) {
  const csvText = await fs.readFile(
    path.join(repoRoot, "artifacts/results", fileName),
    "utf8",
  );
  const rows = parseCsv(csvText).map((row) => row.map(coerceCsvCell));
  const columnCount = Math.max(...rows.map((row) => row.length));
  const normalizedRows = rows.map((row) => [
    ...row,
    ...Array(columnCount - row.length).fill(null),
  ]);
  const sheet = workbook.worksheets.add(sheetName);
  sheet
    .getRangeByIndexes(0, 0, normalizedRows.length, columnCount)
    .values = normalizedRows;
  return sheet;
}

function titleBand(sheet, rangeAddress, title, subtitle = "") {
  const range = sheet.getRange(rangeAddress);
  range.merge();
  range.values = [[subtitle ? `${title}\n${subtitle}` : title]];
  range.format = {
    fill: palette.ink,
    font: { color: palette.white, bold: true, size: 20 },
    verticalAlignment: "center",
    horizontalAlignment: "left",
    wrapText: true,
    borders: { preset: "outside", style: "medium", color: palette.ink },
  };
  range.format.rowHeight = 32;
}

function styleDataSheet(sheet, tableName) {
  sheet.showGridLines = false;
  const used = sheet.getUsedRange();
  used.format.font = { name: "Aptos", size: 10, color: palette.steel };
  const header = used.getRow(0);
  header.format = {
    fill: palette.ink,
    font: { color: palette.white, bold: true, size: 10 },
    wrapText: true,
    verticalAlignment: "center",
    borders: { preset: "outside", style: "thin", color: palette.ink },
  };
  header.format.rowHeight = 30;
  used.format.autofitColumns();
  used.format.autofitRows();
  used.format.columnWidth = 15;
  sheet.freezePanes.freezeRows(1);
  const table = sheet.tables.add(used, true, tableName);
  table.style = "TableStyleMedium2";
}

function card(sheet, labelRange, valueRange, label, formula, format, accent) {
  const labelCell = sheet.getRange(labelRange);
  labelCell.merge();
  labelCell.values = [[label]];
  labelCell.format = {
    fill: accent,
    font: { color: palette.white, bold: true, size: 11 },
    horizontalAlignment: "left",
    verticalAlignment: "center",
  };
  const valueCell = sheet.getRange(valueRange);
  valueCell.merge();
  valueCell.formulas = [[formula]];
  valueCell.format = {
    fill: palette.white,
    font: { color: palette.ink, bold: true, size: 22 },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    numberFormat: format,
    borders: { preset: "outside", style: "medium", color: accent },
  };
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

  const workbook = Workbook.create();
  const oeeData = await importCsv(
    workbook,
    "oee_monthly_line.csv",
    "OEE Data",
  );
  const downtimeData = await importCsv(
    workbook,
    "downtime_pareto.csv",
    "Downtime Data",
  );
  const capabilityData = await importCsv(
    workbook,
    "process_capability.csv",
    "Capability Data",
  );
  const reliabilityData = await importCsv(
    workbook,
    "reliability_metrics.csv",
    "Reliability Data",
  );
  const spcData = await importCsv(
    workbook,
    "spc_xbar_latest.csv",
    "SPC Data",
  );
  const maintenanceData = await importCsv(
    workbook,
    "maintenance_priority.csv",
    "Maintenance Data",
  );
  const driftData = await importCsv(
    workbook,
    "data_drift.csv",
    "Drift Data",
  );
  const shapData = await importCsv(
    workbook,
    "shap_global_importance.csv",
    "SHAP Data",
  );

  for (const [sheet, table] of [
    [oeeData, "OEEDataTable"],
    [downtimeData, "DowntimeDataTable"],
    [capabilityData, "CapabilityDataTable"],
    [reliabilityData, "ReliabilityDataTable"],
    [spcData, "SPCDataTable"],
    [maintenanceData, "MaintenanceDataTable"],
    [driftData, "DriftDataTable"],
    [shapData, "SHAPDataTable"],
  ]) {
    styleDataSheet(sheet, table);
  }
  oeeData.getRange("C2:Q73").format.numberFormat = "0.00";
  oeeData.getRange("K2:Q73").format.numberFormat = "0.00%";
  downtimeData.getRange("B2:B20").format.numberFormat = "#,##0.0";
  downtimeData.getRange("D2:E20").format.numberFormat = "0.00%";
  capabilityData.getRange("B2:J20").format.numberFormat = "0.000";
  reliabilityData.getRange("D2:D30").format.numberFormat = "#,##0.00";
  reliabilityData.getRange("E2:E30").format.numberFormat = "0";
  reliabilityData.getRange("F2:H30").format.numberFormat = "0.00";
  reliabilityData.getRange("I2:I30").format.numberFormat = "0.0000";
  driftData.getRange("C2:C40").format.numberFormat = "0.0000";
  driftData.getRange("A:A").format.columnWidth = 34;
  driftData.getRange("B:B").format.columnWidth = 18;
  driftData.getRange("C:D").format.columnWidth = 14;
  shapData.getRange("C2:C40").format.numberFormat = "0.0000";
  shapData.getRange("A:A").format.columnWidth = 30;
  shapData.getRange("B:B").format.columnWidth = 38;
  shapData.getRange("C:C").format.columnWidth = 20;

  const assumptions = workbook.worksheets.add("Assumptions");
  assumptions.showGridLines = false;
  titleBand(
    assumptions,
    "A1:D2",
    "CONTROL TOWER ASSUMPTIONS",
    "Blue cells are editable; every scenario output is formula-driven.",
  );
  assumptions.getRange("A4:D15").values = [
    ["Parameter", "Value", "Unit", "Purpose"],
    ["Plant OEE target", 0.85, "%", "Executive performance target"],
    ["Availability target", 0.9, "%", "Planned production reliability"],
    ["Performance target", 0.95, "%", "Ideal cycle realization"],
    ["Quality target", 0.99, "%", "First-pass conforming output"],
    ["FPY target", 0.98, "%", "First-pass yield target"],
    ["Minimum recall", 0.72, "%", "Validation threshold constraint"],
    ["Maximum review rate", 0.4, "%", "Planner capacity constraint"],
    [
      "Intervention effectiveness",
      metrics.model.cost_assumptions.intervention_effectiveness,
      "%",
      "Avoided-loss assumption",
    ],
    [
      "False-negative cost",
      metrics.model.cost_assumptions.false_negative_cost,
      "cost units",
      "Validation threshold input",
    ],
    [
      "False-positive cost",
      metrics.model.cost_assumptions.false_positive_cost,
      "cost units",
      "Validation threshold input",
    ],
    [
      "Model threshold",
      metrics.model.threshold.threshold,
      "probability",
      "Selected on validation only",
    ],
  ];
  assumptions.getRange("A4:D4").format = {
    fill: palette.orange,
    font: { color: palette.white, bold: true },
  };
  assumptions.getRange("B5:B15").format = {
    fill: palette.blueInput,
    font: { color: "#0000FF", bold: true },
    borders: { preset: "outside", style: "thin", color: palette.teal },
  };
  assumptions.getRange("B5:B12").format.numberFormat = "0.00%";
  assumptions.getRange("B13:B14").format.numberFormat = "#,##0";
  assumptions.getRange("B15").format.numberFormat = "0.0000";
  assumptions.getRange("A4:D15").format.borders = {
    preset: "inside",
    style: "thin",
    color: "#D9E1E8",
  };
  assumptions.getRange("A18:D24").values = [
    ["Reference", "URL", "Usage", "Claim boundary"],
    [
      "ISO 22400-2",
      "https://www.iso.org/standard/54497.html",
      "Manufacturing KPI definitions",
      "Design reference only",
    ],
    [
      "NIST SPC",
      "https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc3.htm",
      "Control-chart taxonomy",
      "No process acceptance claim",
    ],
    [
      "NIST Capability",
      "https://www.itl.nist.gov/div898/handbook/pmc/section1/pmc16.htm",
      "Control/specification distinction",
      "Synthetic snapshot",
    ],
    [
      "NIST AI RMF",
      "https://www.nist.gov/itl/ai-risk-management-framework",
      "Model governance",
      "No compliance claim",
    ],
    [
      "NIST SSDF",
      "https://csrc.nist.gov/pubs/sp/800/218/final",
      "Secure development",
      "No audit claim",
    ],
    [
      "Project data",
      "Fully synthetic",
      "Seed 20260729",
      "No real plant data",
    ],
  ];
  assumptions.getRange("A18:D18").format = {
    fill: palette.steel,
    font: { color: palette.white, bold: true },
  };
  assumptions.getRange("A1:D24").format.font.name = "Aptos";
  assumptions.getRange("A1:D2").format.font = {
    name: "Aptos Display",
    color: palette.white,
    bold: true,
    size: 20,
  };
  assumptions.getRange("A4:D24").format.wrapText = true;
  assumptions.getRange("A1:D24").format.autofitColumns();
  assumptions.getRange("A:A").format.columnWidth = 28;
  assumptions.getRange("B:B").format.columnWidth = 22;
  assumptions.getRange("C:C").format.columnWidth = 18;
  assumptions.getRange("D:D").format.columnWidth = 34;
  assumptions.freezePanes.freezeRows(4);

  workbook.comments.setSelf({ displayName: "Murat Mirac Gedik" });
  workbook.comments.addThread(
    { cell: assumptions.getRange("B13") },
    "Synthetic false-negative cost used for validation-only threshold selection.",
  );
  workbook.comments.addThread(
    { cell: assumptions.getRange("B15") },
    "Selected from validation data with recall and review-capacity constraints; OOT was not used.",
  );

  const dashboard = workbook.worksheets.add("Executive Dashboard");
  dashboard.showGridLines = false;
  titleBand(
    dashboard,
    "A1:N2",
    "MANUFACTURING CONTROL TOWER",
    "OEE • QUALITY • RELIABILITY • PREDICTIVE MAINTENANCE | Deterministic synthetic data",
  );
  card(
    dashboard,
    "A4:C4",
    "A5:C7",
    "PLANT OEE",
    "=D5*G5*J5",
    "0.00%",
    palette.orange,
  );
  card(
    dashboard,
    "D4:F4",
    "D5:F7",
    "AVAILABILITY",
    "=SUM('OEE Data'!$D$2:$D$73)/SUM('OEE Data'!$C$2:$C$73)",
    "0.00%",
    palette.teal,
  );
  card(
    dashboard,
    "G4:I4",
    "G5:I7",
    "PERFORMANCE",
    "=SUMPRODUCT('OEE Data'!$L$2:$L$73,'OEE Data'!$D$2:$D$73)/SUM('OEE Data'!$D$2:$D$73)",
    "0.00%",
    palette.steel,
  );
  card(
    dashboard,
    "J4:L4",
    "J5:L7",
    "QUALITY / FPY",
    "=SUM('OEE Data'!$F$2:$F$73)/SUM('OEE Data'!$E$2:$E$73)",
    "0.00%",
    palette.green,
  );
  card(
    dashboard,
    "A9:C9",
    "A10:C11",
    "COPQ",
    "=SUM('OEE Data'!$I$2:$I$73)",
    "#,##0",
    palette.red,
  );
  card(
    dashboard,
    "D9:F9",
    "D10:F11",
    "MTBF (HOURS)",
    "=SUM('Reliability Data'!$D$2:$D$13)/SUM('Reliability Data'!$E$2:$E$13)",
    "0.00",
    palette.teal,
  );
  card(
    dashboard,
    "G9:I9",
    "G10:I11",
    "MTTR (HOURS)",
    "=SUM('Reliability Data'!$F$2:$F$13)/SUM('Reliability Data'!$E$2:$E$13)",
    "0.00",
    palette.orange,
  );
  card(
    dashboard,
    "J9:L9",
    "J10:L11",
    "TOTAL UNITS",
    "=SUM('OEE Data'!$E$2:$E$73)",
    "#,##0",
    palette.steel,
  );
  dashboard.getRange("M4:N11").merge();
  dashboard.getRange("M4:N11").values = [[
    `MODEL CONTROL\n\nChampion: ${metrics.model.champion_name}\nOOT PR-AUC: ${metrics.model.oot_metrics.pr_auc.toFixed(4)}\nOOT Recall: ${(metrics.model.oot_metrics.recall * 100).toFixed(2)}%\nOOT Alert Rate: ${(metrics.model.oot_metrics.alert_rate * 100).toFixed(2)}%\n\nRECOMMENDATION ONLY\nHuman approval required`,
  ]];
  dashboard.getRange("M4:N11").format = {
    fill: palette.pale,
    font: { color: palette.ink, bold: true, size: 10 },
    wrapText: true,
    verticalAlignment: "center",
    horizontalAlignment: "center",
    borders: { preset: "outside", style: "medium", color: palette.orange },
  };

  const months = [...new Set(oeeData.getRange("A2:A73").values.flat())];
  dashboard.getRange("P1:T1").values = [[
    "Month",
    "LINE-A",
    "LINE-B",
    "LINE-C",
    "LINE-D",
  ]];
  dashboard.getRange(`P2:P${months.length + 1}`).values = months.map((month) => [
    month,
  ]);
  const lineColumns = ["LINE-A", "LINE-B", "LINE-C", "LINE-D"];
  for (let row = 0; row < months.length; row += 1) {
    for (let column = 0; column < lineColumns.length; column += 1) {
      const excelRow = row + 2;
      const targetColumn = String.fromCharCode("Q".charCodeAt(0) + column);
      dashboard.getRange(`${targetColumn}${excelRow}`).formulas = [[
        `=SUMIFS('OEE Data'!$N$2:$N$73,'OEE Data'!$A$2:$A$73,$P${excelRow},'OEE Data'!$B$2:$B$73,${targetColumn}$1)`,
      ]];
    }
  }
  dashboard.getRange("P23:Q29").formulas = [
    ["='Downtime Data'!A1", "='Downtime Data'!B1"],
    ["='Downtime Data'!A2", "='Downtime Data'!B2/60"],
    ["='Downtime Data'!A3", "='Downtime Data'!B3/60"],
    ["='Downtime Data'!A4", "='Downtime Data'!B4/60"],
    ["='Downtime Data'!A5", "='Downtime Data'!B5/60"],
    ["='Downtime Data'!A6", "='Downtime Data'!B6/60"],
    ["='Downtime Data'!A7", "='Downtime Data'!B7/60"],
  ];
  dashboard.getRange("P:T").format.columnHidden = true;
  const oeeChart = dashboard.charts.add(
    "line",
    dashboard.getRange(`P1:T${months.length + 1}`),
  );
  oeeChart.title = "Monthly OEE by line";
  oeeChart.hasLegend = true;
  oeeChart.yAxis = { numberFormatCode: "0%" };
  oeeChart.setPosition("A13", "G29");
  const downtimeChart = dashboard.charts.add(
    "bar",
    dashboard.getRange("P23:Q29"),
  );
  downtimeChart.title = "Unplanned downtime Pareto (hours)";
  downtimeChart.hasLegend = false;
  downtimeChart.setPosition("H13", "N29");
  dashboard.getRange("A31:N33").merge();
  dashboard.getRange("A31:N33").values = [[
    "Interpretation boundary: all values are synthetic. The service provides decision support and cannot stop equipment, create maintenance orders or approve work.",
  ]];
  dashboard.getRange("A31:N33").format = {
    fill: palette.yellow,
    font: { color: palette.ink, bold: true, size: 10 },
    wrapText: true,
    verticalAlignment: "center",
    borders: { preset: "outside", style: "thin", color: palette.orange },
  };
  dashboard.getRange("A1:N33").format.font.name = "Aptos";
  dashboard.getRange("A1:N2").format.font = {
    name: "Aptos Display",
    color: palette.white,
    bold: true,
    size: 20,
  };
  dashboard.getRange("A:N").format.columnWidth = 12;
  dashboard.getRange("M:N").format.columnWidth = 15;
  dashboard.freezePanes.freezeRows(2);

  const planner = workbook.worksheets.add("Maintenance Planner");
  planner.showGridLines = false;
  titleBand(
    planner,
    "A1:L2",
    "HUMAN-IN-THE-LOOP MAINTENANCE PLANNER",
    "Latest OOT machine scores • Formula-driven cost/risk scenario",
  );
  planner.getRange("A4:L4").values = [[
    "Machine",
    "Line",
    "Failure Probability",
    "Criticality",
    "Failure Cost",
    "Maintenance Cost",
    "Intervention Effectiveness",
    "Expected Failure Cost",
    "Expected Avoided Loss",
    "Expected Net Benefit",
    "Risk / Cost",
    "Priority",
  ]];
  const maintenanceRows = maintenanceData.getRange("A2:Z13").values;
  const plannerValues = maintenanceRows.map((row) => [
    row[3],
    row[2],
    row[10],
    row[5],
    row[6],
    row[7],
    null,
    null,
    null,
    null,
    null,
    null,
  ]);
  planner.getRange("A5:L16").values = plannerValues;
  for (let row = 5; row <= 16; row += 1) {
    planner.getRange(`G${row}`).formulas = [["='Assumptions'!$B$12"]];
    planner.getRange(`H${row}`).formulas = [[
      `=C${row}*E${row}*(0.75+0.10*D${row})`,
    ]];
    planner.getRange(`I${row}`).formulas = [[`=H${row}*G${row}`]];
    planner.getRange(`J${row}`).formulas = [[`=I${row}-F${row}`]];
    planner.getRange(`K${row}`).formulas = [[`=I${row}/F${row}`]];
    planner.getRange(`L${row}`).formulas = [[
      `=IF(AND(C${row}>=MIN('Assumptions'!$B$15*1.25,0.95),D${row}>=4,J${row}>0),"P1",IF(AND(C${row}>='Assumptions'!$B$15,J${row}>0),"P2",IF(OR(C${row}>='Assumptions'!$B$15*0.65,K${row}>=0.75),"P3","MONITOR")))`,
    ]];
  }
  planner.getRange("A4:L4").format = {
    fill: palette.ink,
    font: { color: palette.white, bold: true, size: 10 },
    wrapText: true,
  };
  planner.getRange("A5:L16").format.borders = {
    preset: "inside",
    style: "thin",
    color: "#D9E1E8",
  };
  planner.getRange("C5:C16").format.numberFormat = "0.00%";
  planner.getRange("E5:J16").format.numberFormat = "#,##0";
  planner.getRange("G5:G16").format.numberFormat = "0.00%";
  planner.getRange("K5:K16").format.numberFormat = "0.00x";
  planner.getRange("G5:G16").format.fill = palette.blueInput;
  planner.getRange("C5:C16").conditionalFormats.add("colorScale", {
    criteria: [
      { type: "lowestValue", color: palette.green },
      { type: "percentile", value: 50, color: "#FFCC66" },
      { type: "highestValue", color: palette.red },
    ],
  });
  planner.getRange("J5:J16").conditionalFormats.add("cellIs", {
    operator: "lessThan",
    formula: 0,
    format: { fill: "#FCE8E6", font: { color: palette.red, bold: true } },
  });
  planner.getRange("L5:L16").conditionalFormats.add("containsText", {
    text: "P1",
    format: { fill: palette.red, font: { color: palette.white, bold: true } },
  });
  const chartData = workbook.worksheets.add("Chart Data");
  chartData.showGridLines = false;
  titleBand(
    chartData,
    "A1:B2",
    "CHART SOURCE",
    "Maintenance net benefit",
  );
  chartData.getRange("A4:B4").values = [["Machine", "Net Benefit"]];
  chartData.getRange("A4:B4").format = {
    fill: palette.ink,
    font: { color: palette.white, bold: true },
  };
  for (let row = 5; row <= 16; row += 1) {
    chartData.getRange(`A${row}:B${row}`).formulas = [[
      `='Maintenance Planner'!A${row}`,
      `='Maintenance Planner'!J${row}`,
    ]];
  }
  chartData.getRange("B5:B16").format.numberFormat = "#,##0";
  chartData.getRange("A4:B16").format.borders = {
    preset: "inside",
    style: "thin",
    color: "#D9E1E8",
  };
  chartData.getRange("A:A").format.columnWidth = 18;
  chartData.getRange("B:B").format.columnWidth = 18;
  chartData.freezePanes.freezeRows(4);
  const priorityChart = planner.charts.add(
    "bar",
    chartData.getRange("A4:B16"),
  );
  priorityChart.title = "Expected net benefit by machine";
  priorityChart.hasLegend = false;
  priorityChart.setPosition("A19", "H35");
  planner.getRange("I19:L35").merge();
  planner.getRange("I19:L35").values = [[
    "POLICY BOUNDARY\n\nRisk and synthetic economics support prioritization only.\n\nEvery recommendation requires maintenance-planner review, current safety context and explicit approval.\n\nNo CMMS, PLC or SCADA write action is implemented.",
  ]];
  planner.getRange("I19:L35").format = {
    fill: palette.pale,
    font: { color: palette.ink, bold: true, size: 11 },
    wrapText: true,
    horizontalAlignment: "center",
    verticalAlignment: "center",
    borders: { preset: "outside", style: "medium", color: palette.orange },
  };
  planner.getRange("A:L").format.columnWidth = 15;
  planner.getRange("A:B").format.columnWidth = 12;
  planner.getRange("L:L").format.columnWidth = 14;
  planner.getRange("A4:L16").format.autofitRows();
  planner.freezePanes.freezeRows(4);

  const monitoring = workbook.worksheets.add("Model Monitoring");
  monitoring.showGridLines = false;
  titleBand(
    monitoring,
    "A1:H2",
    "MODEL & ALARM MONITORING",
    "Validation decisions and untouched out-of-time results",
  );
  monitoring.getRange("A4:D14").values = [
    ["Metric", "Validation", "OOT", "Interpretation"],
    [
      "PR-AUC",
      metrics.model.validation_metrics.pr_auc,
      metrics.model.oot_metrics.pr_auc,
      "Higher; compare with positive rate",
    ],
    [
      "ROC-AUC",
      metrics.model.validation_metrics.roc_auc,
      metrics.model.oot_metrics.roc_auc,
      "Discrimination",
    ],
    [
      "Brier score",
      metrics.model.validation_metrics.brier_score,
      metrics.model.oot_metrics.brier_score,
      "Lower is better",
    ],
    [
      "ECE (10 bins)",
      metrics.model.validation_metrics.ece_10_bin,
      metrics.model.oot_metrics.ece_10_bin,
      "Calibration gap",
    ],
    [
      "Precision",
      metrics.model.validation_metrics.precision,
      metrics.model.oot_metrics.precision,
      "True failures among alerts",
    ],
    [
      "Recall",
      metrics.model.validation_metrics.recall,
      metrics.model.oot_metrics.recall,
      "Captured future failures",
    ],
    [
      "F1",
      metrics.model.validation_metrics.f1,
      metrics.model.oot_metrics.f1,
      "Precision/recall balance",
    ],
    [
      "Alert rate",
      metrics.model.validation_metrics.alert_rate,
      metrics.model.oot_metrics.alert_rate,
      "Planner burden",
    ],
    [
      "Positive rate",
      metrics.model.validation_metrics.positive_rate,
      metrics.model.oot_metrics.positive_rate,
      "No-skill PR baseline",
    ],
    [
      "Expected cost / observation",
      metrics.model.validation_metrics.expected_cost_per_observation,
      metrics.model.oot_metrics.expected_cost_per_observation,
      "Synthetic cost units",
    ],
  ];
  monitoring.getRange("A4:D4").format = {
    fill: palette.ink,
    font: { color: palette.white, bold: true },
  };
  monitoring.getRange("B5:C13").format.numberFormat = "0.00%";
  monitoring.getRange("B7:C8").format.numberFormat = "0.0000";
  monitoring.getRange("B14:C14").format.numberFormat = "#,##0.0";
  monitoring.getRange("F4:H11").values = [
    ["Control", "Result", "Status"],
    ["Champion", metrics.model.champion_name, "selected on validation"],
    ["Challenger", metrics.model.challenger_name, "retained"],
    ["Threshold", metrics.model.threshold.threshold, "validation only"],
    [
      "Review-capacity cap",
      metrics.model.cost_assumptions.maximum_alert_rate,
      "validation constraint",
    ],
    [
      "OOT alarm rate",
      metrics.model.oot_metrics.alert_rate,
      metrics.model.oot_metrics.alert_rate >
      metrics.model.cost_assumptions.maximum_alert_rate
        ? "watch"
        : "within cap",
    ],
    [
      "Maximum PSI",
      metrics.monitoring.max_psi,
      metrics.monitoring.features_at_action_level > 0 ? "action" : "stable",
    ],
    [
      "Data-quality checks",
      `${metrics.monitoring.data_quality_checks_passed}/${metrics.monitoring.data_quality_checks_total}`,
      "passed",
    ],
  ];
  monitoring.getRange("F4:H4").format = {
    fill: palette.orange,
    font: { color: palette.white, bold: true },
  };
  monitoring.getRange("G7:G9").format.numberFormat = "0.00%";
  monitoring.getRange("A4:H14").format.borders = {
    preset: "inside",
    style: "thin",
    color: "#D9E1E8",
  };
  monitoring.getRange("A4:H14").format.wrapText = true;
  monitoring.getRange("A:H").format.columnWidth = 20;
  monitoring.getRange("A:A").format.columnWidth = 25;
  monitoring.getRange("D:D").format.columnWidth = 32;
  monitoring.getRange("H:H").format.columnWidth = 20;
  monitoring.freezePanes.freezeRows(4);

  const dictionary = workbook.worksheets.add("Data Dictionary");
  dictionary.showGridLines = false;
  titleBand(
    dictionary,
    "A1:F2",
    "DATA DICTIONARY & FORMULA CONTROL",
    "Primary analytical fields, grain and operating constraints",
  );
  dictionary.getRange("A4:F24").values = [
    ["Table", "Field", "Type", "Unit / Domain", "Definition", "Model use"],
    ["production_shifts", "shift_id", "text", "unique", "Machine-shift primary key", "audit"],
    ["production_shifts", "timestamp", "datetime", "8-hour cadence", "Pre-shift decision timestamp", "split"],
    ["production_shifts", "planned_production_min", "number", "minutes", "Planned time less planned stops", "no"],
    ["production_shifts", "run_time_min", "number", "minutes", "Operating time after unplanned stops", "no"],
    ["production_shifts", "total_units", "integer", "count", "Gross shift output", "no"],
    ["production_shifts", "first_pass_good_units", "integer", "count", "Conforming before rework", "no"],
    ["production_shifts", "scrap_units", "integer", "count", "Discarded units", "no"],
    ["production_shifts", "rework_units", "integer", "count", "Units requiring rework", "no"],
    ["production_shifts", "vibration_rms", "number", "synthetic RMS", "Pre-shift vibration feature", "yes"],
    ["production_shifts", "temperature_c", "number", "Celsius", "Pre-shift thermal feature", "yes"],
    ["production_shifts", "lubrication_index", "number", "0-100", "Synthetic lubricant condition", "yes"],
    ["production_shifts", "failure_event", "0/1", "current shift", "Observed failure outcome", "no"],
    ["production_shifts", "failure_within_24h", "0/1", "next 3 shifts", "Future prediction target", "target"],
    ["quality_measurements", "ctq_dimension_mm", "number", "millimeters", "CTQ subgroup observation", "no"],
    ["quality_measurements", "lsl_mm", "number", "millimeters", "Engineering lower specification", "no"],
    ["quality_measurements", "usl_mm", "number", "millimeters", "Engineering upper specification", "no"],
    ["model_prediction", "failure_probability", "number", "0-1", "Calibrated 24-hour risk", "output"],
    ["maintenance", "criticality", "integer", "1-5", "Asset consequence tier", "policy"],
    ["maintenance", "expected_net_benefit", "number", "cost units", "Avoided loss less maintenance cost", "policy"],
    ["maintenance", "human_approval_required", "boolean", "always true", "Human decision gate", "contract"],
  ];
  dictionary.getRange("A4:F4").format = {
    fill: palette.ink,
    font: { color: palette.white, bold: true },
  };
  dictionary.getRange("A4:F24").format.wrapText = true;
  dictionary.getRange("A4:F24").format.borders = {
    preset: "inside",
    style: "thin",
    color: "#D9E1E8",
  };
  dictionary.getRange("A:A").format.columnWidth = 24;
  dictionary.getRange("B:B").format.columnWidth = 30;
  dictionary.getRange("C:C").format.columnWidth = 15;
  dictionary.getRange("D:D").format.columnWidth = 20;
  dictionary.getRange("E:E").format.columnWidth = 40;
  dictionary.getRange("F:F").format.columnWidth = 16;
  dictionary.freezePanes.freezeRows(4);

  const sheetOrder = [
    dashboard,
    assumptions,
    planner,
    monitoring,
    capabilityData,
    spcData,
    oeeData,
    downtimeData,
    reliabilityData,
    driftData,
    shapData,
    maintenanceData,
    chartData,
    dictionary,
  ];
  for (const sheet of sheetOrder) {
    const used = sheet.getUsedRange();
    used.format.font.name = "Aptos";
  }

  const keyCheck = await workbook.inspect({
    kind: "table",
    sheetId: "Executive Dashboard",
    range: "A1:N33",
    include: "values,formulas",
    tableMaxRows: 33,
    tableMaxCols: 14,
    maxChars: 12000,
  });
  console.log(keyCheck.ndjson);
  const errors = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 200 },
    summary: "final formula error scan",
  });
  console.log(errors.ndjson);

  for (const sheet of sheetOrder) {
    const safeName = sheet.name.replaceAll(/[^A-Za-z0-9]+/g, "_");
    const blob = await workbook.render({
      sheetName: sheet.name,
      autoCrop: "all",
      scale: 1,
      format: "png",
    });
    await fs.writeFile(
      path.join(renderDirectory, `${safeName}.png`),
      new Uint8Array(await blob.arrayBuffer()),
    );
  }

  const output = await SpreadsheetFile.exportXlsx(workbook);
  await output.save(outputPath);
  console.log(`Saved ${outputPath}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
