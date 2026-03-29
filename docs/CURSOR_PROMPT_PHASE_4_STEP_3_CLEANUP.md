A psycopg ResourceWarning remains in the payment API test run even though all tests pass.

Implement only a narrow test-harness cleanup step.

Scope:
- identify the exact source of the open psycopg connection warning in the payment API test harness
- fix DB/session/connection cleanup in tests
- keep the fix as small as possible
- do not change production business logic
- do not change payment reconciliation logic
- do not expand feature scope

Requirements:
- preserve all current passing tests
- explain the likely cause before making changes
- prefer fixing test fixtures/utilities/lifecycle cleanup over touching production code
- only touch production code if a tiny infrastructure cleanup is strictly necessary

Before writing code:
1. identify the likely warning source
2. explain the smallest safe fix
3. state what production code will remain untouched

Then generate the changes and rerun the relevant tests.