# Interview Story - English

## 90-second version

I wanted to show that manufacturing analytics is more than an OEE dashboard, so
I designed a control tower that links production loss, process stability and
failure risk to a human maintenance decision.

The first challenge was data. I built a deterministic simulator for four lines
and twelve machines, with shift output, planned and unplanned stops, CTQ
subgroups, sensor conditions and failure events. Every published number can be
recreated from one seed.

The second challenge was methodological integrity. OEE uses ratio-of-sums,
control limits are separated from specifications, and X-bar/R, I-MR, p and u
charts are selected according to the actual data structure. For predictive
maintenance, I used chronological model-fit, calibration, validation and
out-of-time periods with 24-hour purge gaps. The Random Forest champion reached
0.7489 ROC-AUC and 0.3887 PR-AUC on OOT data. I did not hide the trade-off: at
73.51% recall the OOT alarm rate was 43.11%, so the monitoring runbook treats
review capacity as an operational constraint.

Finally, SHAP drivers feed a cost-risk policy, but the service stays
recommendation-only and requires human approval. The platform includes
FastAPI, PostgreSQL, Power BI, Excel, containers, monitoring and 35 tests with
95.30% coverage.

## Likely follow-up: Why not optimize accuracy?

The event rate is 15.43%, so accuracy can reward a model that rarely alerts. I
prioritized PR-AUC, calibration, recall, alarm burden and asymmetric operating
cost instead.

## Likely follow-up: What would change for a real plant?

I would run source-system and MSA reviews, redefine rational subgroups with
process engineers, perform a shadow deployment, validate by asset family,
calibrate on real outcomes, set planner-capacity thresholds, integrate
enterprise identity and secrets, and preserve the no-autonomous-action boundary
until a separate safety assessment approved any change.

