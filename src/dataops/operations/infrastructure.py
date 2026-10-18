
from __future__ import annotations

import os
from typing import Any

from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import AlreadyExists, NotFound


PROTECTED_CATALOGS = {"munich_bronze", "munich_re_bronze"}


def deploy_infrastructure(
    config: dict[str, Any], dry_run: bool
) -> list[str]:
    """Create default-storage catalogs, schemas, and managed volumes."""

    plan: list[str] = []

    for resource in config["resources"]:
        catalog = resource["catalog"]
        schema = resource["schema"]
        volume = resource["volume"]

        if catalog in PROTECTED_CATALOGS:
            raise ValueError(
                f"Protected catalog cannot be managed by this deployment: {catalog}"
            )

        plan.extend([
            f"Ensure catalog: {catalog} (default storage)",
            f"Ensure schema: {catalog}.{schema}",
            f"Ensure managed volume: {catalog}.{schema}.{volume}",
        ])

    if dry_run:
        return ["DRY RUN — no changes will be made.", *plan]

    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    warehouse_id = os.getenv("DATABRICKS_SQL_WAREHOUSE_ID")

    if not host or not token or not warehouse_id:
        raise RuntimeError(
            "Set DATABRICKS_HOST, DATABRICKS_TOKEN, and "
            "DATABRICKS_SQL_WAREHOUSE_ID."
        )

    client = WorkspaceClient(host=host, token=token)

    for resource in config["resources"]:
        catalog = resource["catalog"]
        schema = resource["schema"]
        volume = resource["volume"]
        comment = resource.get("comment", "")

        # Create missing catalogs through SQL using default storage.
        try:
            client.catalogs.get(catalog)
        except NotFound:
            safe_catalog = catalog.replace("`", "``")
            safe_comment = (
                f"Managed by DataOps ({config['environment']})"
                .replace("'", "''")
            )
            statement = (
                f"CREATE CATALOG IF NOT EXISTS `{safe_catalog}` "
                f"COMMENT '{safe_comment}'"
            )

            response = client.statement_execution.execute_statement(
                warehouse_id=warehouse_id,
                statement=statement,
                wait_timeout="50s",
                on_wait_timeout="CANCEL",
            )

            status = response.status
            if status is None or status.state is None:
                raise RuntimeError(
                    f"No execution status returned for catalog {catalog}."
                )

            if status.state.value != "SUCCEEDED":
                message = (
                    status.error.message
                    if status.error
                    else status.state.value
                )
                raise RuntimeError(
                    f"Failed to create catalog {catalog}: {message}"
                )

        # Create the schema if it does not exist.
        try:
            client.schemas.get(full_name=f"{catalog}.{schema}")
        except NotFound:
            try:
                client.schemas.create(
                    name=schema,
                    catalog_name=catalog,
                    comment=comment,
                )
            except AlreadyExists:
                pass

        # Create the managed volume if it does not exist.
        full_volume_name = f"{catalog}.{schema}.{volume}"

        try:
            client.volumes.read(name=full_volume_name)
        except NotFound:
            try:
                client.volumes.create(
                    name=volume,
                    catalog_name=catalog,
                    schema_name=schema,
                    volume_type="MANAGED",
                )
            except AlreadyExists:
                pass

    return ["Infrastructure apply completed.", *plan]
