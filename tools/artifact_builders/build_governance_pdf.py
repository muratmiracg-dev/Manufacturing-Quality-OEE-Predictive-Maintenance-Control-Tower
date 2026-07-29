"""Build the detailed governance report from deterministic pipeline artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "deliverables/report/Manufacturing_Control_Tower_Governance_Report.pdf"
RESULTS = ROOT / "artifacts/results"
FIGURES = ROOT / "artifacts/figures"

INK = colors.HexColor("#0B131A")
INK_2 = colors.HexColor("#13212B")
STEEL = colors.HexColor("#334155")
GRAY = colors.HexColor("#64748B")
PALE = colors.HexColor("#E8EDF2")
CREAM = colors.HexColor("#F5F2EA")
WHITE = colors.white
ORANGE = colors.HexColor("#FF6B00")
ORANGE_PALE = colors.HexColor("#FFF0E5")
TEAL = colors.HexColor("#00A6A6")
GREEN = colors.HexColor("#2DBE8C")
RED = colors.HexColor("#E63946")
YELLOW = colors.HexColor("#F6C453")
BLUE = colors.HexColor("#1D6F8A")


def load_json(name: str) -> dict[str, Any]:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def load_csv(name: str) -> list[dict[str, str]]:
    with (RESULTS / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


pdfmetrics.registerFont(TTFont("DejaVuSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(
    TTFont("DejaVuSans-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
)

base_styles = getSampleStyleSheet()
STYLES = {
    "cover_eyebrow": ParagraphStyle(
        "CoverEyebrow",
        fontName="DejaVuSans-Bold",
        fontSize=10,
        leading=14,
        textColor=TEAL,
        spaceAfter=12,
    ),
    "cover_title": ParagraphStyle(
        "CoverTitle",
        fontName="DejaVuSans-Bold",
        fontSize=29,
        leading=35,
        textColor=WHITE,
        spaceAfter=18,
    ),
    "cover_subtitle": ParagraphStyle(
        "CoverSubtitle",
        fontName="DejaVuSans",
        fontSize=13,
        leading=19,
        textColor=PALE,
        spaceAfter=24,
    ),
    "kicker": ParagraphStyle(
        "Kicker",
        fontName="DejaVuSans-Bold",
        fontSize=8,
        leading=11,
        textColor=TEAL,
        spaceAfter=4,
    ),
    "title": ParagraphStyle(
        "Title",
        fontName="DejaVuSans-Bold",
        fontSize=21,
        leading=26,
        textColor=INK,
        spaceAfter=10,
    ),
    "h2": ParagraphStyle(
        "H2",
        fontName="DejaVuSans-Bold",
        fontSize=12,
        leading=16,
        textColor=ORANGE,
        spaceBefore=6,
        spaceAfter=5,
    ),
    "body": ParagraphStyle(
        "Body",
        fontName="DejaVuSans",
        fontSize=8.5,
        leading=12.5,
        textColor=STEEL,
        spaceAfter=6,
    ),
    "body_bold": ParagraphStyle(
        "BodyBold",
        fontName="DejaVuSans-Bold",
        fontSize=8.5,
        leading=12.5,
        textColor=INK,
        spaceAfter=6,
    ),
    "small": ParagraphStyle(
        "Small",
        fontName="DejaVuSans",
        fontSize=6.8,
        leading=9.5,
        textColor=GRAY,
    ),
    "caption": ParagraphStyle(
        "Caption",
        fontName="DejaVuSans",
        fontSize=6.5,
        leading=9,
        textColor=GRAY,
        alignment=TA_CENTER,
        spaceBefore=2,
        spaceAfter=5,
    ),
    "callout": ParagraphStyle(
        "Callout",
        fontName="DejaVuSans",
        fontSize=9,
        leading=13,
        textColor=WHITE,
    ),
    "callout_title": ParagraphStyle(
        "CalloutTitle",
        fontName="DejaVuSans-Bold",
        fontSize=8,
        leading=11,
        textColor=TEAL,
        spaceAfter=3,
    ),
    "metric_label": ParagraphStyle(
        "MetricLabel",
        fontName="DejaVuSans-Bold",
        fontSize=6.6,
        leading=9,
        textColor=GRAY,
        alignment=TA_CENTER,
    ),
    "metric_value": ParagraphStyle(
        "MetricValue",
        fontName="DejaVuSans-Bold",
        fontSize=14,
        leading=18,
        textColor=INK,
        alignment=TA_CENTER,
    ),
    "table_head": ParagraphStyle(
        "TableHead",
        fontName="DejaVuSans-Bold",
        fontSize=7,
        leading=9,
        textColor=WHITE,
    ),
    "table_body": ParagraphStyle(
        "TableBody",
        fontName="DejaVuSans",
        fontSize=6.7,
        leading=9,
        textColor=STEEL,
    ),
    "table_body_bold": ParagraphStyle(
        "TableBodyBold",
        fontName="DejaVuSans-Bold",
        fontSize=6.7,
        leading=9,
        textColor=INK,
    ),
}


def para(text: str, style: str = "body") -> Paragraph:
    return Paragraph(text, STYLES[style])


def bullet(items: list[str]) -> list[Paragraph]:
    return [para(f"• {item}") for item in items]


def pct(value: Any, digits: int = 2) -> str:
    return f"{float(value) * 100:.{digits}f}%"


def num(value: Any, digits: int = 0) -> str:
    return f"{float(value):,.{digits}f}"


def table_cell(value: Any, bold: bool = False) -> Paragraph:
    return para(str(value), "table_body_bold" if bold else "table_body")


def styled_table(
    headers: list[str],
    rows: list[list[Any]],
    widths: list[float] | None = None,
    row_fills: dict[int, colors.Color] | None = None,
) -> Table:
    data = [[para(header, "table_head") for header in headers]]
    data.extend([[table_cell(value) for value in row] for row in rows])
    report_table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    rules: list[tuple[Any, ...]] = [
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.35, PALE),
    ]
    for row_index in range(1, len(data)):
        rules.append(
            (
                "BACKGROUND",
                (0, row_index),
                (-1, row_index),
                CREAM if row_index % 2 else WHITE,
            )
        )
    for row_index, fill in (row_fills or {}).items():
        rules.append(("BACKGROUND", (0, row_index + 1), (-1, row_index + 1), fill))
    report_table.setStyle(TableStyle(rules))
    return report_table


def metric_cards(items: list[tuple[str, str, colors.Color]], columns: int = 4) -> Table:
    cells: list[list[Any]] = []
    row: list[Any] = []
    for label, value, accent in items:
        content = Table(
            [
                [para(label.upper(), "metric_label")],
                [para(value, "metric_value")],
            ],
            colWidths=[(170 / columns) * mm],
        )
        content.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), WHITE),
                    ("BOX", (0, 0), (-1, -1), 0.7, accent),
                    ("LINEBEFORE", (0, 0), (0, -1), 4, accent),
                    ("TOPPADDING", (0, 0), (-1, 0), 6),
                    ("BOTTOMPADDING", (0, 1), (-1, 1), 7),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        row.append(content)
        if len(row) == columns:
            cells.append(row)
            row = []
    if row:
        row.extend([""] * (columns - len(row)))
        cells.append(row)
    cards = Table(cells, colWidths=[(170 / columns) * mm] * columns, hAlign="LEFT")
    cards.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return cards


def callout(title: str, body: str, accent: colors.Color = TEAL) -> Table:
    content = Table(
        [[para(title.upper(), "callout_title")], [para(body, "callout")]],
        colWidths=[170 * mm],
    )
    content.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), INK_2),
                ("BOX", (0, 0), (-1, -1), 0.8, accent),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, 0), 7),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
            ]
        )
    )
    return content


def figure(name: str, max_width_mm: float = 170, max_height_mm: float = 92) -> Image:
    path = FIGURES / name
    with PILImage.open(path) as source:
        width, height = source.size
    scale = min(
        (max_width_mm * mm) / width,
        (max_height_mm * mm) / height,
    )
    return Image(str(path), width=width * scale, height=height * scale)


def section_header(kicker: str, title: str) -> list[Any]:
    return [para(kicker.upper(), "kicker"), para(title, "title")]


def end_page(story: list[Any]) -> None:
    story.append(PageBreak())


def on_page(canvas: Any, document: BaseDocTemplate) -> None:
    width, height = A4
    canvas.saveState()
    if document.page == 1:
        canvas.setFillColor(INK)
        canvas.rect(0, 0, width, height, fill=1, stroke=0)
        canvas.setFillColor(ORANGE)
        canvas.rect(0, 0, 10 * mm, height, fill=1, stroke=0)
        canvas.setFillColor(GRAY)
        canvas.setFont("DejaVuSans", 6.5)
        canvas.drawString(22 * mm, 12 * mm, "Portfolio governance report • July 2026")
    else:
        canvas.setFillColor(ORANGE)
        canvas.rect(0, height - 5 * mm, width, 5 * mm, fill=1, stroke=0)
        canvas.setStrokeColor(PALE)
        canvas.setLineWidth(0.5)
        canvas.line(20 * mm, 15 * mm, width - 20 * mm, 15 * mm)
        canvas.setFillColor(GRAY)
        canvas.setFont("DejaVuSans", 6.2)
        canvas.drawString(
            20 * mm,
            10 * mm,
            "Manufacturing Quality, OEE & Predictive Maintenance Control Tower",
        )
        canvas.drawRightString(width - 20 * mm, 10 * mm, f"{document.page:02d}")
    canvas.restoreState()


def build() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    metrics = load_json("pipeline_metrics.json")
    capability = load_csv("process_capability.csv")
    downtime = load_csv("downtime_pareto.csv")
    quality_checks = load_csv("data_quality_checks.csv")
    local_shap = load_csv("shap_local_explanations.csv")[:4]

    kpi = metrics["executive_kpis"]
    model = metrics["model"]
    oot = model["oot_metrics"]
    validation = model["validation_metrics"]

    document = BaseDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=19 * mm,
        bottomMargin=19 * mm,
        title="Manufacturing Control Tower Governance Report",
        author="Murat Mirac Gedik",
        subject="Synthetic manufacturing analytics and predictive-maintenance governance",
    )
    frame = Frame(
        document.leftMargin,
        document.bottomMargin,
        document.width,
        document.height,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    document.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=on_page)])
    story: list[Any] = []

    # 1. Cover
    story.extend(
        [
            Spacer(1, 47 * mm),
            para("MANUFACTURING GOVERNANCE", "cover_eyebrow"),
            para(
                "Quality, OEE &<br/>Predictive Maintenance<br/>Control Tower",
                "cover_title",
            ),
            para(
                "Detailed governance report for a deterministic synthetic factory, "
                "time-aware predictive maintenance model and human-gated decision policy.",
                "cover_subtitle",
            ),
            callout(
                "Scope boundary",
                "Recommendation only. No automated work orders, PLC/SCADA writes, equipment stops or maintenance approvals.",
                ORANGE,
            ),
            Spacer(1, 14 * mm),
            metric_cards(
                [
                    ("OEE", pct(kpi["oee"]), ORANGE),
                    ("FPY", pct(kpi["fpy"]), GREEN),
                    ("OOT PR-AUC", f"{oot['pr_auc']:.3f}", TEAL),
                    ("OOT recall", pct(oot["recall"]), BLUE),
                ]
            ),
        ]
    )
    end_page(story)

    # 2. Contents
    story.extend(section_header("Navigation", "Contents and evidence chain"))
    story.append(
        para(
            "The report follows one governed evidence chain: synthetic events become "
            "auditable KPIs, time-split predictions, explanations and planner-reviewed recommendations."
        )
    )
    contents = [
        ("01", "Executive decision record"),
        ("02", "Scope and claim boundary"),
        ("03", "Deterministic data design"),
        ("04", "Data contract and quality"),
        ("05", "System architecture"),
        ("06", "OEE performance"),
        ("07", "Downtime and reliability"),
        ("08", "Quality economics and capability"),
        ("09", "SPC method and alarms"),
        ("10", "Temporal model development"),
        ("11", "Champion/challenger validation"),
        ("12", "Calibration and alarm quality"),
        ("13", "SHAP explanations"),
        ("14", "Maintenance decision policy"),
        ("15", "Service, database and BI"),
        ("16", "Security and threat model"),
        ("17", "Monitoring and incident response"),
        ("18", "Risk register and limitations"),
        ("19", "Reference crosswalk"),
        ("20", "Delivery matrix"),
    ]
    story.append(
        styled_table(
            ["Section", "Evidence topic", "Section", "Evidence topic"],
            [[a[0], a[1], b[0], b[1]] for a, b in zip(contents[:10], contents[10:], strict=True)],
            [16 * mm, 66 * mm, 16 * mm, 66 * mm],
        )
    )
    story.append(Spacer(1, 8 * mm))
    story.append(
        callout(
            "Review principle",
            "Metrics in this report are read directly from pipeline artifacts. No model or business result is manually fabricated.",
            TEAL,
        )
    )
    story.extend(
        bullet(
            [
                "Primary evidence: artifacts/results/pipeline_metrics.json and exported analytical CSVs.",
                "Reproducibility: seed 20260729, documented configuration and executable pipeline.",
                "Communication: the same results feed README, Excel, PBIP, PowerPoint and this report.",
                "Reference mapping: official sources are design inputs, never certification claims.",
            ]
        )
    )
    end_page(story)

    # 3. Executive decision record
    story.extend(
        section_header(
            "01 • Executive decision record",
            "The plant clears its OEE target; alert workload is the open control",
        )
    )
    story.append(
        metric_cards(
            [
                ("OEE", pct(kpi["oee"]), ORANGE),
                ("Availability", pct(kpi["availability"]), TEAL),
                ("Performance", pct(kpi["performance"]), BLUE),
                ("Quality / FPY", pct(kpi["quality_rate"]), GREEN),
                ("Unplanned stop", f"{num(kpi['unplanned_downtime_hours'])} h", RED),
                ("COPQ", num(kpi["copq"]), ORANGE),
                ("MTBF", f"{num(kpi['mtbf_hours'], 2)} h", TEAL),
                ("MTTR", f"{num(kpi['mttr_hours'], 2)} h", BLUE),
            ]
        )
    )
    story.append(Spacer(1, 6 * mm))
    story.append(
        styled_table(
            ["Decision area", "Evidence", "Disposition", "Owner gate"],
            [
                [
                    "OEE",
                    f"{pct(kpi['oee'])}; performance {pct(kpi['performance'])}",
                    "Investigate speed loss before availability",
                    "Operations",
                ],
                [
                    "Quality",
                    f"FPY {pct(kpi['fpy'])}; PRD-A Ppk {float(capability[0]['ppk']):.2f}",
                    "Capability investigation",
                    "Quality engineering",
                ],
                [
                    "Model",
                    f"OOT PR-AUC {oot['pr_auc']:.3f}; recall {pct(oot['recall'])}",
                    "Useful ranking; capacity watch",
                    "Model owner",
                ],
                [
                    "Maintenance",
                    f"{metrics['decision_support']['recommendation_counts']['P1']} P1 recommendations",
                    "Planner review only",
                    "Maintenance planner",
                ],
            ],
            [30 * mm, 54 * mm, 52 * mm, 34 * mm],
            {2: ORANGE_PALE},
        )
    )
    story.append(Spacer(1, 6 * mm))
    story.append(
        callout(
            "Open operational control",
            f"OOT alert rate is {pct(oot['alert_rate'])}, above the 40% validation review-capacity cap. "
            "The report treats this as a watch item instead of suppressing it.",
            RED,
        )
    )
    story.extend(
        bullet(
            [
                "All results describe synthetic data and synthetic cost units.",
                "The system can rank and explain; it cannot execute maintenance.",
                "Real-plant adoption would require shadow validation, plant-specific cost calibration and safety ownership.",
            ]
        )
    )
    end_page(story)

    # 4. Scope boundary
    story.extend(
        section_header(
            "02 • Scope and claim boundary", "What the platform does—and explicitly does not do"
        )
    )
    story.append(
        styled_table(
            ["In scope", "Out of scope"],
            [
                [
                    "Compute OEE, downtime, reliability, quality, SPC and capability metrics.",
                    "Control production equipment or safety systems.",
                ],
                [
                    "Estimate 24-hour failure probability and surface SHAP reason codes.",
                    "Create, approve or close CMMS work orders.",
                ],
                [
                    "Combine risk, criticality and synthetic economics into planner priorities.",
                    "Claim real-world avoided cost or maintenance ROI.",
                ],
                [
                    "Serve recommendations through a read-only FastAPI contract.",
                    "Write to PLC, SCADA, historian or enterprise maintenance systems.",
                ],
                [
                    "Map design evidence to official references.",
                    "Claim certification, conformance or regulatory compliance.",
                ],
            ],
            [85 * mm, 85 * mm],
        )
    )
    story.append(Spacer(1, 7 * mm))
    story.append(
        callout(
            "Human approval invariant",
            "Every response includes human_approval_required=true and execution_mode=recommendation_only. "
            "The decision boundary is enforced in code, contract tests and documentation.",
            ORANGE,
        )
    )
    story.extend(section_header("Claim language", "Approved interpretation"))
    story.extend(
        bullet(
            [
                "Use: “synthetic demonstration,” “decision support,” “estimated probability,” and “proposed pilot.”",
                "Avoid: “production deployed,” “automatically schedules maintenance,” “prevents failures,” or “compliant with ISO/NIST.”",
                "Treat costs as scenario inputs; do not present them as financial statements.",
                "Treat SHAP values as model attribution, not root-cause proof.",
            ]
        )
    )
    story.append(
        styled_table(
            ["Control", "Evidence"],
            [
                ["API contract", "src/manufacturing_ct/api.py and tests/test_api.py"],
                ["Architecture decision", "docs/adr/001-recommendation-only-boundary.md"],
                ["Threat mitigation", "docs/governance/threat_model.md"],
                ["Runtime policy", "artifacts/results/policy_config.json"],
            ],
            [55 * mm, 115 * mm],
        )
    )
    end_page(story)

    # 5. Data design
    story.extend(
        section_header(
            "03 • Deterministic data design", "A synthetic plant with realistic operating structure"
        )
    )
    story.append(
        metric_cards(
            [
                ("Lines", str(metrics["dataset"]["lines"]), ORANGE),
                ("Machines", str(metrics["dataset"]["machines"]), TEAL),
                ("Products", str(metrics["dataset"]["products"]), GREEN),
                ("Shifts", str(metrics["dataset"]["shifts"]), BLUE),
                ("Machine shifts", num(metrics["dataset"]["production_shift_rows"]), ORANGE),
                ("CTQ readings", num(metrics["dataset"]["quality_measurement_rows"]), GREEN),
                ("Downtime events", num(metrics["dataset"]["downtime_event_rows"]), RED),
                ("Maintenance events", num(metrics["dataset"]["maintenance_event_rows"]), TEAL),
            ]
        )
    )
    story.append(Spacer(1, 6 * mm))
    story.append(
        styled_table(
            ["Entity", "Grain", "Examples", "Purpose"],
            [
                [
                    "Production shift",
                    "machine x 8-hour shift",
                    "counts, speed, sensors, lags",
                    "OEE and model features",
                ],
                [
                    "Quality measurement",
                    "five CTQ readings / subgroup",
                    "dimension, specs, defect counts",
                    "SPC and capability",
                ],
                [
                    "Downtime event",
                    "event",
                    "planned flag, failure type, duration",
                    "Pareto and reliability",
                ],
                [
                    "Maintenance event",
                    "event",
                    "action, hours, synthetic cost",
                    "history and policy",
                ],
                [
                    "Prediction",
                    "pre-shift decision record",
                    "probability, threshold, explanations",
                    "human review",
                ],
            ],
            [33 * mm, 42 * mm, 53 * mm, 42 * mm],
        )
    )
    story.append(Spacer(1, 6 * mm))
    story.append(
        callout(
            "Reproducibility",
            f"Seed {metrics['seed']} • period {metrics['period']['start']} to {metrics['period']['end']} • "
            "the same configuration reproduces the exported metrics and figures.",
            TEAL,
        )
    )
    story.extend(
        bullet(
            [
                "Multiple failure modes: electrical, bearing, sensor, hydraulic and overheating.",
                "Planned/unplanned downtime remains distinct from quality and maintenance records.",
                "Sensor degradation, product mix, seasonality and maintenance history generate learnable—not perfectly separable—risk.",
                "No real operator, equipment or plant data is present.",
            ]
        )
    )
    end_page(story)

    # 6. Data contract and quality
    story.extend(
        section_header(
            "04 • Data contract and quality",
            "Contracts define grain, availability time and failure behavior",
        )
    )
    story.append(
        styled_table(
            ["Contract control", "Implementation", "Failure disposition"],
            [
                ["Primary key uniqueness", "shift_id at machine-shift grain", "Fail pipeline"],
                [
                    "Required field completeness",
                    "pre-feature contract checks",
                    "Fail or quarantine",
                ],
                ["Non-negative counts", "units, downtime and repair duration", "Fail pipeline"],
                ["Downtime within shift", "event duration bounded by shift", "Fail pipeline"],
                ["Sensor plausibility", "documented synthetic ranges", "Flag and investigate"],
                [
                    "Schema/version",
                    "data contract + deterministic config",
                    "Block incompatible change",
                ],
            ],
            [45 * mm, 73 * mm, 52 * mm],
        )
    )
    story.append(Spacer(1, 5 * mm))
    dq_rows = [
        [
            row["check"],
            "PASS" if row["passed"] == "True" else "FAIL",
            row["exceptions"],
        ]
        for row in quality_checks
    ]
    story.append(
        styled_table(
            ["Pipeline check", "Result", "Exceptions / context"],
            dq_rows,
            [78 * mm, 28 * mm, 64 * mm],
        )
    )
    story.append(Spacer(1, 5 * mm))
    story.append(
        callout(
            "Quality result",
            f"{metrics['monitoring']['data_quality_checks_passed']}/{metrics['monitoring']['data_quality_checks_total']} "
            "gates passed. Completeness context is recorded rather than silently discarded.",
            GREEN,
        )
    )
    story.extend(
        bullet(
            [
                "Temporal availability is part of the contract: model features must exist before the shift decision timestamp.",
                "Prediction labels and realized outcomes are stored separately to preserve auditability.",
                "Data quality is not model drift; each has distinct thresholds and owners.",
            ]
        )
    )
    end_page(story)

    # 7. Architecture
    story.extend(
        section_header(
            "05 • System architecture",
            "Five analytical layers with one recommendation-only boundary",
        )
    )
    architecture_rows = [
        [
            "1",
            "Synthetic generator",
            "events, sensors, quality and maintenance history",
            "versioned CSV/artifacts",
        ],
        [
            "2",
            "KPI + SPC analytics",
            "OEE, Pareto, MTBF/MTTR, capability and alarms",
            "analytical tables/figures",
        ],
        [
            "3",
            "Temporal ML",
            "fit, calibration, validation, OOT and threshold controls",
            "model bundle/metrics",
        ],
        [
            "4",
            "SHAP + policy",
            "global/local attribution and cost-risk prioritization",
            "reason codes/recommendations",
        ],
        [
            "5",
            "Delivery",
            "FastAPI, PostgreSQL views, PBIP, Excel, reports",
            "human-facing outputs",
        ],
    ]
    story.append(
        styled_table(
            ["Layer", "Component", "Responsibility", "Evidence"],
            architecture_rows,
            [14 * mm, 39 * mm, 78 * mm, 39 * mm],
        )
    )
    story.append(Spacer(1, 7 * mm))
    story.append(
        callout(
            "Governed analytical record",
            "The same versioned metrics, model threshold and decision record feed every channel. "
            "This reduces narrative/model divergence across code, BI and executive reporting.",
            TEAL,
        )
    )
    story.extend(section_header("Deployment profiles", "Runtime separation"))
    story.append(
        styled_table(
            ["Profile", "Purpose", "Key controls"],
            [
                [
                    "Docker Compose",
                    "local integrated stack",
                    "API, PostgreSQL, Prometheus and Grafana",
                ],
                [
                    "Kubernetes",
                    "portable deployment starter",
                    "non-root, read-only filesystem, HPA, PDB, NetworkPolicy",
                ],
                ["PostgreSQL", "governed data serving", "normalized tables and analytical views"],
                [
                    "Prometheus/Grafana",
                    "operational observability",
                    "service/model metrics, alerts and dashboards",
                ],
            ],
            [38 * mm, 55 * mm, 77 * mm],
        )
    )
    story.extend(
        bullet(
            [
                "No plant-network segmentation, identity-provider integration or enterprise secrets system is implemented.",
                "Production credentials must be externalized; the repository contains examples only.",
            ]
        )
    )
    end_page(story)

    # 8. OEE
    story.extend(
        section_header(
            "06 • OEE performance", "Performance loss is the largest mathematical constraint"
        )
    )
    story.append(figure("oee_monthly_trend.png", 170, 88))
    story.append(
        para(
            "Figure 1. Monthly OEE by production line from deterministic pipeline output.",
            "caption",
        )
    )
    story.append(
        metric_cards(
            [
                ("Availability", pct(kpi["availability"]), TEAL),
                ("Performance", pct(kpi["performance"]), ORANGE),
                ("Quality", pct(kpi["quality_rate"]), GREEN),
                ("OEE", pct(kpi["oee"]), BLUE),
            ]
        )
    )
    story.append(Spacer(1, 5 * mm))
    story.append(
        styled_table(
            ["Component", "Formula", "Result", "Interpretation"],
            [
                [
                    "Availability",
                    "runtime / planned production time",
                    pct(kpi["availability"]),
                    "limited downtime loss",
                ],
                [
                    "Performance",
                    "ideal output / actual runtime",
                    pct(kpi["performance"]),
                    "largest gap to 100%",
                ],
                [
                    "Quality",
                    "first-pass good / total units",
                    pct(kpi["quality_rate"]),
                    "quality opportunity remains",
                ],
                [
                    "OEE",
                    "availability x performance x quality",
                    pct(kpi["oee"]),
                    "ratio-of-sums plant result",
                ],
            ],
            [34 * mm, 55 * mm, 25 * mm, 56 * mm],
        )
    )
    story.append(
        callout(
            "Calculation control",
            "OEE uses runtime-weighted ratios and plant-level ratio-of-sums. Averaging row-level OEE would create weighting error.",
            ORANGE,
        )
    )
    end_page(story)

    # 9. Downtime and reliability
    story.extend(
        section_header(
            "07 • Downtime and reliability",
            "Electrical events and minor stops explain most downtime",
        )
    )
    story.append(figure("downtime_pareto.png", 170, 84))
    story.append(para("Figure 2. Unplanned downtime duration and cumulative share.", "caption"))
    story.append(
        metric_cards(
            [
                ("Unplanned hours", num(kpi["unplanned_downtime_hours"]), RED),
                ("Failures", num(kpi["failure_count"]), ORANGE),
                ("MTBF", f"{num(kpi['mtbf_hours'], 2)} h", TEAL),
                ("MTTR", f"{num(kpi['mttr_hours'], 2)} h", BLUE),
            ]
        )
    )
    story.append(Spacer(1, 4 * mm))
    story.append(
        styled_table(
            ["Category", "Hours", "Events", "Share", "Cumulative"],
            [
                [
                    row["category"],
                    f"{float(row['duration_min']) / 60:,.1f}",
                    row["event_count"],
                    pct(row["share"]),
                    pct(row["cumulative_share"]),
                ]
                for row in downtime
            ],
            [46 * mm, 30 * mm, 28 * mm, 28 * mm, 38 * mm],
        )
    )
    story.append(
        callout(
            "Priority",
            "Electrical and minor-stop countermeasures should precede lower-frequency categories. "
            "Reliability metrics describe history; they do not authorize maintenance.",
            TEAL,
        )
    )
    end_page(story)

    # 10. Quality and capability
    story.extend(
        section_header(
            "08 • Quality economics and capability", "PRD-A is the long-term capability watch item"
        )
    )
    story.append(figure("process_capability.png", 170, 82))
    story.append(para("Figure 3. Within and overall capability indices by product.", "caption"))
    story.append(
        metric_cards(
            [
                ("FPY", pct(kpi["fpy"]), GREEN),
                ("Scrap", pct(kpi["scrap_rate"]), RED),
                ("Rework", pct(kpi["rework_rate"]), ORANGE),
                ("COPQ", num(kpi["copq"]), TEAL),
            ]
        )
    )
    story.append(Spacer(1, 4 * mm))
    story.append(
        styled_table(
            ["Product", "Cp", "Cpk", "Pp", "Ppk", "Disposition"],
            [
                [
                    row["product_id"],
                    f"{float(row['cp']):.3f}",
                    f"{float(row['cpk']):.3f}",
                    f"{float(row['pp']):.3f}",
                    f"{float(row['ppk']):.3f}",
                    "Watch long-term centering"
                    if row["product_id"] == "PRD-A"
                    else "Synthetic snapshot",
                ]
                for row in capability
            ],
            [27 * mm, 22 * mm, 24 * mm, 22 * mm, 24 * mm, 51 * mm],
            {0: ORANGE_PALE},
        )
    )
    story.append(
        callout(
            "Interpretation",
            "Cp/Cpk use within-subgroup variation; Pp/Ppk use overall variation. "
            "These are synthetic capability estimates—not product acceptance decisions.",
            ORANGE,
        )
    )
    end_page(story)

    # 11. SPC
    story.extend(
        section_header(
            "09 • SPC method and alarms", "Chart choice follows data type and sampling design"
        )
    )
    story.append(figure("spc_xbar.png", 170, 82))
    story.append(
        para("Figure 4. X-bar chart for fixed n=5 CTQ subgroups with rule signals.", "caption")
    )
    story.append(
        styled_table(
            ["Chart", "Data", "Sample-size condition", "Why selected"],
            [
                ["X-bar/R", "CTQ dimension", "fixed n=5", "subgroup mean and short-term range"],
                [
                    "I-MR",
                    "roughness",
                    "one observation / shift",
                    "individual level and moving range",
                ],
                [
                    "p",
                    "defective proportion",
                    "variable lot size",
                    "binomial proportion limits vary by n",
                ],
                [
                    "u",
                    "defects per unit",
                    "variable inspected units",
                    "Poisson rate limits vary by exposure",
                ],
                ["np / c", "not selected", "constant size required", "assumption does not hold"],
            ],
            [28 * mm, 42 * mm, 51 * mm, 49 * mm],
        )
    )
    story.append(Spacer(1, 4 * mm))
    story.append(
        styled_table(
            ["Alarm rule", "Documented trigger"],
            [
                ["Rule 1", "one point beyond 3 sigma"],
                ["Rule 2", "two of three consecutive points beyond 2 sigma on one side"],
                ["Rule 3", "four of five consecutive points beyond 1 sigma on one side"],
                ["Rule 4", "eight consecutive points on one side of the center line"],
            ],
            [33 * mm, 137 * mm],
        )
    )
    story.append(
        callout(
            "Critical distinction",
            "Control limits estimate baseline process behavior. LSL/USL are independent engineering specifications used for capability.",
            RED,
        )
    )
    end_page(story)

    # 12. Temporal development
    story.extend(
        section_header(
            "10 • Temporal model development",
            "Model fit, calibration, validation and OOT remain chronologically isolated",
        )
    )
    partitions = model["partitions"]
    story.append(
        styled_table(
            ["Partition", "Window", "Rows", "Positive rate", "Allowed decisions"],
            [
                [
                    name.replace("_", " ").title(),
                    f"{part['start'][:10]} to {part['end'][:10]}",
                    num(part["rows"]),
                    pct(part["positive_rate"]),
                    {
                        "model_fit": "fit candidate models",
                        "calibration": "fit sigmoid calibration",
                        "validation": "select champion and threshold",
                        "oot": "evaluate only",
                    }[name],
                ]
                for name, part in partitions.items()
            ],
            [29 * mm, 48 * mm, 25 * mm, 30 * mm, 38 * mm],
            {3: ORANGE_PALE},
        )
    )
    story.append(Spacer(1, 7 * mm))
    story.append(
        callout(
            "Leakage controls",
            "Lagged and rolling features use past-only values; the 24-hour label looks forward. "
            "Chronological boundaries and purge gaps prevent observations from seeing future outcomes.",
            TEAL,
        )
    )
    story.extend(section_header("Class imbalance and thresholding", "Decision controls"))
    story.extend(
        bullet(
            [
                f"Overall 24-hour positive rate: {pct(metrics['dataset']['target_positive_rate'])}.",
                "PR-AUC is compared with the positive-rate no-skill baseline, not interpreted in isolation.",
                f"Threshold {model['threshold']['threshold']:.4f} is chosen only on validation data.",
                "Validation constraints: recall target at least 72%; review-capacity cap 40%.",
                "OOT data does not alter model choice, calibration or threshold.",
            ]
        )
    )
    story.append(
        styled_table(
            ["Control", "Evidence"],
            [
                ["Feature availability", "pre-shift feature construction and data contract"],
                ["Chronological split", "model_fit → calibration → validation → OOT"],
                ["Calibration isolation", "dedicated calibration partition"],
                ["Threshold isolation", "validation-only selection"],
                ["OOT immutability", "single final evaluation"],
            ],
            [55 * mm, 115 * mm],
        )
    )
    end_page(story)

    # 13. Champion/challenger
    story.extend(
        section_header(
            "11 • Champion/challenger validation",
            "Random forest wins narrowly; logistic regression remains available",
        )
    )
    candidates = model["candidate_summary"]
    story.append(
        styled_table(
            ["Candidate", "Val PR-AUC", "Val ROC-AUC", "Val Brier", "Selection score", "Status"],
            [
                [
                    "Random forest",
                    f"{candidates['random_forest']['validation_at_0_5']['pr_auc']:.4f}",
                    f"{candidates['random_forest']['validation_at_0_5']['roc_auc']:.4f}",
                    f"{candidates['random_forest']['validation_at_0_5']['brier_score']:.4f}",
                    f"{candidates['random_forest']['selection_score']:.4f}",
                    "Champion",
                ],
                [
                    "Logistic regression",
                    f"{candidates['logistic_regression']['validation_at_0_5']['pr_auc']:.4f}",
                    f"{candidates['logistic_regression']['validation_at_0_5']['roc_auc']:.4f}",
                    f"{candidates['logistic_regression']['validation_at_0_5']['brier_score']:.4f}",
                    f"{candidates['logistic_regression']['selection_score']:.4f}",
                    "Challenger",
                ],
            ],
            [45 * mm, 26 * mm, 26 * mm, 24 * mm, 29 * mm, 20 * mm],
            {0: ORANGE_PALE},
        )
    )
    story.append(Spacer(1, 6 * mm))
    story.append(
        metric_cards(
            [
                ("OOT PR-AUC", f"{oot['pr_auc']:.4f}", TEAL),
                ("OOT ROC-AUC", f"{oot['roc_auc']:.4f}", BLUE),
                ("OOT Brier", f"{oot['brier_score']:.4f}", ORANGE),
                ("OOT ECE", f"{oot['ece_10_bin']:.4f}", GREEN),
                ("Precision", pct(oot["precision"]), BLUE),
                ("Recall", pct(oot["recall"]), GREEN),
                ("F1", pct(oot["f1"]), TEAL),
                ("Alert rate", pct(oot["alert_rate"]), RED),
            ]
        )
    )
    story.append(Spacer(1, 6 * mm))
    story.append(
        styled_table(
            ["Measure", "Validation", "OOT", "Interpretation"],
            [
                [
                    "PR-AUC",
                    f"{validation['pr_auc']:.4f}",
                    f"{oot['pr_auc']:.4f}",
                    "ranking above baseline",
                ],
                ["Recall", pct(validation["recall"]), pct(oot["recall"]), "failure capture"],
                [
                    "Precision",
                    pct(validation["precision"]),
                    pct(oot["precision"]),
                    "true failures among alerts",
                ],
                [
                    "Alert rate",
                    pct(validation["alert_rate"]),
                    pct(oot["alert_rate"]),
                    "planner workload",
                ],
                [
                    "Expected cost / obs.",
                    f"{validation['expected_cost_per_observation']:.1f}",
                    f"{oot['expected_cost_per_observation']:.1f}",
                    "synthetic scenario",
                ],
            ],
            [38 * mm, 30 * mm, 30 * mm, 72 * mm],
            {3: ORANGE_PALE},
        )
    )
    story.append(
        callout(
            "Validation conclusion",
            "The champion generalizes directionally, but OOT workload exceeds the validation capacity cap. "
            "Promotion requires operational review rather than metric-only approval.",
            RED,
        )
    )
    end_page(story)

    # 14. Calibration and alarm quality
    story.extend(
        section_header(
            "12 • Calibration and alarm quality",
            "Probability quality and planner workload are evaluated separately",
        )
    )
    images = Table(
        [
            [
                figure("model_calibration.png", 80, 83),
                figure("oot_confusion_matrix.png", 80, 83),
            ]
        ],
        colWidths=[85 * mm, 85 * mm],
    )
    images.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(images)
    story.append(
        Table(
            [
                [
                    para(
                        f"Calibration: Brier {oot['brier_score']:.4f}; ECE {oot['ece_10_bin']:.4f}.",
                        "caption",
                    ),
                    para(
                        f"Confusion: TN {oot['true_negative']}; FP {oot['false_positive']}; "
                        f"FN {oot['false_negative']}; TP {oot['true_positive']}.",
                        "caption",
                    ),
                ]
            ],
            colWidths=[85 * mm, 85 * mm],
        )
    )
    story.append(
        metric_cards(
            [
                (
                    "Alerts/day",
                    num(metrics["monitoring"]["alarm_quality"]["alerts_per_day"], 2),
                    ORANGE,
                ),
                (
                    "Median lead",
                    f"{num(metrics['monitoring']['alarm_quality']['median_lead_time_hours'])} h",
                    TEAL,
                ),
                ("False alerts", num(metrics["monitoring"]["alarm_quality"]["false_alerts"]), RED),
                (
                    "Missed failures",
                    num(metrics["monitoring"]["alarm_quality"]["missed_failures"]),
                    BLUE,
                ),
            ]
        )
    )
    story.append(Spacer(1, 5 * mm))
    story.append(
        styled_table(
            ["Control", "Design threshold", "OOT result", "Disposition"],
            [
                ["Recall", "≥ 72% validation", pct(oot["recall"]), "passes capture objective"],
                ["Review capacity", "≤ 40% validation", pct(oot["alert_rate"]), "watch / redesign"],
                [
                    "Calibration",
                    "Brier + ECE monitored",
                    f"{oot['brier_score']:.4f} / {oot['ece_10_bin']:.4f}",
                    "acceptable synthetic result",
                ],
                [
                    "Lead time",
                    "report median",
                    f"{metrics['monitoring']['alarm_quality']['median_lead_time_hours']:.0f} h",
                    "planner context",
                ],
            ],
            [38 * mm, 47 * mm, 38 * mm, 47 * mm],
            {1: ORANGE_PALE},
        )
    )
    story.append(
        callout(
            "Alarm governance",
            "A calibrated model can still create excessive workload. Alert rate, precision, lead time and misses are monitored as operational controls.",
            ORANGE,
        )
    )
    end_page(story)

    # 15. SHAP
    story.extend(
        section_header("13 • SHAP explanations", "Global drivers become local planner reason codes")
    )
    story.append(figure("shap_global_importance.png", 170, 84))
    story.append(para("Figure 7. Mean absolute SHAP value across 700 explained rows.", "caption"))
    story.append(
        styled_table(
            ["Rank", "Reason code", "SHAP value", "Transformed value"],
            [
                [
                    row["rank"],
                    row["reason_code"],
                    f"{float(row['shap_value']):.4f}",
                    f"{float(row['transformed_value']):.3f}",
                ]
                for row in local_shap
            ],
            [20 * mm, 86 * mm, 30 * mm, 34 * mm],
        )
    )
    story.append(
        callout(
            "Local example",
            f"{local_shap[0]['shift_id']} • risk {pct(local_shap[0]['failure_probability'])} • "
            "top reasons: " + ", ".join(row["reason_code"] for row in local_shap) + ".",
            TEAL,
        )
    )
    story.extend(
        bullet(
            [
                "Global importance supports model review; local SHAP supports a specific planner conversation.",
                "Reason codes are deterministic labels layered on model features; they are not verified root causes.",
                "Correlated features can share or exchange attribution.",
                "SHAP explains the fitted base estimator; the sigmoid calibration layer is outside attribution.",
            ]
        )
    )
    end_page(story)

    # 16. Maintenance policy
    story.extend(
        section_header(
            "14 • Maintenance decision policy",
            "Risk, criticality and synthetic economics determine review priority",
        )
    )
    story.append(figure("maintenance_priority.png", 170, 84))
    story.append(para("Figure 8. Latest OOT machine priority by expected net benefit.", "caption"))
    story.append(
        styled_table(
            ["Input", "Role"],
            [
                ["Calibrated failure probability", "likelihood within 24-hour horizon"],
                ["Machine criticality", "consequence multiplier tier 1-5"],
                ["Estimated failure cost", "synthetic scenario loss"],
                ["Maintenance cost", "synthetic intervention cost"],
                ["Intervention effectiveness", "scenario avoided-loss fraction"],
            ],
            [62 * mm, 108 * mm],
        )
    )
    story.append(Spacer(1, 4 * mm))
    story.append(
        metric_cards(
            [
                (
                    "P1 reviews",
                    str(metrics["decision_support"]["recommendation_counts"]["P1"]),
                    RED,
                ),
                (
                    "Monitor",
                    str(metrics["decision_support"]["recommendation_counts"]["MONITOR"]),
                    TEAL,
                ),
                ("Execution", "NONE", ORANGE),
                ("Human gate", "TRUE", GREEN),
            ]
        )
    )
    story.append(Spacer(1, 4 * mm))
    story.append(
        styled_table(
            ["Priority", "Meaning", "Required action"],
            [
                [
                    "P1",
                    "high risk/criticality with positive expected net benefit",
                    "planner review within 8 hours",
                ],
                [
                    "P2",
                    "above threshold with positive net benefit",
                    "planner review within 24 hours",
                ],
                ["P3", "moderate risk or cost ratio", "inspect in routine planning"],
                ["MONITOR", "no favorable recommendation", "continue standard monitoring"],
            ],
            [23 * mm, 85 * mm, 62 * mm],
        )
    )
    story.append(
        callout(
            "Safety invariant",
            "The policy cannot override lockout/tagout, operating procedures, current equipment state or qualified maintenance judgment.",
            RED,
        )
    )
    end_page(story)

    # 17. Service/database/BI
    story.extend(
        section_header(
            "15 • Service, database and BI",
            "Every delivery channel consumes the same governed evidence",
        )
    )
    story.append(
        styled_table(
            ["Layer", "Deliverable", "Control"],
            [
                [
                    "FastAPI",
                    "recommendation-only endpoint, health and Prometheus metrics",
                    "human gate in response contract",
                ],
                [
                    "PostgreSQL",
                    "normalized schema and analytical views",
                    "typed keys, timestamps and decision fields",
                ],
                [
                    "Power BI PBIP",
                    "starter semantic model, DAX measures and six report pages",
                    "explicit project-start limitation",
                ],
                [
                    "Excel",
                    "14-sheet formula workbook with dashboard and planner",
                    "blue inputs, comments and formula scan",
                ],
                [
                    "PPT/PDF",
                    "executive narrative and governance evidence",
                    "results loaded from pipeline artifacts",
                ],
            ],
            [35 * mm, 82 * mm, 53 * mm],
        )
    )
    story.append(Spacer(1, 7 * mm))
    story.append(
        callout(
            "API boundary",
            "POST /v1/recommendations returns a probability, threshold, priority, reason codes and human approval fields. "
            "No write client for plant or maintenance systems exists.",
            ORANGE,
        )
    )
    story.extend(section_header("Analytical database views", "Governed consumption"))
    story.append(
        styled_table(
            ["View", "Purpose"],
            [
                ["manufacturing.vw_oee_daily", "daily OEE component and plant rollup"],
                ["manufacturing.vw_downtime_pareto", "duration/event Pareto by category"],
                ["manufacturing.vw_machine_reliability", "MTBF, MTTR and machine reliability"],
                ["manufacturing.vw_quality_copq", "FPY, scrap, rework and COPQ"],
                ["manufacturing.vw_maintenance_priority", "latest human-gated policy output"],
            ],
            [69 * mm, 101 * mm],
        )
    )
    story.extend(
        bullet(
            [
                "PBIP is a version-controlled starter; it requires validation in the current Power BI Desktop.",
                "The Excel workbook is scenario-oriented and does not replace the pipeline system of record.",
                "All business-facing artifacts preserve the synthetic-data disclaimer.",
            ]
        )
    )
    end_page(story)

    # 18. Security/threat
    story.extend(
        section_header(
            "16 • Security and threat model",
            "Controls reduce portfolio risk without claiming production hardening",
        )
    )
    story.append(
        styled_table(
            ["Threat", "Example", "Implemented / documented control"],
            [
                [
                    "Input manipulation",
                    "extreme valid sensor payload",
                    "schema bounds, model drift and gateway guidance",
                ],
                [
                    "Model substitution",
                    "modified joblib bundle",
                    "read-only mount, image immutability and hash runbook",
                ],
                [
                    "Dependency compromise",
                    "vulnerable package/action",
                    "pins, pip-audit, Dependabot, CodeQL and Trivy",
                ],
                [
                    "Credential leakage",
                    "secret committed to repository",
                    ".env example, external secret guidance and scanning",
                ],
                [
                    "Denial of service",
                    "high request volume",
                    "resource limits, HPA and rate-limit guidance",
                ],
                [
                    "Recommendation escalation",
                    "advice treated as work order",
                    "human gate and no CMMS/PLC client",
                ],
                [
                    "Monitoring evasion",
                    "missing/forged metrics",
                    "independent scrape and missing-target alert",
                ],
                [
                    "Data poisoning",
                    "shifted source distribution",
                    "contract checks, PSI and manual retraining gate",
                ],
            ],
            [38 * mm, 53 * mm, 79 * mm],
        )
    )
    story.append(Spacer(1, 5 * mm))
    story.append(
        metric_cards(
            [
                ("Unit/coverage", "35 / 95.3%", GREEN),
                ("pip-audit", "CLEAN", TEAL),
                ("CodeQL", "WORKFLOW", BLUE),
                ("Trivy", "WORKFLOW", ORANGE),
            ]
        )
    )
    story.append(Spacer(1, 5 * mm))
    story.append(
        styled_table(
            ["Secure delivery control", "Evidence"],
            [
                ["Static analysis", ".github/workflows/codeql.yml"],
                ["Dependency audit", ".github/workflows/security.yml and local pip-audit"],
                ["Container scan", "Trivy filesystem and image jobs"],
                ["Ownership", ".github/CODEOWNERS"],
                ["Dependency updates", ".github/dependabot.yml"],
                ["Protected main", "docs/branch_protection_guide.md"],
            ],
            [58 * mm, 112 * mm],
        )
    )
    story.append(
        callout(
            "Out of scope",
            "Plant segmentation, IAM integration, enterprise secrets management, signed telemetry and production CMMS connectivity remain deployment responsibilities.",
            RED,
        )
    )
    end_page(story)

    # 19. Monitoring/incident
    story.extend(
        section_header(
            "17 • Monitoring and incident response",
            "Data quality, drift, model quality and workload have separate controls",
        )
    )
    story.append(figure("feature_drift.png", 170, 80))
    story.append(para("Figure 9. PSI comparing model-fit and OOT feature populations.", "caption"))
    story.append(
        metric_cards(
            [
                (
                    "Data checks",
                    f"{metrics['monitoring']['data_quality_checks_passed']}/{metrics['monitoring']['data_quality_checks_total']}",
                    GREEN,
                ),
                ("Action PSI", str(metrics["monitoring"]["features_at_action_level"]), RED),
                ("Max PSI", f"{metrics['monitoring']['max_psi']:.3f}", ORANGE),
                ("OOT alert rate", pct(oot["alert_rate"]), BLUE),
            ]
        )
    )
    story.append(Spacer(1, 4 * mm))
    story.append(
        styled_table(
            ["Signal class", "Examples", "First response"],
            [
                [
                    "Data quality",
                    "missing/invalid/range violations",
                    "quarantine batch; verify source contract",
                ],
                ["Data drift", "PSI action level", "segment by time/source; do not auto-retrain"],
                [
                    "Model quality",
                    "PR-AUC, Brier, ECE, recall",
                    "compare to validation and business tolerance",
                ],
                [
                    "Alarm quality",
                    "precision, alert rate, lead time, misses",
                    "review threshold and planner capacity",
                ],
                [
                    "Service health",
                    "latency, errors, missing scrape",
                    "fail safe; investigate API/dependency",
                ],
            ],
            [36 * mm, 68 * mm, 66 * mm],
        )
    )
    story.append(
        callout(
            "Incident sequence",
            "Detect → classify → contain → preserve evidence → assess decision impact → approve recovery → retrospective. "
            "Prediction/recommendation outages fail closed to manual planning.",
            TEAL,
        )
    )
    end_page(story)

    # 20. Risks/limitations
    story.extend(
        section_header(
            "18 • Risk register and limitations",
            "Residual risk remains high for synthetic-to-real transfer",
        )
    )
    risks = [
        ["R-01", "Synthetic-to-real transfer gap", "High", "High", "High"],
        ["R-02", "Temporal leakage", "Medium", "High", "Low"],
        ["R-03", "Poor probability calibration", "Medium", "High", "Medium"],
        ["R-04", "Alert overload", "High", "Medium", "Medium"],
        ["R-05", "Seasonal/source drift", "High", "Medium", "Medium"],
        ["R-06", "Control/specification confusion", "Medium", "High", "Low"],
        ["R-07", "SHAP over-interpretation", "Medium", "Medium", "Medium"],
        ["R-08", "Cost assumption sensitivity", "High", "Medium", "Medium"],
        ["R-09", "Unauthorized operational integration", "Low", "Critical", "Low"],
        ["R-10", "Dependency/container vulnerability", "Medium", "High", "Medium"],
        ["R-11", "Model bundle tampering", "Low", "High", "Medium"],
        ["R-12", "Missing/malformed sensor data", "Medium", "Medium", "Medium"],
    ]
    story.append(
        styled_table(
            ["ID", "Risk", "Likelihood", "Impact", "Residual"],
            risks,
            [18 * mm, 75 * mm, 26 * mm, 25 * mm, 26 * mm],
            {0: ORANGE_PALE, 3: ORANGE_PALE},
        )
    )
    story.append(Spacer(1, 5 * mm))
    story.append(
        callout(
            "Primary limitation",
            "Synthetic performance cannot establish real-plant effectiveness. Real adoption requires shadow data, verified labels, "
            "plant-specific cost and safety owners, and a new untouched acceptance window.",
            RED,
        )
    )
    story.extend(section_header("Known validation limitations", "Items that block overclaiming"))
    story.extend(
        bullet(
            [
                f"OOT alert rate {pct(oot['alert_rate'])} exceeds the 40% validation review-capacity cap.",
                "Time/cumulative variables generate large PSI across a later window and require redesign review.",
                "Failure labels are synthetic and cleaner than real maintenance histories.",
                "Synthetic cost units are useful for ranking sensitivity, not finance approval.",
                "No causal inference or counterfactual maintenance-effect estimate is claimed.",
            ]
        )
    )
    end_page(story)

    # 21. Crosswalk
    story.extend(
        section_header(
            "19 • Reference crosswalk",
            "Official sources are design references—not compliance claims",
        )
    )
    crosswalk = [
        [
            "ISO 22400-2",
            "Manufacturing KPI formulas",
            "OEE documentation",
            "No certification/conformance",
        ],
        [
            "ISO 13374-2",
            "Condition-monitoring processing",
            "Staged architecture",
            "Illustrative only",
        ],
        [
            "ISO 13374-4",
            "Health/advisory presentation",
            "Dashboard/recommendation contract",
            "No presentation conformance",
        ],
        ["NIST SPC", "Variables/attributes charts", "X-bar/R, I-MR, p and u", "Synthetic process"],
        ["NIST capability", "Capability/specification", "Cp/Cpk/Pp/Ppk", "No process acceptance"],
        [
            "NIST AI RMF 1.0",
            "Govern/map/measure/manage",
            "Model card, monitoring and risks",
            "Voluntary reference",
        ],
        ["NIST SSDF 1.1", "Secure development", "CI/tests/security scans", "No SSDF audit"],
        ["GitHub CodeQL", "Code scanning", "codeql.yml", "Execution/config dependent"],
        [
            "GitHub dependency review",
            "Supply-chain changes",
            "pip-audit/Dependabot",
            "No complete risk guarantee",
        ],
        ["Prometheus rules", "Operational alerts", "rules + runbook", "Thresholds need tuning"],
    ]
    story.append(
        styled_table(
            ["Reference", "Concept", "Project evidence", "Claim boundary"],
            crosswalk,
            [38 * mm, 43 * mm, 51 * mm, 38 * mm],
        )
    )
    story.append(Spacer(1, 5 * mm))
    story.append(
        styled_table(
            ["Official URL", "Use"],
            [
                ["https://www.iso.org/standard/54497.html", "ISO 22400-2"],
                ["https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc3.htm", "SPC taxonomy"],
                ["https://www.itl.nist.gov/div898/handbook/pmc/section1/pmc16.htm", "Capability"],
                ["https://www.nist.gov/itl/ai-risk-management-framework", "AI risk"],
                ["https://csrc.nist.gov/pubs/sp/800/218/final", "SSDF"],
                [
                    "https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/",
                    "Alert rules",
                ],
            ],
            [116 * mm, 54 * mm],
        )
    )
    story.append(
        callout(
            "Crosswalk status",
            "Versions and status must be rechecked before production use. The crosswalk documents design intent; it does not establish compliance.",
            ORANGE,
        )
    )
    end_page(story)

    # 22. Delivery matrix
    story.extend(
        section_header(
            "20 • Delivery matrix", "One evidence chain across code, analytics and communication"
        )
    )
    story.append(
        styled_table(
            ["Delivery", "Location", "Review question"],
            [
                ["Python pipeline", "src/manufacturing_ct/", "Can the result be reproduced?"],
                [
                    "Tests and QA",
                    "tests/ and .github/workflows/",
                    "Are controls automated and covered?",
                ],
                ["SQL", "sql/", "Can analytical records be governed and queried?"],
                ["Power BI PBIP", "powerbi/", "Can decision consumers explore the model?"],
                ["Excel", "deliverables/excel/", "Can assumptions and priorities be reviewed?"],
                [
                    "Executive deck",
                    "deliverables/presentation/",
                    "Can leaders understand the decision?",
                ],
                [
                    "Governance PDF",
                    "deliverables/report/",
                    "Can reviewers trace claims to evidence?",
                ],
                ["Documentation", "docs/", "Are contracts, ADRs and runbooks explicit?"],
                ["Portfolio copy", "docs/portfolio/", "Are public claims bounded and accurate?"],
                [
                    "Infrastructure",
                    "Dockerfile, compose, k8s/, monitoring/",
                    "Can operability be inspected?",
                ],
            ],
            [35 * mm, 60 * mm, 75 * mm],
        )
    )
    story.append(Spacer(1, 8 * mm))
    story.append(
        metric_cards(
            [
                ("Pipeline rows", num(metrics["dataset"]["production_shift_rows"]), ORANGE),
                ("Tests", "35", GREEN),
                ("Coverage", "95.30%", TEAL),
                ("Human gate", "ENFORCED", RED),
            ]
        )
    )
    story.append(Spacer(1, 7 * mm))
    story.append(
        callout(
            "Final governance position",
            "The project demonstrates an end-to-end manufacturing analytics and predictive-maintenance decision system "
            "while preserving synthetic-data, human-approval and non-compliance boundaries.",
            TEAL,
        )
    )
    story.extend(section_header("Proposed next step", "If real data becomes available"))
    story.extend(
        bullet(
            [
                "Run in shadow mode with plant-specific data contracts and verified failure labels.",
                "Rebuild temporal splits, recalibrate synthetic economics and define planner capacity.",
                "Conduct safety, cybersecurity, privacy and architecture reviews with accountable owners.",
                "Approve any integration only after monitored acceptance criteria and rollback plans.",
            ]
        )
    )

    document.build(story)
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    build()
