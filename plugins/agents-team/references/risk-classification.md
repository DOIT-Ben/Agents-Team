# Risk Classification

## L1

All must hold: local, reversible, no data/API/schema/state/auth/paid-provider/production/core-flow changes. Direct implementation and focused verification are allowed; a separate Issue is optional.

## L2

Any user-visible feature, cross-module change, compatible API addition, retry/upload/download change, or work needing browser E2E. Requires Goal Issue, PR, and independent QA.

## L3

Any data migration, destructive operation, state machine, core contract, auth/secrets, paid provider, deployment, product redline, cross-project isolation, duplicate-charge, or artifact-loss risk. Requires user-approved design, read-only independent review, independent QA, and rollback evidence.

When uncertain, classify upward. Discovering real data, cost, or production impact automatically promotes to L3.
