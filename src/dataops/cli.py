
from __future__ import annotations

import argparse
import os
import sys

from dataops.config import load_environment_config
from dataops.operations.cleanup import cleanup_infrastructure
from dataops.operations.infrastructure import deploy_infrastructure
from dataops.operations.placeholder import run_placeholder

OPERATIONS = {
    "infra_deploy",
    "control_tables",
    "schema_migration",
    "batch_load",
    "repair",
    "cleanup",
    "rollback",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enterprise Databricks DataOps dispatcher"
    )

    parser.add_argument(
        "--operation",
        required=True,
        choices=sorted(OPERATIONS),
    )
    parser.add_argument(
        "--environment",
        required=True,
        choices=["dev", "uat", "prd"],
    )
    parser.add_argument(
        "--dry-run",
        choices=["true", "false"],
        default="true",
    )

    # Existing parameters used by other DataOps operations.
    parser.add_argument(
        "--scope",
        choices=[
            "initial",
            "incremental",
            "repair",
            "all_project_catalogs",
            "one_catalog",
            "one_schema",
            "one_volume",
        ],
        default="incremental",
    )
    parser.add_argument("--target", default="")
    parser.add_argument("--migration-version", default="")

    # Parameters used by the cleanup operation.
    parser.add_argument("--catalogs", default="")
    parser.add_argument("--schemas", default="")
    parser.add_argument("--tables", default="")
    parser.add_argument("--volumes", default="")

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dry_run = args.dry_run == "true"

    # Keep the existing production approval guard.
    if (
        args.environment == "prd"
        and not dry_run
        and os.getenv("PRODUCTION_APPROVED", "").lower() != "true"
    ):
        print(
            "ERROR: production apply is blocked. "
            "Use a protected GitHub Environment and explicitly "
            "configure PRODUCTION_APPROVED=true after approval.",
            file=sys.stderr,
        )
        return 2

    params = {
        "environment": args.environment,
        "scope": args.scope,
        "target": args.target,
        "migration_version": args.migration_version,
    }

    try:
        if args.operation == "infra_deploy":
            config = load_environment_config(args.environment)
            messages = deploy_infrastructure(config, dry_run)

        elif args.operation == "cleanup":
            messages = cleanup_infrastructure(
                catalogs=args.catalogs,
                schemas=args.schemas,
                tables=args.tables,
                volumes=args.volumes,
                dry_run=dry_run,
            )

        else:
            messages = run_placeholder(
                args.operation,
                params,
                dry_run,
            )

        for message in messages:
            print(message)

        return 0

    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
