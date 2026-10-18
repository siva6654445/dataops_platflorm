from dataops.config import load_environment_config


def test_dev_config_contains_three_layers():
    config = load_environment_config("dev")
    assert config["environment"] == "dev"
    assert len(config["resources"]) == 3
    assert {item["catalog"] for item in config["resources"]} == {
        "bronze_catalog", "silver_catalog", "gold_catalog"
    }


def test_invalid_environment_is_rejected():
    try:
        load_environment_config("production")
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid environment should be rejected")
