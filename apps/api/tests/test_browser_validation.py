from uuid import uuid4
from unittest.mock import patch

from app.services.browser_validation import BrowserValidationService


def test_browser_validation_timeout_is_structured_failure():
    project_id = uuid4()
    with patch("app.services.browser_validation.subprocess.run", side_effect=__import__("subprocess").TimeoutExpired(["docker"], 180)):
        result = BrowserValidationService._run(project_id, 1, "http://127.0.0.1:49999", "container-id")

    assert result["status"] == "failed"
    assert "timed out after 180 seconds" in result["diagnostics"][0]


def test_browser_validation_command_uses_host_gateway():
    project_id = uuid4()
    completed = __import__("subprocess").CompletedProcess(["docker"], 0, stdout='{"http_status":200,"metrics":{"fcp_ms":100,"lcp_ms":200,"inp_ms":null,"cls":0.01,"ttfb_ms":50}}\n', stderr="")
    with patch("app.services.browser_validation.subprocess.run", return_value=completed) as run:
        result = BrowserValidationService._run(project_id, 1, "http://127.0.0.1:49999", "container-id")

    command = run.call_args.args[0]
    assert "--add-host" in command
    assert "host.docker.internal:host-gateway" in command
    assert "container:container-id" not in command
    assert "AWE_BROWSER_TARGET=http://host.docker.internal:49999" in command
    assert result["status"] == "warning"  # INP unavailable is advisory.
