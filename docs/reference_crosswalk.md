# Reference Crosswalk

This is a design-reference crosswalk, **not** a claim of certification,
conformance or regulatory compliance.

| Official reference | Relevant concept | Project evidence | Claim boundary |
|---|---|---|---|
| [ISO 22400-2](https://www.iso.org/standard/54497.html) | Manufacturing operations KPI definitions and formula elements | OEE component formulas, units and ratio-of-sums documentation | No ISO certification or conformance assessment |
| [ISO 13374-2](https://www.iso.org/standard/36645.html) | Condition-monitoring data processing and information models | Staged data, analytics, model and policy layers | Architecture is illustrative, not assessed for interoperability |
| [ISO 13374-4](https://www.iso.org/standard/54933.html) | Presentation of health, advisory and recommendation information | Dashboard/report outputs and recommendation response contract | No claim of conformant CM&D presentation |
| [NIST/SEMATECH SPC handbook](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc3.htm) | Variables and attributes control charts | X-bar/R, I-MR, p and u implementations | Synthetic process; no production control approval |
| [NIST process capability](https://www.itl.nist.gov/div898/handbook/pmc/section1/pmc16.htm) | Capability compared with specification limits | Cp/Cpk/Pp/Ppk and explicit control/spec separation | No process acceptance claim |
| [NIST AI RMF 1.0](https://www.nist.gov/itl/ai-risk-management-framework) | Govern, map, measure and manage AI risk | Model card, validation, monitoring, risk register and human oversight | Voluntary reference; no NIST endorsement |
| [NIST SSDF 1.1](https://csrc.nist.gov/pubs/sp/800/218/final) | Secure development practices | CI, tests, review ownership, CodeQL, dependency and image scans | Partial project mapping, not an SSDF audit |
| [GitHub CodeQL](https://docs.github.com/code-security/code-scanning/introduction-to-code-scanning/about-code-scanning-with-codeql) | Automated code vulnerability analysis | `codeql.yml` | Scan coverage depends on GitHub execution and configuration |
| [GitHub dependency review](https://docs.github.com/code-security/supply-chain-security/understanding-your-software-supply-chain/about-dependency-review) | Detect risky dependency changes | pip-audit and Dependabot; optional dependency-review rule | No guarantee all supply-chain risk is detected |
| [Prometheus alerting rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/) | Rule-based operational alerts | Prometheus rules and runbook | Demo thresholds require production tuning |

Version and status should be rechecked before production use. In particular,
NIST notes that AI RMF 1.0 is under revision as of the project's publication
date.

