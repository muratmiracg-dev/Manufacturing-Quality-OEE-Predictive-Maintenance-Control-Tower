# LinkedIn Post - English

🏭 New portfolio project: Manufacturing Quality, OEE & Predictive Maintenance
Control Tower

What happens when production performance, quality engineering and predictive
maintenance are designed as one decision-support system rather than separate
dashboards?

I built a fully reproducible platform using deterministic synthetic data from
4 lines, 12 machines, 4 products and 3 shifts.

Key results from the actual pipeline:

✅ 19,692 production shifts and 98,460 CTQ measurements  
✅ 85.27% plant OEE: 98.36% availability, 90.99% performance, 95.27% quality  
✅ X-bar/R, I-MR, p and u SPC charts with documented alarm rules  
✅ Cp, Cpk, Pp and Ppk with control/specification limits kept separate  
✅ Calibrated Random Forest champion: 0.7489 OOT ROC-AUC and 0.3887 PR-AUC  
✅ 73.51% OOT recall at a validation-selected, capacity-constrained threshold  
✅ Global and local SHAP explanations converted into maintenance reason codes  
✅ 35 tests and 95.30% coverage  

The recommendation policy combines risk, machine criticality, estimated
failure cost and maintenance cost. It remains deliberately human-in-the-loop:
no work orders, machine stops or maintenance approvals are automated.

The repository also includes FastAPI, PostgreSQL views, a PBIP starter,
formula-driven Excel, an executive deck, a detailed governance PDF, Docker,
Kubernetes, Prometheus, Grafana, CodeQL, pip-audit, Trivy and Dependabot.

🔗 Repository:
https://github.com/muratmiracg-dev/Manufacturing-Quality-OEE-Predictive-Maintenance-Control-Tower

#ManufacturingAnalytics #OEE #PredictiveMaintenance #SPC #QualityEngineering
#MachineLearning #SHAP #PowerBI #MLOps #Industry40

