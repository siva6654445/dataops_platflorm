# Architecture

```text
Operator
  |
  v
GitHub Actions: select one named trigger
  |  workflow_dispatch parameters
  v
Reusable operation workflow
  |  checkout, Python, environment, dry-run, secrets
  v
Python CLI / operation adapter
  |---- infrastructure (implemented with Databricks SDK)
  |---- control tables (adapter required)
  |---- schema migration (adapter required)
  |---- batch load (adapter required)
  |---- repair (adapter required)
  |---- cleanup (adapter required; dry-run first)
  |---- rollback (adapter required; dry-run first)
  v
Azure Databricks workspace API / Jobs / Unity Catalog
```

Each named workflow is a separate operational trigger, matching the user experience of
separate Azure Pipelines. Shared logic lives in a reusable workflow so authentication,
setup, environment selection, and safety checks remain consistent.
