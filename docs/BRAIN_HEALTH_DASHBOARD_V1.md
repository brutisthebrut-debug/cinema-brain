# Brain Health Dashboard v1

Brain Health Dashboard v1 is a dependency-free, read-only Cinema Brain Studio surface over the verified `recommendation_audit_v1.json` contract. It exists to make one immutable recommendation release understandable without creating a second source of ranking, audit, or outcome logic.

## Input

The dashboard accepts one local JSON file:

- `recommendation_audit_v1.json`

It rejects the file unless the record declares:

- audit version `1.0.0`;
- audit type `recommendation_release_audit`;
- status `verified_read_only`;
- verified input integrity;
- an eligible release with zero failed gates;
- the required Audit v1 collections;
- the pre-outcome `awaiting_outcome` state.

Release package verification remains owned by Recommendation Audit v1. The dashboard does not reproduce cryptographic or semantic audit logic.

## Visible health record

The surface renders only fields already present in Audit v1:

- release and audit identity;
- source revision and prediction snapshot digest;
- release-gate results;
- candidate and release accounting;
- Brain health ratios;
- raw-to-balanced slate movement;
- explanation-evidence coverage;
- abstention counts and reason frequencies;
- the frozen release's explicit outcome state.

Percentage conversion, labels, and responsive layout are presentation only. They do not change or reinterpret engine results.

## Read-only and privacy boundary

The dashboard:

- reads a user-selected local file;
- performs no network requests;
- loads no third-party dependencies;
- writes no local or session storage;
- provides no editing, export, ranking, release, or outcome controls;
- does not modify the imported file;
- escapes imported text before rendering it into the page.

The production workflow copies the static dashboard into the same private artifact bundle as the verified audit. The artifact is retained under the workflow's existing private 30-day policy. The interface is not deployed publicly.

## Operation

1. Run `.github/workflows/unwatched-horror-ranking.yml`.
2. Download and unzip the private recommendation artifact.
3. Open `brain_health_dashboard_v1.html` in a browser.
4. Select `recommendation_audit_v1.json` from the same bundle.
5. Confirm the release ID before using the view for diagnosis or handoff.

## Regression contract

Required coverage proves that the dashboard:

- contains every stable Audit v1 section;
- rejects wrong-version, unverified, failed-gate, or post-outcome records;
- remains dependency-free and mobile-ready;
- has no network or browser-storage behavior;
- escapes text from the imported audit.

## Handoff

After Dashboard v1 is merged and CI is green, stop UI work. The next implementation is post-watch outcome capture keyed by `release_id`, preserving the manifest, prediction snapshot, audit, and dashboard input unchanged. That outcome contract may calculate Recommendation Trust and prediction error; Dashboard v1 may not.
