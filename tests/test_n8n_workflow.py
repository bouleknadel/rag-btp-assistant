"""Vérifie la cohérence du workflow n8n exporté avec l'API."""

import json
import re

import pytest

from rag_btp.api.main import create_app
from rag_btp.config import PROJECT_ROOT

WORKFLOW = PROJECT_ROOT / "n8n" / "workflow_ingestion.json"


@pytest.fixture(scope="module")
def workflow() -> dict:
    return json.loads(WORKFLOW.read_text(encoding="utf-8"))


def test_nodes_are_unique_and_connections_valid(workflow):
    names = [n["name"] for n in workflow["nodes"]]
    assert len(names) == len(set(names))
    assert len({n["id"] for n in workflow["nodes"]}) == len(names)
    for source, outputs in workflow["connections"].items():
        assert source in names
        for branch in outputs["main"]:
            for link in branch:
                assert link["node"] in names, f"{source} → {link['node']}"


def test_every_node_is_reachable_from_trigger(workflow):
    reachable, frontier = set(), ["Nouveau document"]
    while frontier:
        node = frontier.pop()
        reachable.add(node)
        for branch in workflow["connections"].get(node, {}).get("main", []):
            frontier += [link["node"] for link in branch if link["node"] not in reachable]
    assert reachable == {n["name"] for n in workflow["nodes"]}


def test_trigger_watches_inbox_for_new_files(workflow):
    trigger = next(n for n in workflow["nodes"] if n["type"].endswith("localFileTrigger"))
    assert trigger["parameters"]["triggerOn"] == "folder"
    assert "add" in trigger["parameters"]["events"]


def test_api_endpoints_called_exist(workflow):
    routes = {route.path for route in create_app().routes}
    urls = [
        n["parameters"]["url"]
        for n in workflow["nodes"]
        if n["type"] == "n8n-nodes-base.httpRequest" and "api_url" in n["parameters"]["url"]
    ]
    endpoints = {re.search(r"\}\}(/[\w/]+)$", url).group(1) for url in urls}
    assert endpoints == {"/ingest", "/summarize/file"}
    assert endpoints <= routes


def test_multipart_field_names_match_api(workflow):
    fields = {
        n["name"]: n["parameters"]["bodyParameters"]["parameters"][0]["name"]
        for n in workflow["nodes"]
        if n["parameters"].get("contentType") == "multipart-form-data"
    }
    assert fields == {
        "Indexer (POST /ingest)": "files",
        "Synthétiser (POST /summarize/file)": "file",
    }


def test_no_secret_in_export(workflow):
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "credentials" not in text
    for pattern in (
        r"gsk_\w{10,}",
        r"sk-\w{10,}",
        r"lsv2_\w{10,}",
        r"hooks\.slack\.com/services/\w",
    ):
        assert not re.search(pattern, text)
