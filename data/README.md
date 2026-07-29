# Synthetic data

`data/sample/` contains inspectable samples and complete master data. The full
22 MB generated dataset is intentionally excluded from Git because it is
recreated byte-for-byte from `configs/base.yaml` and seed `20260729`:

```bash
python -m manufacturing_ct.pipeline --config configs/base.yaml
```

All entities, sensor readings, failures, costs and work events are artificial.
No production, employee, vendor or customer data was used.

