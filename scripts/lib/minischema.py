"""A dependency-free JSON Schema validator covering the subset this toolkit uses.

Why not `jsonschema`? The npm package ships with zero runtime dependencies and
the Python validators only need `pyyaml`. Adding a schema library to run
`validate-project` would push a dependency onto every consumer for a feature
they may never call. The schemas in `contracts/schemas/` are ours, so the
subset they use is bounded and can be supported directly.

Supported keywords:
    $ref ("_defs.json#/$defs/X", "other.schema.json#/$defs/X", "#/$defs/X")
    $defs, type, const, enum, pattern, minLength
    minimum, maximum, minItems, maxItems, minProperties
    properties, required, additionalProperties, patternProperties, items

Anything else in a schema is ignored rather than silently failing, and
`unsupported_keywords()` reports what was skipped so the schemas cannot quietly
outgrow the validator.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

SUPPORTED = {
    "$schema", "$id", "$ref", "$defs", "title", "description", "examples", "default",
    "type", "const", "enum", "pattern", "minLength",
    "minimum", "maximum", "minItems", "maxItems", "minProperties",
    "properties", "required", "additionalProperties", "patternProperties", "items",
}

_TYPE_CHECKS = {
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "array": lambda v: isinstance(v, list),
    "object": lambda v: isinstance(v, dict),
    "null": lambda v: v is None,
}


class SchemaStore:
    """Loads every *.json in a directory and resolves cross-file $ref."""

    def __init__(self, schema_dir: Path):
        self.dir = Path(schema_dir)
        self.schemas: dict[str, dict] = {}
        for path in sorted(self.dir.glob("*.json")):
            self.schemas[path.name] = json.loads(path.read_text(encoding="utf-8"))

    def get(self, name: str) -> dict:
        if name not in self.schemas:
            raise KeyError(f"unknown schema: {name}")
        return self.schemas[name]

    def resolve(self, ref: str, current: str) -> dict:
        if "#" in ref:
            file_part, pointer = ref.split("#", 1)
        else:
            file_part, pointer = ref, ""
        doc = self.get(file_part) if file_part else self.get(current)
        node = doc
        for token in [t for t in pointer.split("/") if t]:
            token = token.replace("~1", "/").replace("~0", "~")
            if not isinstance(node, dict) or token not in node:
                raise KeyError(f"unresolvable $ref: {ref}")
            node = node[token]
        return node

    def unsupported_keywords(self) -> list[str]:
        """Report schema keywords the validator would silently ignore.

        Walks only positions that are actually schemas. The keys inside
        `properties`, `patternProperties`, and `$defs` are names chosen by the
        schema author, not keywords, so they are descended into as schemas
        without being inspected as vocabulary.
        """
        found: set[str] = set()
        NAMED_MAPS = ("properties", "patternProperties", "$defs")

        def walk_schema(node):
            if not isinstance(node, dict):
                return
            for key, value in node.items():
                if key not in SUPPORTED:
                    found.add(key)
                if key in NAMED_MAPS and isinstance(value, dict):
                    for subschema in value.values():
                        walk_schema(subschema)
                elif key in ("items", "additionalProperties"):
                    walk_schema(value)

        for doc in self.schemas.values():
            walk_schema(doc)
        return sorted(found)


def validate(instance, schema_name: str, store: SchemaStore) -> list[str]:
    """Return a list of human-readable error strings. Empty means valid."""
    errors: list[str] = []
    _validate(instance, store.get(schema_name), store, schema_name, "$", errors)
    return errors


def _validate(value, schema, store: SchemaStore, current: str, path: str, errors: list[str]) -> None:
    if schema is True or schema == {}:
        return
    if schema is False:
        errors.append(f"{path}: value is not allowed here")
        return
    if not isinstance(schema, dict):
        return

    if "$ref" in schema:
        ref = schema["$ref"]
        next_file = ref.split("#", 1)[0] or current
        try:
            target = store.resolve(ref, current)
        except KeyError as exc:
            errors.append(f"{path}: {exc}")
            return
        _validate(value, target, store, next_file, path, errors)
        # Sibling keywords alongside $ref still apply.
        rest = {k: v for k, v in schema.items() if k != "$ref"}
        if rest:
            _validate(value, rest, store, current, path, errors)
        return

    if "type" in schema:
        expected = schema["type"]
        allowed = [expected] if isinstance(expected, str) else list(expected)
        if not any(_TYPE_CHECKS.get(t, lambda _v: True)(value) for t in allowed):
            errors.append(f"{path}: expected type {'/'.join(allowed)}, got {_type_name(value)}")
            return

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected constant {schema['const']!r}, got {value!r}")

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} is not one of {schema['enum']}")

    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: {value!r} does not match /{schema['pattern']}/")
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength {schema['minLength']}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: {value} is below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: {value} is above maximum {schema['maximum']}")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: needs at least {schema['minItems']} item(s), got {len(value)}")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: allows at most {schema['maxItems']} item(s), got {len(value)}")
        if "items" in schema:
            for index, item in enumerate(value):
                _validate(item, schema["items"], store, current, f"{path}[{index}]", errors)

    if isinstance(value, dict):
        if "minProperties" in schema and len(value) < schema["minProperties"]:
            errors.append(f"{path}: needs at least {schema['minProperties']} propert(y|ies)")
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required property '{key}'")
        properties = schema.get("properties", {})
        pattern_properties = schema.get("patternProperties", {})
        additional = schema.get("additionalProperties", True)
        for key, item in value.items():
            child = f"{path}.{key}"
            handled = False
            if key in properties:
                _validate(item, properties[key], store, current, child, errors)
                handled = True
            for pattern, subschema in pattern_properties.items():
                if re.search(pattern, str(key)):
                    _validate(item, subschema, store, current, child, errors)
                    handled = True
            if not handled:
                if additional is False:
                    errors.append(f"{path}: unexpected property '{key}'")
                elif isinstance(additional, dict):
                    _validate(item, additional, store, current, child, errors)


def _type_name(value) -> str:
    for name, check in _TYPE_CHECKS.items():
        if name != "number" and check(value):
            return name
    return type(value).__name__
