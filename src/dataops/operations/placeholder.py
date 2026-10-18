from __future__ import annotations


def run_placeholder(operation: str, parameters: dict[str, str], dry_run: bool) -> list[str]:
    """Safe placeholder until real table/job-specific adapters are configured."""
    summary = (
        f"Operation={operation}; environment={parameters['environment']}; "
        f"scope={parameters.get('scope', 'not-applicable')}; "
        f"target={parameters.get('target', 'not-provided')}"
    )
    if dry_run:
        return ["DRY RUN — no changes will be made.", summary]
    raise NotImplementedError(
        f"{operation} is not wired to a real Databricks job/SQL implementation yet. "
        "Configure the operation-specific adapter before applying."
    )
