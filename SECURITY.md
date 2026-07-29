# Security Policy

## Supported version

Security fixes are applied to the latest `main` revision.

## Reporting

Do not open a public issue for a suspected vulnerability. Use GitHub's private
vulnerability reporting feature when available. Include the affected version,
reproduction steps, expected impact and any safe mitigation.

## Security boundaries

- The service is recommendation-only and has no PLC, SCADA or CMMS write path.
- API input is schema validated and rejects unknown fields.
- Containers run as a non-root user with a read-only root filesystem in
  Kubernetes.
- Secrets are externalized; sample values are never production credentials.
- CodeQL, pip-audit and Trivy run in GitHub Actions.
- Dependabot tracks Python, Docker and GitHub Actions dependencies.

## Response targets

| Severity | Initial triage | Target remediation |
|---|---:|---:|
| Critical | 1 business day | 3 business days |
| High | 2 business days | 10 business days |
| Medium | 5 business days | 30 days |
| Low | 10 business days | Planned release |

These are portfolio operating targets, not contractual service levels.

