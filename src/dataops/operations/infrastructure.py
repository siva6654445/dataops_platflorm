from __future__ import annotations

from typing import Any


def deploy_infrastructure(config: dict[str, Any], dry_run: bool) -> list[str]:
    """Create catalogs, schemas and managed volumes idempotently.

    Requires a Databricks SDK WorkspaceClient authenticated by environment variables.
    The dry-run path never contacts the workspace.
    """
    plan: list[str] = []
    for resource in config["resources"]:
        catalog = resource["catalog"]
        schema = resource["schema"]
        volume = resource["volume"]
        plan.extend([
            f"Ensure catalog: {catalog}",
            f"Ensure schema: {catalog}.{schema}",
            f"Ensure managed volume: {catalog}.{schema}.{volume}",
        ])

    if dry_run:
        return ["DRY RUN — no changes will be made.", *plan]

    from databricks.sdk import WorkspaceClient
    from databricks.sdk.errors import AlreadyExists, NotFound

    client = WorkspaceClient()
    for resource in config["resources"]:
        catalog = resource["catalog"]
        schema = resource["schema"]
        volume = resource["volume"]
        comment = resource.get("comment", "")

        try:
            client.catalogs.get(catalog)
        except NotFound:
            client.catalogs.create(name=catalog, comment=f"Managed by DataOps ({config['environment']})")

        try:
            client.schemas.get(full_name=f"{catalog}.{schema}")
        except NotFound:
            client.schemas.create(name=schema, catalog_name=catalog, comment=comment)

        try:
            client.volumes.read(name=volume, catalog_name=catalog, schema_name=schema)
        except NotFound:
            client.volumes.create(
                name=volume,
                catalog_name=catalog,
                schema_name=schema,
                volume_type="MANAGED",
                comment=comment,
            )
        except AlreadyExists:
            # A concurrent deployment may have created the volume after the read.
            pass

    return ["Infrastructure apply completed.", *plan]
