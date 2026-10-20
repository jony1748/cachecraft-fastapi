import json
import sys

import httpx
from pydantic import ValidationError

from cache_cli.settings import CLISettings


def run() -> None:
    try:
        settings = CLISettings()
        if settings.json is not None:
            payload = json.loads(settings.json)
        else:
            path = settings.input_path()
            raw = sys.stdin.read() if path is None else path.read_text(encoding="utf-8")
            payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("Input JSON must be an object.")

        results = []
        with httpx.Client(base_url=settings.host.rstrip("/"), timeout=15) as client:
            for iteration in range(settings.repeat):
                created = client.post("/api/v1/payload", json=payload)
                created.raise_for_status()
                metadata = created.json()
                response = client.get(f"/api/v1/payload/{metadata['id']}")
                response.raise_for_status()
                results.append({"iteration": iteration + 1, **metadata, **response.json()})
        rendered = "\n".join(json.dumps(row, ensure_ascii=False) for row in results) + "\n"
        path = settings.output_path()
        if path is None:
            sys.stdout.write(rendered)
        else:
            path.write_text(rendered, encoding="utf-8")
    except (ValidationError, ValueError, OSError, httpx.HTTPError, json.JSONDecodeError) as exc:
        print(f"cache-cli: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    run()
