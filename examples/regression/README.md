# Six frozen synthetic regression examples

These are complete, offline runnable HTML source pages for six synthetic capability-test questions. They are regression records, including same-task revisions, not six unfamiliar first submissions. They represent no real organization. The review scope and per-case results are recorded in [validation](../../docs/validation.md).

| Question | Frozen variant | Local page | Static mirror |
|---|---|---|---|
| [Intercity delivery scheduling](intercity-delivery-scheduling/README.md) | `B01-c3r2` | [Open page](intercity-delivery-scheduling/artifact.html) | [Pages mirror](../../docs/regression/intercity-delivery-scheduling.html) |
| [Factorial outreach experiment](factorial-outreach-experiment/README.md) | `B02-c3` | [Open page](factorial-outreach-experiment/artifact.html) | [Pages mirror](../../docs/regression/factorial-outreach-experiment.html) |
| [Perishable inventory expiry](perishable-inventory-expiry/README.md) | `B03-c3r1` | [Open page](perishable-inventory-expiry/artifact.html) | [Pages mirror](../../docs/regression/perishable-inventory-expiry.html) |
| [Recruitment waiting and workload](recruitment-waiting-load/README.md) | `B04-c3r1` | [Open page](recruitment-waiting-load/artifact.html) | [Pages mirror](../../docs/regression/recruitment-waiting-load.html) |
| [Service error budget and latency](service-error-budget-latency/README.md) | `B05-c3r1` | [Open page](service-error-budget-latency/artifact.html) | [Pages mirror](../../docs/regression/service-error-budget-latency.html) |
| [Venue booking and occupancy capacity](venue-booking-capacity/README.md) | `B06-c3` | [Open page](venue-booking-capacity/artifact.html) | [Pages mirror](../../docs/regression/venue-booking-capacity.html) |

Clone or download the repository and open any `artifact.html` directly in a desktop browser. No install, server, producer, or network dependency is needed. The mirrors under `docs/regression/` are served by GitHub Pages.

Each folder includes original `input/brief.md` and `input/data.json`, frozen `computed.json`, a concise README, and a `provenance.json` hash manifest. Only the exact first-party ChartMotion license header and HTML line endings are adjusted; input and computed bytes are preserved. Third-party notices are unchanged.

Run `python scripts/sync_regression_examples.py` from the repository root to verify bundled provenance hashes and input bytes, then copy the six frozen pages to `docs/regression/`. This script does not regenerate business data or execute a producer. These fixed examples do not promise a general-purpose generator for new problems.

The package smoke test opens each default desktop page once. It does not replace the independent interaction and visual review. Publication changes only the exact license header and line endings described in each provenance record.
