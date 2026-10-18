# Databricks DataOps Platform — Enterprise Starter

A fresh project built from scratch to mimic the operational model of Azure DevOps:
**separate manually triggered pipelines**, each with its own parameters, backed by shared
reusable workflow templates and Python entry points.

This is a new project. It does not reuse or overwrite `dbx_integration`.

## Trigger model

GitHub → Actions → choose a pipeline → Run workflow → choose parameters → review logs.

Separate workflows:
- `infra-deploy.yml` — catalogs, schemas, managed volumes
- `control-tables.yml` — bootstrap / initial / incremental control-table operations
- `schema-migration.yml` — apply a versioned migration
- `batch-load.yml` — initial, incremental, or repair execution mode
- `repair.yml` — process selected failed workflow/entity
- `cleanup.yml` — preview-first cleanup
- `rollback.yml` — restore/rollback operation scaffold

Shared components:
- `.github/workflows/_reusable-operation.yml`
- `src/dataops/cli.py`
- `src/dataops/config.py`
- `src/dataops/operations/`
- `config/environments/*.json`
- `tests/`

## Initial resources

The example environment configuration describes:
- `bronze_catalog.bronze.raw_files`
- `silver_catalog.silver.clean_files`
- `gold_catalog.gold.export_files`

These are examples and are not created until you deliberately run an apply operation.

## Setup

1. Create a new GitHub repository, e.g. `databricks-dataops-platform`.
2. Extract/copy this project into that new repository.
3. Add GitHub Actions secrets:
   - `DATABRICKS_HOST`
   - `DATABRICKS_TOKEN`
4. Create GitHub Environments named `dev`, `uat`, `prd`. Configure required reviewers on `prd`.
5. Push to GitHub.
6. Go to **Actions** and choose a specific pipeline.
7. First run with `dry_run=true` in `dev`.

## Local setup

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Validate parameters without contacting Databricks:

```bash
PYTHONPATH=src python -m dataops.cli \
  --operation infra_deploy --environment dev --dry-run true
```

## Safety and honest boundaries

- `dry_run=true` is the default for manual workflows.
- The CLI refuses production apply unless `PRODUCTION_APPROVED=true` is explicitly supplied
  by a protected environment/job configuration.
- Cleanup and rollback are preview-only scaffolds until target-specific deletion/restore
  policies are deliberately implemented.
- Control-table, batch-load, repair, and migration pipelines currently validate and record
  the requested operation; business SQL/job execution adapters must be implemented for your
  actual tables and Databricks jobs.
- The infrastructure operation can create catalogs, schemas, and managed volumes using the
  Databricks SDK. Run first in a disposable dev workspace and ensure the principal has only
  the required privileges.
- No Azure storage account, Azure DevOps project, or Terraform-managed Azure infrastructure
  is required. This project targets Azure Databricks workspace APIs only.

## Enterprise extension points

- Replace PAT with workload identity/OAuth where supported by your workspace and GitHub setup.
- Add CODEOWNERS and branch protection for `main`.
- Require PR checks (`quality-checks.yml`) before merge.
- Add idempotency/state checks, policy validation, drift detection, alerts, and approval gates.
