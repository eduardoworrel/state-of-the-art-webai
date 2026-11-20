"""A small JSON Schema validator for the subset the schemas in schema/ use.

Supported: type, enum, const, required, properties, patternProperties, additionalProperties (false),
propertyNames, items, minItems, maxItems, minLength, maxLength, minimum, maximum, pattern, $ref ("#/$defs/..").
If the `jsonschema` package is installed, check.py can use it instead; the result is the same for these schemas.
"""
import re


def _type_ok(v, t):
    return {"object": isinstance(v, dict), "array": isinstance(v, list), "string": isinstance(v, str),
            "integer": isinstance(v, int) and not isinstance(v, bool), "boolean": isinstance(v, bool)}.get(t, True)


def validate(value, schema, root, path="$"):
    """Returns a list of (path, message)."""
    out = []
    if "$ref" in schema:
        node = root
        for part in schema["$ref"].lstrip("#/").split("/"):
            node = node[part]
        return validate(value, node, root, path)
    if "const" in schema and value != schema["const"]:
        out.append((path, f"must be {schema['const']!r}, got {value!r}"))
    if "enum" in schema and value not in schema["enum"]:
        out.append((path, f"must be one of {schema['enum']}, got {value!r}"))
    if "type" in schema and not _type_ok(value, schema["type"]):
        return out + [(path, f"must be {schema['type']}, got {type(value).__name__}")]
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            out.append((path, f"is too short ({len(value)} < {schema['minLength']} characters)"))
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            out.append((path, f"is too long ({len(value)} > {schema['maxLength']} characters): {value!r}"))
        if "pattern" in schema and not re.search(schema["pattern"], value):
            out.append((path, f"does not match the required format {schema['pattern']!r}: {value!r}"))
    if isinstance(value, int) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            out.append((path, f"must be >= {schema['minimum']}"))
        if "maximum" in schema and value > schema["maximum"]:
            out.append((path, f"must be <= {schema['maximum']}"))
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            out.append((path, f"needs at least {schema['minItems']} item(s), has {len(value)}"))
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            out.append((path, f"has too many items ({len(value)} > {schema['maxItems']})"))
        if "items" in schema:
            for i, v in enumerate(value):
                out += validate(v, schema["items"], root, f"{path}[{i}]")
    if isinstance(value, dict):
        for k in schema.get("required", []):
            if k not in value:
                out.append((path, f"is missing the required field `{k}`"))
        props, pats = schema.get("properties", {}), schema.get("patternProperties", {})
        for k, v in value.items():
            if "propertyNames" in schema:
                out += validate(k, schema["propertyNames"], root, f"{path}.{k}")
            matched = False
            if k in props:
                matched = True
                out += validate(v, props[k], root, f"{path}.{k}")
            for pat, sub in pats.items():
                if re.search(pat, k):
                    matched = True
                    out += validate(v, sub, root, f"{path}.{k}")
            if not matched and schema.get("additionalProperties") is False:
                out.append((f"{path}.{k}", "is not a known field (check the spelling, or see SPEC.md)"))
    return out
