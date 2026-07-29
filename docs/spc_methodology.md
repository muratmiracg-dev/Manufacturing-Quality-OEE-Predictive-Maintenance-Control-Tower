# SPC and Process Capability Methodology

## Chart selection

| Data pattern | Selected chart | Why |
|---|---|---|
| Five CTQ measurements in a rational subgroup | X-bar/R | Fixed subgroup size `n=5`; monitors location and within-subgroup spread |
| One roughness observation per shift | I-MR | No rational subgroup is available |
| Defective units from variable lot sizes | p | Binomial proportion with varying `n` |
| Multiple defects across variable unit counts | u | Poisson-style defects per unit with varying exposure |
| Fixed lot defective count | np not selected | Generated lot size varies |
| Fixed opportunity defect count | c not selected | Generated units/opportunities vary |

## Baseline and forward use

Control parameters are fit only on observations before `validation_start`.
They are then frozen and applied to later validation and OOT observations.
This prevents future process behavior from changing historical limits.

## Alarm rules

The implementation evaluates:

1. one point beyond 3 sigma;
2. two of three consecutive points beyond 2 sigma on the same side;
3. four of five consecutive points beyond 1 sigma on the same side;
4. eight consecutive points on one side of the center line.

An alarm is evidence for investigation, not proof of a defect or an instruction
to change the process. Autocorrelation and rational subgroup quality must be
reviewed before operational use.

## Control limits are not specification limits

- Control limits are estimated from baseline process variation.
- Specification limits are product-engineering requirements.
- A statistically stable process can still be incapable.
- An unstable process should not be treated as capable merely because most
  measurements are within specification.

## Capability

- Cp and Cpk use within-subgroup sigma estimated from `R-bar / d2`.
- Pp and Ppk use the overall sample standard deviation.
- Cpk/Ppk include centering; Cp/Pp measure potential spread only.
- The committed values are synthetic snapshots, not supplier or process
  acceptance evidence.

The chart taxonomy and capability distinction follow the
[NIST/SEMATECH handbook](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc3.htm)
and its [process capability section](https://www.itl.nist.gov/div898/handbook/pmc/section1/pmc16.htm).

