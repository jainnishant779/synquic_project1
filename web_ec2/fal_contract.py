"""Check our fal.ai requests against fal's published OpenAPI schemas, without a key and without spending anything.

fal publishes each model's queue schema at https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=<id>. The files are kept in
fal_schemas/ so the checks run offline and in tests. Used in three places:
  - `python fal_contract.py refresh`  downloads the schemas again (free) for every model the studio can call
  - `python fal_contract.py check`    builds the exact payloads MediaProviders would send and validates each one
  - dry-run mode (FAL_DRY_RUN=1): every payload is validated before it would be sent, see media_providers.DryRunTransport
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parent / "fal_schemas"
OPENAPI_URL = "https://fal.ai/api/openapi/queue/openapi.json?endpoint_id={}"


def schema_file(endpoint):
    return SCHEMA_DIR / (endpoint.replace("/", "_").replace(".", "_") + ".json")


def load(endpoint):
    path = schema_file(endpoint)
    if not path.is_file():
        raise FileNotFoundError(f"No saved schema for {endpoint}; run `python fal_contract.py refresh`")
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve(doc, node):
    while isinstance(node, dict) and "$ref" in node:
        name = node["$ref"].split("/")[-1]
        extra = {k: v for k, v in node.items() if k != "$ref"}
        node = {**doc["components"]["schemas"][name], **extra}
    return node


def _endpoint_paths(doc):
    return {k: v for k, v in doc.get("paths", {}).items() if "/requests/" not in k}


def input_schema(doc):
    for item in _endpoint_paths(doc).values():
        post = item.get("post")
        if post:
            return _resolve(doc, post["requestBody"]["content"]["application/json"]["schema"])
    raise ValueError("schema has no submit path")


def output_schema(doc):
    for path, item in doc.get("paths", {}).items():
        if path.endswith("/requests/{request_id}") and "get" in item:
            return _resolve(doc, item["get"]["responses"]["200"]["content"]["application/json"]["schema"])
    raise ValueError("schema has no result path")


TYPES = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "array": list, "object": dict}


def _check(doc, schema, value, where, problems):
    schema = _resolve(doc, schema)
    for key in ("anyOf", "oneOf"):
        if key in schema:
            options = schema[key]
            for option in options:
                trial = []
                _check(doc, option, value, where, trial)
                if not trial:
                    return
            kinds = []
            for option in options:
                option = _resolve(doc, option)
                kinds.append(str(option.get("enum") or option.get("type") or option.get("title") or "?"))
            problems.append(f"{where}: {value!r:.60} matches none of {' | '.join(kinds)}")
            return
    for part in schema.get("allOf", []):
        _check(doc, part, value, where, problems)
    kind = schema.get("type")
    if kind == "null":
        if value is not None:
            problems.append(f"{where}: must be null")
        return
    if kind in TYPES:
        expected = TYPES[kind]
        if isinstance(value, bool) and kind in ("integer", "number"):
            problems.append(f"{where}: must be {kind}, got boolean")
            return
        if not isinstance(value, expected):
            problems.append(f"{where}: must be {kind}, got {type(value).__name__} {value!r:.40}")
            return
    if "enum" in schema and value not in schema["enum"]:
        problems.append(f"{where}: {value!r} is not one of {schema['enum']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            problems.append(f"{where}: {value} is below the minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            problems.append(f"{where}: {value} is above the maximum {schema['maximum']}")
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            problems.append(f"{where}: shorter than {schema['minLength']} characters")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            problems.append(f"{where}: longer than {schema['maxLength']} characters")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            problems.append(f"{where}: fewer than {schema['minItems']} items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            problems.append(f"{where}: more than {schema['maxItems']} items")
        if "items" in schema:
            for i, item in enumerate(value[:3]):
                _check(doc, schema["items"], item, f"{where}[{i}]", problems)
    if isinstance(value, dict) and ("properties" in schema or kind == "object"):
        props = schema.get("properties", {})
        for name in schema.get("required", []):
            if name not in value:
                problems.append(f"{where}.{name}: required field missing")
        for name, item in value.items():
            if name in props:
                _check(doc, props[name], item, f"{where}.{name}", problems)
            elif props and schema.get("additionalProperties") is not True:
                problems.append(f"{where}.{name}: unknown field (the model would ignore it)")


def validate_input(endpoint, payload):
    """Problems with a payload for this endpoint, as readable strings. Empty list = the request matches the schema."""
    doc = load(endpoint)
    problems = []
    _check(doc, input_schema(doc), payload, "input", problems)
    return problems


def sample_output(endpoint):
    """An output object built from the schema's own examples, to check that our parsing finds the file."""
    doc = load(endpoint)

    def build(schema, depth=0):
        schema = _resolve(doc, schema)
        if depth > 6:
            return None
        if "examples" in schema and schema["examples"]:
            return schema["examples"][0]
        for key in ("anyOf", "oneOf"):
            if key in schema:
                for option in schema[key]:
                    if _resolve(doc, option).get("type") != "null":
                        return build(option, depth + 1)
        if schema.get("type") == "array":
            return [build(schema.get("items", {}), depth + 1)]
        if schema.get("type") == "object" or "properties" in schema:
            return {name: build(item, depth + 1) for name, item in schema.get("properties", {}).items() if name in schema.get("required", []) or depth < 2}
        return schema.get("default")

    def fill_urls(node, key=""):   # fal's File schema has no example url; give one with the extension the field implies
        if isinstance(node, dict):
            if "url" in node and not node["url"]:
                node["url"] = "https://v3.fal.media/files/check/out" + (".mp4" if "video" in key else ".png")
            for name, value in node.items():
                fill_urls(value, name)
        elif isinstance(node, list):
            for value in node:
                fill_urls(value, key)
        return node

    return fill_urls(build(output_schema(doc)))


def endpoints():
    """Every fal endpoint the studio can call, with the settings currently in force."""
    import media_providers as mp
    s = mp.MediaProviders.settings()
    names = [s["image_model"], s["edit_model"], s["cutout_model"], s["product_shot_model"]]
    return names + [spec["endpoint"] for spec in mp.VIDEO_MODELS.values()]


def refresh():
    import urllib.request
    SCHEMA_DIR.mkdir(exist_ok=True)
    failed = []
    for endpoint in endpoints():
        try:
            with urllib.request.urlopen(OPENAPI_URL.format(endpoint), timeout=40) as response:
                body = response.read()
            json.loads(body)
            schema_file(endpoint).write_bytes(body)
            print("saved ", endpoint)
        except Exception as error:   # a 404 means the endpoint id is wrong
            failed.append(endpoint)
            print("FAILED", endpoint, str(error)[:80])
    return failed


def captured_calls():
    """Run every MediaProviders call with a capturing transport: (label, endpoint, payload, parsed ok or error)."""
    import io
    import os
    import media_providers as mp
    from PIL import Image

    def tiny(fmt):
        buffer = io.BytesIO()
        Image.new("RGBA" if fmt == "PNG" else "RGB", (8, 8), (200, 120, 40, 255) if fmt == "PNG" else (200, 120, 40)).save(buffer, fmt)
        return buffer.getvalue()

    jpeg, png = tiny("JPEG"), tiny("PNG")
    mp4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64
    calls = []

    def submit(key, endpoint, payload, timeout):
        calls.append((endpoint, payload))
        return sample_output(endpoint)

    def download(url):
        path = url.lower().split("?")[0]
        return mp4 if path.endswith((".mp4", ".mov", ".webm")) else png if path.endswith(".png") else jpeg

    out = []

    def run(label, fn):
        before = len(calls)
        try:
            fn()
            result = "ok"
        except Exception as error:
            result = f"parse error: {error}"
        for endpoint, payload in calls[before:]:
            out.append((label, endpoint, payload, result))

    providers = mp.MediaProviders(lambda: "check-only", submit=submit, download=download)
    run("text_to_image", lambda: providers.text_to_image("A bright kitchen counter, morning light", "9:16"))
    run("edit_with_references", lambda: providers.edit_with_references("The product on a kitchen counter", [jpeg], "9:16"))
    run("remove_background", lambda: providers.remove_background(jpeg))
    run("product_shot", lambda: providers.product_shot(png, "on a marble counter"))
    old = os.environ.get("AD_VIDEO_MODEL")
    try:
        for name in mp.VIDEO_MODELS:
            os.environ["AD_VIDEO_MODEL"] = name
            for seconds in (2, 3, 5):
                run(f"image_to_video {name} {seconds}s", lambda: providers.image_to_video(jpeg, "Slow push-in on the scene", seconds, "720p"))
    finally:
        if old is None:
            os.environ.pop("AD_VIDEO_MODEL", None)
        else:
            os.environ["AD_VIDEO_MODEL"] = old
    return out


def check():
    bad = 0
    for label, endpoint, payload, parsed in captured_calls():
        try:
            problems = validate_input(endpoint, payload)
        except FileNotFoundError as error:
            problems = [str(error)]
        if parsed != "ok":
            problems.append(f"output: {parsed}")
        bad += bool(problems)
        print(("OK    " if not problems else "FAIL  ") + f"{label:28} {endpoint}")
        for problem in problems:
            print("        -", problem)
    print(f"{bad} call(s) with problems")
    return bad


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    command = sys.argv[1] if len(sys.argv) > 1 else "check"
    if command == "refresh":
        sys.exit(1 if refresh() else 0)
    sys.exit(1 if check() else 0)
