# Beta Feedback Lifecycle Split Plan

## Purpose

The beta feedback lifecycle must move forward as small L2 goals. No slice should mix telemetry collection, export, release packaging, issue submission, provider architecture, and rollback policy in one PR.

## Slice Order

1. Privacy-safe local feedback export preview.
2. Feedback issue templates.
3. Offline beta evaluation dataset and tooling.
4. Beta channel configuration.
5. Release packaging and verification.
6. Recall and rollback documentation.

## Proposed L2 Slices

### 1. Privacy-safe local feedback export preview

- Issue title: `[Goal] Add privacy-safe local feedback export preview`
- Allowed scope: local export module or command, redaction rules, no-write preview path, focused unit tests, minimal command docs.
- Forbidden scope: telemetry daemon, GitHub issue submission, beta release workflow, version bump, provider registry.
- Dependencies: none.
- Required gates: CI and privacy review.
- Manual owner decision: required before writing any export artifact outside a preview.

### 2. Feedback issue templates

- Issue title: `[Goal] Add beta feedback issue templates`
- Allowed scope: GitHub issue templates for bug reports, usability notes, and opt-in evidence attachments; template validation tests if templates become managed files.
- Forbidden scope: automatic issue creation, telemetry ingestion, release workflow, user data export implementation.
- Dependencies: slice 1 should define the redacted artifact shape first.
- Required gates: CI and privacy review.
- Manual owner decision: not required unless templates request new personal data fields.

### 3. Offline beta evaluation dataset and tooling

- Issue title: `[Goal] Add offline beta feedback evaluation fixtures`
- Allowed scope: synthetic or redacted local fixtures, parser tests, scoring/checklist script for feedback quality, docs for fixture format.
- Forbidden scope: real user data, network upload, analytics service, model/provider selection rewrite.
- Dependencies: slices 1 and 2 define export and issue shapes.
- Required gates: CI and privacy review.
- Manual owner decision: required before adding any non-synthetic example.

### 4. Beta channel configuration

- Issue title: `[Goal] Define beta channel configuration`
- Allowed scope: config schema, local defaults, validation tests, docs for enabling/disabling beta feedback features.
- Forbidden scope: production rollout, release publishing, telemetry collection, secrets or account configuration.
- Dependencies: slices 1 through 3 clarify data shape and expected workflow.
- Required gates: CI.
- Manual owner decision: required for default-on behavior; default should remain off until approved.

### 5. Release packaging and verification

- Issue title: `[Goal] Package beta feedback workflow for release verification`
- Allowed scope: distribution packaging checks, install verification, changelog/release notes draft, smoke-test instructions.
- Forbidden scope: version bump without owner approval, production release, beta channel policy changes.
- Dependencies: slices 1 through 4.
- Required gates: CI and package verification.
- Manual owner decision: required before version bump or publication.

### 6. Recall and rollback documentation

- Issue title: `[Goal] Document beta feedback recall and rollback`
- Allowed scope: operator checklist, rollback steps, artifact deletion guidance, user communication template, verification checklist.
- Forbidden scope: implementing deletion automation, external account operations, policy changes outside this repository.
- Dependencies: slices 1 through 5 determine actual artifacts and release path.
- Required gates: docs review.
- Manual owner decision: required before using the recall process for real users.

## Dependency Notes

Slice 1 is the next implementation PR because it creates the smallest useful artifact boundary. Slices 2 and 3 should not start until the redacted export shape exists. Release and rollback work should remain last because they depend on the actual beta workflow surface.

## Review Rule

If a proposed PR touches more than one slice, it should be split unless the second slice is a test-only or docs-only adjustment required to validate the first slice.
