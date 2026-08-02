# Golden Review Operations

This workflow removes hand-authored JSON from benchmark review while preserving explicit human control.

## 1. Generate the bounded real-data review

```bash
python -m cinema_brain --db cinema_brain.db sample-review \
  --limit 10 \
  --output reports/sample_review.json
```

## 2. Generate the review worksheet

```bash
python -m cinema_brain golden-review-template \
  --benchmark config/golden_horror_v1.json \
  --sample reports/sample_review.json \
  --output reports/golden_review.csv
```

Open the CSV and complete only `decision` and `reason`.

Allowed decisions:
- `approved`
- `rejected`
- `quarantined`

Blank rows remain undecided and are not included in the packet.

## 3. Compile the auditable decision packet

```bash
python -m cinema_brain golden-review-compile \
  --benchmark config/golden_horror_v1.json \
  --template reports/golden_review.csv \
  --reviewer Daniel \
  --output reports/golden_review_decisions.json
```

The compiler recalculates identity status from the provider title and year. Editing `identity_exact` in the CSV cannot bypass the exact-match requirement.

## 4. Promote approved records

```bash
python -m cinema_brain golden-promote \
  --benchmark config/golden_horror_v1.json \
  --decisions reports/golden_review_decisions.json \
  --next-version horror-identity-v1.1 \
  --output config/golden_horror_v1.1.json
```

Promotion remains a separate explicit operation. Rejected and quarantined records are preserved in the review packet but never promoted.

## Safety rules

- The worksheet contains provider evidence, not trusted truth.
- Every completed decision requires a reason.
- Only exact accepted-title and release-year matches can be approved.
- The decision packet remains bound to the benchmark version reviewed.
- Generated benchmark changes must be inspected in a pull request before merge.
