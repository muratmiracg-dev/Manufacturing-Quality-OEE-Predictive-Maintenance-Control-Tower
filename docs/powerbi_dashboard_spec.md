# Power BI Dashboard Specification

## Visual language

- Canvas: 1920 x 1080.
- Background: warm industrial cream `#F5F2EA`.
- Primary ink: `#101820`; secondary ink: `#334155`.
- Safety orange `#FF6B00` for attention and loss.
- Teal `#00A6A6` for process baselines.
- Green `#2DBE8C` for stable/good; red `#E63946` for action.
- Use flat industrial geometry, disciplined spacing and minimal chrome.

## Page blueprint

| Page | Decision question | Primary visuals |
|---|---|---|
| 01 Executive Overview | Where is plant performance and risk concentrated? | OEE decomposition, loss waterfall, latest risk tier, 12-month trend |
| 02 OEE Performance | Which component and line drives the gap? | Line trend, component variance, machine heatmap, shift matrix |
| 03 Downtime & Reliability | What fails, where, and for how long? | Pareto, MTBF/MTTR scatter, failure-mode trend, event table |
| 04 Quality & SPC | Is the process stable and capable? | X-bar/R, I-MR, p/u, Cpk/Ppk comparison, alarm table |
| 05 Predictive Maintenance | Which machines should planners review? | Probability/threshold, priority table, SHAP reasons, cost-risk comparison |
| 06 Model Monitoring | Can the score still be trusted? | PR/ROC, calibration, confusion matrix, PSI, alarm burden |

## Required interactions

- Slicers: date, line, machine, product and shift.
- Cross-filtering only within the same analytical grain.
- Tooltip must show numerator and denominator for OEE percentages.
- Control and specification limits must use different labels and line styles.
- Every maintenance visual must show `Human approval required`.
- Model page must show the OOT period and threshold source.

## Acceptance checks

- Reconcile dashboard OEE with `pipeline_metrics.json` to four decimals.
- Reconcile total units, COPQ, failure count and recommendation counts.
- Confirm the theme, page order and date sorting.
- Verify no visual implies autonomous machine or work-order control.

