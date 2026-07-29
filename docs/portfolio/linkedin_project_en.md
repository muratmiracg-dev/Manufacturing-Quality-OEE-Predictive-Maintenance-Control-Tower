# LinkedIn Project Description - English

Developed an end-to-end Manufacturing Quality, OEE & Predictive Maintenance
Control Tower using deterministic, fully synthetic plant data across 4
production lines, 12 machines, 4 products and 3 shifts.

The platform integrates OEE decomposition, planned/unplanned downtime Pareto,
MTBF/MTTR, scrap, rework, first-pass yield, Cost of Poor Quality, SPC and
process capability. Data-appropriate X-bar/R, I-MR, p and u control charts were
implemented with documented alarm rules, frozen development baselines and a
clear separation between control limits and engineering specification limits.

A leakage-controlled 24-hour failure prediction pipeline compares calibrated
Random Forest and Logistic Regression candidates using chronological
development, validation and out-of-time test periods. The selected champion
achieved 0.7489 ROC-AUC and 0.3887 PR-AUC on OOT data, versus a 0.1543 no-skill
PR baseline, with 0.1137 Brier score and 73.51% recall at the
capacity-constrained threshold.

Global/local SHAP explanations feed traceable maintenance reason codes. A
recommendation-only policy combines failure probability, machine criticality,
estimated failure cost, maintenance cost and intervention effectiveness while
keeping human approval mandatory.

Built with Python, scikit-learn, SHAP, FastAPI, PostgreSQL, Power BI Project,
Excel, Docker, Kubernetes, Prometheus, Grafana and GitHub Actions. The project
includes 35 tests with 95.30% coverage, CodeQL, pip-audit, Trivy, Dependabot,
model governance, threat modeling, incident response and a detailed reference
crosswalk without claiming standards compliance.

