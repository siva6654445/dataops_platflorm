
from __future__ import annotations

from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound

PROTECTED_CATALOGS = {"munich_bronze", "munich_re_bronze"}


def _names(value: str) -> list[str]:
    return list(dict.fromkeys(
        item.strip()
        for item in (value or "").split(",")
        if item.strip()
    ))


def _parts(name: str, count: int, resource_type: str) -> list[str]:
    parts = name.split(".")
    if len(parts) != count or any(not part for part in parts):
        raise ValueError(
            f"Invalid {resource_type} '{name}'. "
            f"Expected {count} dot-separated components."
        )
    return parts


def _protect(catalog: str) -> None:
    if catalog.lower() in PROTECTED_CATALOGS:
        raise ValueError(
            f"BLOCKED: catalog '{catalog}' is protected."
        )


def _schema_children(
    client: WorkspaceClient,
    catalog: str,
    schema: str,
) -> list[tuple[str, str]]:
    children: list[tuple[str, str]] = []

    for table in client.tables.list(
        catalog_name=catalog,
        schema_name=schema,
    ):
        full_name = getattr(table, "full_name", None)
        if not full_name:
            full_name = f"{catalog}.{schema}.{table.name}"
        children.append(("table", full_name))

    for volume in client.volumes.list(
        catalog_name=catalog,
        schema_name=schema,
    ):
        children.append(
            ("volume", f"{catalog}.{schema}.{volume.name}")
        )

    return children


def cleanup_infrastructure(
    *,
    catalogs: str = "",
    schemas: str = "",
    tables: str = "",
    volumes: str = "",
    dry_run: bool = True,
) -> list[str]:
    """Preview or delete selected Databricks resources."""
    selected_catalogs = _names(catalogs)
    selected_schemas = _names(schemas)
    selected_tables = _names(tables)
    selected_volumes = _names(volumes)

    if not any((
        selected_catalogs,
        selected_schemas,
        selected_tables,
        selected_volumes,
    )):
        raise ValueError(
            "Specify at least one catalog, schema, table, or volume."
        )

    for catalog in selected_catalogs:
        _protect(catalog)
    for name in selected_schemas:
        _protect(_parts(name, 2, "schema")[0])
    for name in selected_tables:
        _protect(_parts(name, 3, "table")[0])
    for name in selected_volumes:
        _protect(_parts(name, 3, "volume")[0])

    client = WorkspaceClient()

    # Resource order ensures child objects are processed before parents.
    plan: set[tuple[str, str]] = set()
    schemas_to_delete: set[str] = set()

    for catalog in selected_catalogs:
        for schema_info in client.schemas.list(catalog_name=catalog):
            schema = schema_info.name
            if schema.lower() == "information_schema":
                continue
            full_schema = f"{catalog}.{schema}"
            schemas_to_delete.add(full_schema)
            plan.update(_schema_children(client, catalog, schema))
        plan.add(("catalog", catalog))

    for full_schema in selected_schemas:
        catalog, schema = _parts(full_schema, 2, "schema")
        schemas_to_delete.add(full_schema)
        plan.update(_schema_children(client, catalog, schema))

    for full_table in selected_tables:
        _parts(full_table, 3, "table")
        plan.add(("table", full_table))

    for full_volume in selected_volumes:
        _parts(full_volume, 3, "volume")
        plan.add(("volume", full_volume))

    for schema in schemas_to_delete:
        plan.add(("schema", schema))

    order = {"table": 0, "volume": 1, "schema": 2, "catalog": 3}
    ordered_plan = sorted(
        plan,
        key=lambda item: (order[item[0]], item[1]),
    )

    messages = [
        f"Mode: {'DRY RUN' if dry_run else 'APPLY'}",
        f"Planned resources: {len(ordered_plan)}",
    ]
    messages.extend(
        f"PLAN: delete {kind}: {name}"
        for kind, name in ordered_plan
    )

    if dry_run:
        messages.append("DRY RUN: nothing was deleted.")
        return messages

    # Recheck protected catalog names immediately before deletion.
    for _, name in ordered_plan:
        _protect(name.split(".", 1)[0])

    for kind, name in ordered_plan:
        try:
            if kind == "table":
                client.tables.delete(full_name=name)
            elif kind == "volume":
                client.volumes.delete(name=name)
            elif kind == "schema":
                client.schemas.delete(full_name=name)
            elif kind == "catalog":
                # Never force-delete. Databricks rejects deletion
                # if other objects remain.
                client.catalogs.delete(name=name)

            messages.append(f"DELETED: {kind}: {name}")

        except NotFound:
            messages.append(f"SKIPPED (not found): {kind}: {name}")

    messages.append("Cleanup completed.")
    return messages
