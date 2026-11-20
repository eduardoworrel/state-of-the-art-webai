"""Loads the small YAML subset used by this repo (maps, lists, quoted/plain scalars, comments).

If PyYAML is installed it is used instead, so contributors can write any valid YAML.
The subset: 2-space indentation, `key: value`, `- item`, `- key: value` (map items), `#` comment lines.
"""
import re
from pathlib import Path

try:  # optional
    import yaml as _yaml
except ImportError:  # pragma: no cover
    _yaml = None


def _scalar(v):
    v = v.strip()
    if v[:1] in ('"', "'"):
        q = v[0]
        end = v.rfind(q)
        s = v[1:end]
        return s.replace('\\"', '"').replace("\\\\", "\\") if q == '"' else s.replace("''", "'")
    v = re.sub(r"\s#.*$", "", v).strip()
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if v in ("true", "false"):
        return v == "true"
    if v in ("", "null", "~"):
        return None
    return v


def _kv(content):
    m = re.match(r"^([^:\s][^:]*?):(?:\s+(.*))?$", content)
    return (m.group(1), m.group(2)) if m else None


def _block(lines, i, indent):
    if lines[i][1] == "-" or lines[i][1].startswith("- "):
        return _list(lines, i, indent)
    return _map(lines, i, indent)


def _list(lines, i, indent):
    out = []
    while i < len(lines) and lines[i][0] == indent and (lines[i][1] == "-" or lines[i][1].startswith("- ")):
        rest = lines[i][1][1:].strip()
        if not rest:
            i += 1
            node, i = _block(lines, i, lines[i][0])
            out.append(node)
        elif _kv(rest) and not rest.startswith(('"', "'")):
            lines[i] = (indent + 2, rest)
            node, i = _map(lines, i, indent + 2)
            out.append(node)
        else:
            out.append(_scalar(rest))
            i += 1
    return out, i


def _map(lines, i, indent):
    out = {}
    while i < len(lines) and lines[i][0] == indent and not lines[i][1].startswith("- "):
        kv = _kv(lines[i][1])
        if not kv:
            raise ValueError(f"cannot parse line: {lines[i][1]!r}")
        key, val = kv
        i += 1
        if val is None or val == "":
            if i < len(lines) and (lines[i][0] > indent or (lines[i][0] == indent and lines[i][1].startswith("- "))):
                out[key], i = _block(lines, i, lines[i][0])
            else:
                out[key] = None
        else:
            out[key] = _scalar(val)
    return out, i


def parse(text):
    lines = []
    for raw in text.splitlines():
        s = raw.rstrip()
        if not s.strip() or s.lstrip().startswith("#"):
            continue
        lines.append((len(s) - len(s.lstrip(" ")), s.strip()))
    if not lines:
        return {}
    node, _ = _block(lines, 0, lines[0][0])
    return node


def _plain(x):
    """PyYAML parses dates; keep everything as plain strings/ints like the mini parser does."""
    if isinstance(x, dict):
        return {str(k): _plain(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_plain(v) for v in x]
    if x is None or isinstance(x, (bool, int)):
        return x
    return str(x)


def load(path):
    text = Path(path).read_text(encoding="utf-8")
    if _yaml is not None:
        return _plain(_yaml.safe_load(text))
    return parse(text)
