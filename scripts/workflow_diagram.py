"""Build a self-contained workflow diagram from a bounded, auditable model."""
from argparse import ArgumentParser
from collections import defaultdict
from html import escape
import json
from pathlib import Path
import re

from chart_html import require


ASSETS = Path(__file__).resolve().parents[1] / "assets"


def text(data, key, limit=90):
    value = data.get(key)
    require(isinstance(value, str) and bool(value.strip()) and len(value) <= limit,
            f"{key} must contain 1 to {limit} characters")
    return value


def integer(value, low, high, label):
    require(type(value) is int and low <= value <= high, f"{label} must be {low} to {high}")
    return value


def validate(model):
    require(isinstance(model, dict), "model must be an object")
    for key in ("title", "purpose", "source"):
        text(model, key, 150)
    roles = model.get("roles")
    require(isinstance(roles, list) and 1 <= len(roles) <= 5
            and all(isinstance(role, str) and 1 <= len(role.strip()) <= 12 for role in roles),
            "supply 1 to 5 named roles")
    require(len(set(roles)) == len(roles), "roles must be unique")
    items = model.get("nodes")
    require(isinstance(items, list) and 2 <= len(items) <= 16, "supply 2 to 16 nodes")
    nodes = {}
    flow_slots = set()
    lane_slots = set()
    for data in items:
        require(isinstance(data, dict), "node must be an object")
        key = text(data, "id", 32)
        require(re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", key) and key not in nodes,
                f"invalid or duplicate node ID: {key}")
        text(data, "label", 18)
        stage = integer(data.get("stage"), 0, 6, f"stage for {key}")
        track = integer(data.get("track"), 0, 4, f"track for {key}")
        role = text(data, "role", 12)
        require(role in roles, f"unknown role for {key}")
        require(data.get("kind") in ("start", "action", "decision", "end"), f"invalid kind for {key}")
        require((stage, track) not in flow_slots and (stage, role) not in lane_slots,
                f"nodes overlap in a workflow view: {key}")
        flow_slots.add((stage, track))
        lane_slots.add((stage, role))
        nodes[key] = data
    first = [key for key, data in nodes.items() if data["kind"] == "start"]
    require(len(first) == 1 and any(n["kind"] == "end" for n in nodes.values()),
            "one start and at least one terminal node are required")
    entries = model.get("edges")
    require(isinstance(entries, list) and 1 <= len(entries) <= 24, "supply 1 to 24 edges")
    pairs = set()
    successors = defaultdict(list)
    for edge in entries:
        require(isinstance(edge, dict), "edge must be an object")
        start, end = text(edge, "from", 32), text(edge, "to", 32)
        require(start in nodes and end in nodes and start != end, f"invalid edge: {start} → {end}")
        require((start, end) not in pairs, f"duplicate edge: {start} → {end}")
        require(nodes[start]["kind"] != "end" and nodes[end]["kind"] != "start",
                "terminal nodes cannot have successors; start cannot have predecessors")
        require(isinstance(edge.get("label", ""), str) and len(edge.get("label", "")) <= 14,
                "edge label can be at most 14 characters")
        pairs.add((start, end))
        successors[start].append(edge)
    for key, item in nodes.items():
        branch = successors[key]
        if item["kind"] == "decision":
            reasons = [edge.get("label", "").strip() for edge in branch]
            require(len(reasons) >= 2 and all(reasons) and len(set(reasons)) == len(reasons),
                    f"decision {key} needs distinct named branches")
        elif item["kind"] != "end":
            require(len(branch) == 1, f"node {key} must have one successor; use a decision to split")
    visited = set()
    pending = list(first)
    while pending:
        key = pending.pop()
        if key not in visited:
            visited.add(key)
            pending.extend(edge["to"] for edge in successors[key])
    require(visited == nodes.keys(), "all nodes must be reachable from the start")
    if "focus_node" in model:
        require(text(model, "focus_node", 32) in nodes, "focus_node must reference a node")
    counts = model.get("observations", [])
    require(isinstance(counts, list) and len(counts) <= 100, "observations must contain up to 100 path groups")
    if counts:
        text(model, "period", 100)
        text(model, "unit", 6)
    for route in counts:
        require(isinstance(route, dict), "observed path must be an object")
        path = route.get("nodes")
        require(isinstance(path, list) and 1 <= len(path) <= 50
                and all(isinstance(key, str) and key in nodes for key in path), "invalid observed path")
        require(path[0] == first[0] and all(pair in pairs for pair in zip(path, path[1:])),
                "observed paths must start at the entry and use existing edges")
        require(route.get("state") in ("closed", "open"), "observed path state must be closed or open")
        require((nodes[path[-1]]["kind"] == "end") == (route["state"] == "closed"),
                "closed paths need a terminal outcome; open paths cannot have one")
        integer(route.get("count"), 1, 1_000_000_000, "observed path count")


def build(model):
    validate(model)
    values = {
        "TITLE": escape(model["title"]),
        "DATA": json.dumps(model, ensure_ascii=False, allow_nan=False).replace("<", "\\u003c"),
        "MOTION": (ASSETS / "chart-motion.js").read_text(encoding="utf-8"),
        "WORKFLOW": (ASSETS / "workflow-diagram.js").read_text(encoding="utf-8"),
    }
    source = (ASSETS / "workflow-diagram.html").read_text(encoding="utf-8")
    return re.sub(r"@@([A-Z]+)@@", lambda match: values[match.group(1)], source)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        model = json.loads(args.spec.read_text(encoding="utf-8-sig"))
        args.out.write_text(build(model), encoding="utf-8")
    except (ValueError, OSError) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    main()
