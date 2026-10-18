from dataops.operations.infrastructure import deploy_infrastructure


def test_dry_run_returns_plan_without_sdk_call():
    config = {
        "environment": "dev",
        "resources": [{
            "catalog": "bronze_catalog",
            "schema": "bronze",
            "volume": "raw_files",
            "comment": "test"
        }]
    }
    result = deploy_infrastructure(config, dry_run=True)
    assert any("bronze_catalog.bronze.raw_files" in line for line in result)
    assert result[0].startswith("DRY RUN")
