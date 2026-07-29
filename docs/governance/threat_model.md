# Threat Model

## Assets

- model bundle and threshold;
- recommendation integrity;
- synthetic data lineage and metric artifacts;
- API availability;
- PostgreSQL and monitoring credentials.

## Actors and threats

| Threat | Example | Mitigation |
|---|---|---|
| Input manipulation | Extreme but syntactically valid sensor payload | Strict bounds, rate limiting at gateway, drift and anomaly review |
| Model substitution | Modified joblib bundle | Immutable image, read-only filesystem, artifact hash and controlled release |
| Dependency compromise | Malicious or vulnerable package/action | Pinning, pip-audit, Dependabot, CodeQL, Trivy |
| Credential leakage | Secret committed to repository | External secrets, `.env.example`, secret scanning |
| Denial of service | High request volume | HPA, resource limits, gateway rate limits, graceful 503 |
| Recommendation escalation | Consumer treats advice as work order | Human approval fields, no CMMS/PLC write client, clear contract |
| Monitoring evasion | Disabled or forged metrics | Independent scrape, access control and alert on missing targets |
| Data poisoning | Shifted sensor/source distributions | Contract checks, PSI, signed batches, manual retraining gate |

## Out of scope

The repository does not implement plant network segmentation, PLC security,
identity-provider integration, enterprise secrets management or a production
CMMS connector. Those controls remain deployment responsibilities.

