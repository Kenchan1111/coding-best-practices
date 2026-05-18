---
family: Q
name: numerical_precision
severity: medium
languages: [python, javascript, typescript]
triggers:
  - statistical_method
  - numerical_approximation
  - digest_length
  - sparse_data_screening
patterns_matched:
  - 'student_t_cdf clamps tail to 1.0'
  - 'KM quantile continuity undocumented'
  - 'digest prefix used where SHA256 promised'
  - 'ND fraction guard missing'
  - 'seasonal trend run on too few observations'
fix_pattern: document_and_test_numerical_convention
gstack_integration: review_domain_numerics
---

# Q - Numerical precision and statistical conventions

## When this check applies

Use this check when code implements statistical methods, approximations, quantiles, digest lengths, sparse-data screening, nondetect handling, or defensibility labels.

## Avoid

```python
if t > 12:
    return 1.0
```

For low degrees of freedom, the tail may still be material.

```python
leaf = sha256(payload).hexdigest()[:12]
```

This is not equivalent to "SHA256" if the spec promises full-strength leaves.

## Required review steps

1. Identify numerical approximations and document their valid domain.
2. Test boundary cases, low sample sizes, low degrees of freedom, and both tails.
3. Check whether conventions such as left/right continuity are stated and tested.
4. Ensure digest truncation is named honestly and not described as full SHA256.
5. Require warnings when data is too sparse, too censored, or otherwise not defensible.

## Preferred fixes

```python
if dof <= 1 and abs(t) > 12:
    warn("student-t approximation is unreliable in heavy tail")
```

```python
leaf = sha256(payload).hexdigest()
```

or rename the field to `digest_prefix_12` when truncation is intentional.

## Fix-first classification

ASK by default. Numerical conventions and defensibility thresholds are domain decisions.

AUTO-FIX only for naming honesty, missing warnings, and tests around already-documented conventions.

## Sources catalogue

- Q1: `_student_t_cdf` capped at t=12 and returned 1.0.
- Q2: KM CDF continuity shifted quantiles.
- Q3: Merkle leaves used 48-bit digest prefixes while spec said SHA256.
- Q4: nondetect fraction guard was missing.
- Q5: seasonal trend looked defensible on too-sparse data.
- gstack relation: domain-specific extension beyond generic performance or API review.
