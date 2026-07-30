import json


def test_doctor_json_is_safe_and_actionable(cli_runner, isolated_env) -> None:
    result = cli_runner("doctor", "--json")

    assert result.exit_code in {0, 1}
    payload = json.loads(result.stdout)
    assert payload["douban_access"] == "read_only"
    assert "checks" in payload
    assert "cookie" not in result.stdout.casefold()


def test_print_config_has_generic_stdio_and_http_forms(cli_runner, isolated_env) -> None:
    stdio = cli_runner("print-config", "--transport", "stdio")
    http = cli_runner("print-config", "--transport", "streamable-http")

    assert stdio.exit_code == 0
    assert json.loads(stdio.stdout)["command"] == "cove-douban-mcp"
    assert json.loads(stdio.stdout)["args"] == ["serve", "--transport", "stdio"]
    assert json.loads(http.stdout)["url"].endswith("/mcp")
    assert "actual_token" not in http.stdout

