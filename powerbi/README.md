# Power BI Project starter

This source-control-friendly PBIP starter follows Microsoft's documented PBIP
layout: a `.pbip` shortcut, PBIR `definition.pbir` report pointer and semantic
model `definition.pbism` plus `model.bim`.

## Open and refresh

1. Start PostgreSQL with `docker compose up postgres`.
2. Generate and load the synthetic data:

   ```bash
   python -m manufacturing_ct.pipeline --config configs/base.yaml
   python scripts/load_postgres.py --replace
   ```

3. Open `ManufacturingControlTower.pbip` in a current Power BI Desktop version.
4. Confirm the PostgreSQL host/database credentials.
5. Refresh and save the project before adding visuals.

The report contains six named 1920x1080 starter pages and a registered
manufacturing theme. Use the visual blueprint in
[`docs/powerbi_dashboard_spec.md`](../docs/powerbi_dashboard_spec.md).

Power BI Desktop Projects remain a Microsoft preview capability at the time of
publication; validate the project with the target Desktop build before release.
Official overview:
https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview

