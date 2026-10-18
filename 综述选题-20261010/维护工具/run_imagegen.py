"""Reuse Codex provider credentials with the installed imagegen CLI.

This launcher configures a child process; image requests remain implemented by
the unmodified imagegen skill. Credentials are never written into this project.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


DEFAULT_MODEL = "gpt-image-2.5-sunburst"
DEFAULT_QUALITY = "high"


def load_provider() -> tuple[Path, str, str, str]:
    codex_dir = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    config = tomllib.loads((codex_dir / "config.toml").read_text(encoding="utf-8-sig"))
    provider_name = config.get("model_provider", "openai")
    provider = config.get("model_providers", {}).get(provider_name, {})
    endpoint = provider.get("base_url", "https://api.openai.com/v1").rstrip("/")
    parsed = urlsplit(endpoint)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Provider base_url must be an HTTPS URL without credentials, query or fragment.")
    key = (
        provider.get("experimental_bearer_token")
        or provider.get("api_key")
        or provider.get("api-key")
        or os.environ.get(provider.get("env_key", "OPENAI_API_KEY"))
        or config.get("api_key")
        or config.get("api-key")
    )
    if not isinstance(key, str) or not key.strip():
        raise ValueError("No credential found for the active Codex provider.")
    key = key.strip()
    if key.lower().startswith("bearer "):
        key = key[7:].strip()
    return codex_dir, provider_name, endpoint, key


def redact(message: str, key: str) -> str:
    message = message.replace(key, "[REDACTED]")
    message = re.sub(r"(?i)Bearer\s+[^\s\"']+", "Bearer [REDACTED]", message)
    return re.sub(r"\bsk-[A-Za-z0-9_-]+", "[REDACTED]", message)


def check_models(endpoint: str, key: str) -> int:
    request = Request(
        endpoint + "/models",
        headers={"Authorization": "Bearer " + key, "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.load(response)
        model_ids = sorted(str(item.get("id", "")) for item in payload.get("data", []))
        image_models = [model for model in model_ids if "image" in model.lower()]
        print(json.dumps({"model_list_accessible": True, "requested_model": DEFAULT_MODEL,
                          "requested_model_listed": DEFAULT_MODEL in model_ids,
                          "image_models": image_models}, ensure_ascii=False), flush=True)
        return 0
    except HTTPError as exc:
        print(f"Model-list check: HTTP {exc.code}", file=sys.stderr, flush=True)
        return 1
    except (URLError, TimeoutError) as exc:
        print("Model-list check: " + redact(str(exc), key), file=sys.stderr, flush=True)
        return 1


def has_option(arguments: list[str], option: str) -> bool:
    return any(argument == option or argument.startswith(option + "=") for argument in arguments)


def main() -> int:
    try:
        codex_dir, provider_name, endpoint, key = load_provider()
    except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
        # Do not print TOML contents or values from a malformed credential file.
        print(f"Could not load Codex provider configuration ({type(exc).__name__}).", file=sys.stderr)
        return 2

    print(f"Provider: {provider_name}; endpoint: {endpoint}; credential: loaded (hidden).", flush=True)
    arguments = sys.argv[1:]
    if arguments == ["--check"]:
        return check_models(endpoint, key)
    if not arguments:
        print("Usage: run_imagegen.py --check | generate/edit/generate-batch [imagegen CLI arguments]", file=sys.stderr)
        return 2

    cli = codex_dir / "skills/.system/imagegen/scripts/image_gen.py"
    if not cli.is_file():
        print("Installed imagegen CLI not found.", file=sys.stderr)
        return 2
    if arguments[0] in {"generate", "edit", "generate-batch"}:
        for option, default in (("--model", DEFAULT_MODEL), ("--quality", DEFAULT_QUALITY), ("--size", "auto")):
            if not has_option(arguments, option):
                arguments += [option, default]

    child_environment = os.environ.copy()
    child_environment.update({"OPENAI_API_KEY": key, "OPENAI_BASE_URL": endpoint,
                              "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"})
    # Disable SDK debug logging so request headers are not emitted.
    child_environment.pop("OPENAI_LOG", None)
    process = subprocess.Popen(
        [sys.executable, "-X", "utf8", str(cli), *arguments],
        env=child_environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
    assert process.stdout is not None
    for line in process.stdout:
        print(redact(line, key), end="", flush=True)
    return process.wait()


if __name__ == "__main__":
    raise SystemExit(main())
