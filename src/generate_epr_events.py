#!/usr/bin/env python3

import argparse
import json
import re
import shlex
import logging
import sys
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx
import ulid


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_except_hook(type, value, tb):
    print(f"epr python hates {type.__name__}")
    print(str(type))
    import pdb
    import traceback
    traceback.print_exception(type, value, tb)
    pdb.post_mortem(tb)


debug = os.environ.get("EPR_DEBUG", False)
if debug:
    sys.excepthook = debug_except_hook
    logger.setLevel(logging.DEBUG)# Set up logging



# Function to generate a ULID
def generate_ulid() -> str:
    return str(ulid.ulid())


# Function to get current timestamp in ISO format
def get_current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def gen_sha(seed: str) -> str:
    """Generate a fake sha256 hash from a seed string."""
    import hashlib

    h = hashlib.sha256()
    h.update(seed.encode("utf-8"))
    return h.hexdigest()


def generate_event_receivers() -> List[Dict[str, Any]]:
    """
    Generate a list of event receivers for each supported event type.
    """
    event_receivers: List[Dict[str, Any]] = []
    types = [
        "dev.cdevents.pipelinerun.started.0.2.0",
        "dev.cdevents.pipelinerun.queued.0.2.0",
        "dev.cdevents.artifact.packaged.0.2.0",
        "dev.cdevents.artifact.published.0.2.0",
        "dev.cdevents.build.started.0.2.0",
        "dev.cdevents.build.finished.0.2.0",
        "dev.cdevents.testcaserun.finished.0.2.0",
        "dev.cdevents.testsuiterun.finished.0.2.0",
        "dev.cdevents.environment.created.0.2.0",
        "dev.cdevents.service.deployed.0.2.0",
        "dev.cdevents.pipelinerun.finished.0.2.0",
    ]
    for event_type in types:
        name = "-".join(event_type.split(".")[:-3])
        version = ".".join(event_type.split(".")[-3:])
        description = " ".join(event_type.split(".")[:-3]).title()
        evr = dict(name=name, version=version, description=description, type=event_type, schema={})
        event_receivers.append(evr)
    return event_receivers


# Generate a series of CDEvents for different services and event types
def generate_events(evrs: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate a CDEvent of each supported type for each service name.
    Ensures each generated event has unique ids/timestamps and includes
    fields commonly required by the included schemas.
    """
    events: List[Dict[str, Any]] = []
    event_receivers: List[Dict[str, Any]] = []
    names = ["foo", "bar", "baz", "qux"]
    types = [
        "dev.cdevents.pipelinerun.started.0.2.0",
        "dev.cdevents.pipelinerun.queued.0.2.0",
        "dev.cdevents.artifact.packaged.0.2.0",
        "dev.cdevents.artifact.published.0.2.0",
        "dev.cdevents.build.started.0.2.0",
        "dev.cdevents.build.finished.0.2.0",
        "dev.cdevents.testcaserun.finished.0.2.0",
        "dev.cdevents.testsuiterun.finished.0.2.0",
        "dev.cdevents.environment.created.0.2.0",
        "dev.cdevents.service.deployed.0.2.0",
        "dev.cdevents.pipelinerun.finished.0.2.0",
    ]
    release = datetime.now(timezone.utc).strftime("%Y.%m.%s")
    for idx, name in enumerate(names, start=1):
        chain_id = generate_ulid()
        env_id = f"cluster/0{idx}"
        sha = gen_sha(f"{name}-{env_id}")
        artifact_id = f"pkg:oci/{name}@sha256:{sha}"
        subject_base_id = f"{name}-{generate_ulid()[:8]}"
        source = f"urn:generator:{name}"
        sbom_uri = f"https://sbom.repo/{name}/{generate_ulid()}.spdx"
        for event_type in types:
            ev_id = generate_ulid()
            ts = get_current_timestamp()
            subject_type = event_type.split(".")[2].strip()
            event_receiver_id = evrs.get(event_type, {}).get("data", "<replace_with_evr_id>")
            if subject_type == "testsuiterun":
                subject_type = "testSuiteRun"
            elif subject_type == "testcaserun":
                subject_type = "testCaseRun"

            context = {
                "version": "0.4.1",
                "id": ev_id,
                "chainId": chain_id,
                "source": source,
                "type": event_type,
                "timestamp": ts,
            }

            # Build subject content by event/subject type
            if "pipelinerun.started" in event_type or "pipelinerun.queued" in event_type:
                subject = {
                    "id": subject_base_id,
                    "type": "pipelineRun",
                    "content": {
                        "pipelineName": f"pipeline-{subject_base_id}",
                        "url": f"https://pipelines.example/run/{subject_base_id}",
                    },
                }
            elif "pipelinerun.finished" in event_type:
                subject = {
                    "id": subject_base_id,
                    "type": "pipelineRun",
                    "content": {
                        "pipelineName": f"pipeline-{subject_base_id}",
                        "url": f"https://pipelines.example/run/{subject_base_id}",
                        "outcome": "pass",
                    },
                }
            elif "artifact.packaged" in event_type:
                # artifact events (packaged / published)
                subject = {
                    "id": subject_base_id,
                    "type": "artifact",
                    "content": {
                        "change": {
                            "id": artifact_id,
                            "source": f"https://git.example/{name}.git",
                        },
                        "sbom": {
                            "uri": sbom_uri,
                        },
                    },
                }
            elif "artifact.published" in event_type:
                # artifact events (packaged / published)
                subject = {
                    "id": subject_base_id,
                    "type": "artifact",
                    "content": {
                        "sbom": {
                            "uri": sbom_uri,
                        },
                        "user": "robot",
                    },
                }
            elif "build" in event_type:
                subject = {
                    "id": subject_base_id,
                    "type": "build",
                    "source":  f"https://git.example/{name}.git",
                    "content": {
                        "artifactId": artifact_id,
                    },
                }
                if "finished" in event_type:
                    subject["content"]["artifactId"] = artifact_id
            elif "testcaserun" in event_type:
                subject = {
                            "id": "myTestCaseRun123",
                            "source":  f"https://git.example/{name}.git",
                            "type": "testCaseRun",
                            "content": {
                                "outcome": "pass",
                            "environment": {"id": env_id, "source": source},
                            "testCase": {
                                "id": generate_ulid(),
                                "version": "1.0",
                                "name": f"{name} integration test case",
                                "type": "integration"
                            }
                            }
                        }
            elif "testsuiterun" in event_type:
                subject = {
                    "id": subject_base_id,
                    "type": "testSuiteRun",
                    "content": {
                        "environment": {"id": env_id, "source": source},
                        "outcome": "pass" if idx % 2 == 1 else "fail",
                        "testSuite": {
                            "id": generate_ulid(),
                            "version": "1.0",
                            "name": f"{name} integration tests",
                        },
                    },
                }
            elif "service" in event_type:
                subject = {
                    "id": subject_base_id,
                    "type": "service",
                    "content": {
                        "environment": {"id": env_id, "source": source},
                        "artifactId": artifact_id,
                    },
                }
            elif "environment" in event_type:
                subject = {
                    "id": env_id,
                    "type": "environment",
                    "content": {
                        "name": f"{name}-env-0{idx}",
                        "url": f"https://{name}-env-0{idx}.example.com",
                    },
                }
            else:
                subject = {"id": subject_base_id, "type": subject_type, "content": {}}

            event_template: Dict[str, Any] = {"context": context, "subject": subject}
            ev = dict(name=name, version="1.0.0", release=release, platform_id="x64-linux-oci-2", package="oci", description=f"{name} {event_type}", payload=event_template, success=True, event_receiver_id=event_receiver_id)
            # debug output to stdout for visibility when running interactively
            logger.debug(json.dumps(ev, indent=2))
            events.append(ev)

    return events

def post(url, data, headers=None, timeout=10.0):
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response
    except httpx.HTTPStatusError as e:
        print(f"HTTP error {e.response.status_code}: {e.response.text}")
        raise
    except Exception as e:
        print(f"Request failed: {e}")
        raise

def post_event_receiver(evr: Dict[str, Any],
    url: str = "http://localhost:8042",
    timeout: float = 10.0,
) -> httpx.Response:
    """
    Post a single JSON event receiver to the given webhook URL using httpx.
    Returns the httpx.Response on success, raises on network errors.
    """
    headers = {"Content-Type": "application/json"}
    endpoint = f"{url}/api/v1/receivers"
    resp = post(endpoint, data=evr, headers=headers, timeout=timeout)
    return resp

def post_event(
    event: Dict[str, Any],
    url: str = "http://localhost:8042",
    timeout: float = 10.0,
) -> httpx.Response:
    """
    Post a single JSON event to the given webhook URL using httpx.
    Returns the httpx.Response on success, raises on network errors.
    """
    headers = {"Content-Type": "application/json"}
    endpoint = f"{url}/api/v1/events"
    resp = post(endpoint, data=event, headers=headers, timeout=timeout)
    return resp

def post_event_receivers(
    evrs: List[Dict[str, Any]],
    url: str = "http://localhost:8042",
    timeout: float = 10.0,
) -> Dict[str, Dict[str, Any]]:
    """
    Post a list of event receivers sequentially. Returns a list of (evr_id, status_code, response_text).
    """
    results: Dict[str, Dict[str, Any]] = {}
    for evr in evrs:
        try:
            resp = post_event_receiver(evr, url=url, timeout=timeout)
            data=json.loads(resp.text)
            _id = data.get("data", "<no_id_returned>")
            results[evr["type"]] = dict(status=resp.status_code, data=_id)
        except Exception as e:
            results[evr["type"]] = dict(status=None, data=dict(error=str(e)))
    return results


def post_events(
    events: List[Dict[str, Any]],
    url: str = "http://localhost:8042",
    timeout: float = 10.0,
) -> List[Tuple[Optional[str], Optional[int], str]]:
    """
    Post a list of events sequentially. Returns a list of (event_id, status_code, response_text).
    """
    results: List[Tuple[Optional[str], Optional[int], str]] = []
    for ev in events:
        try:
            resp = post_event(ev, url=url, timeout=timeout)
            ev_id = resp.json().get("data")
            results.append((ev_id, resp.status_code, resp.text))
        except Exception as e:
            nvrpp = ev.get("description", "<no_description>")
            logger.error(f"Failed to post event {nvrpp}: {e}")
            results.append((None, None, str(e)))
    return results


def make_curl_command(event: Dict[str, Any], url: str) -> str:
    """
    Build a curl command that posts the given event to url.
    The JSON payload is shell-quoted.
    """
    # compact JSON to keep command shorter
    json_str = json.dumps(event, separators=(",", ":"), ensure_ascii=False)
    quoted_payload = shlex.quote(json_str)
    quoted_url = shlex.quote(url)
    return f"curl -sS -X POST -H 'Content-Type: application/json' -d {quoted_payload} {quoted_url}"


def main() -> None:
    """
    Generate event_receivers and events and either post them, show curl commands in a dry-run, or write to disk.
    """
    parser = argparse.ArgumentParser(
        description="Generate and post EPR event_receivers and events, print curl commands (dry-run), or write to disk."
    )
    parser.add_argument(
        "--url",
        "-u",
        default="http://localhost:8042",
        help="Webhook URL",
    )
    parser.add_argument("--timeout", "-t", type=float, default=10.0, help="Request timeout in seconds")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't send requests; print curl commands instead",
    )
    parser.add_argument(
        "--write-to-disk",
        action="store_true",
        help="Write events to disk as JSON files and skip posting",
    )
    args = parser.parse_args()

    url = args.url
    timeout = args.timeout

    event_receivers = generate_event_receivers()
    evr_results = {}
    if not args.dry_run:
        print(f"Posting {len(event_receivers)} event receivers to {url}/api/v1/receivers")
        evr_results = post_event_receivers(event_receivers, url=url, timeout=timeout)
    else:
        print("Dry run: curl commands for event receivers:")
        for evr in event_receivers:
            curl = make_curl_command(evr, f"{url}/api/v1/receivers")
            print(curl)

    if not args.dry_run:
        for evr_type, result in evr_results.items():
            status = result.get("status")
            status_str = str(status) if status is not None else "ERROR" 
            print(f"{evr_type}: {status_str}")
    events = generate_events(evrs=evr_results)
    if args.write_to_disk:
        os.makedirs("epr_reports/event_receivers", exist_ok=True)
        for evr in event_receivers:
            evr_type = evr["type"]
            filename = f"epr_reports/event_receivers/{evr_type.replace('.', '_')}.json"
            with open(filename, "w") as f:
                json.dump(evr, f, indent=2)
            print(f"Wrote event receiver {evr_type} to {filename}")
        os.makedirs("epr_reports/events", exist_ok=True)
        for idx, event in enumerate(events, start=1):
            filename = f"epr_reports/events/event_{idx:03d}_{event['name']}_{event['version']}.json"
            with open(filename, "w") as f:
                json.dump(event, f, indent=2)
            print(f"Wrote event {event['payload']['context']['id']} to {filename}")
        print(f"Wrote {len(events)} events to disk in the 'epr_reports/events' directory")
        # Write curl commands
        with open("epr_reports/curl_commands_event_receivers.txt", "w") as f:
            for evr in event_receivers:
                curl = make_curl_command(evr, f"{url}/api/v1/receivers")
                f.write(curl + "\n")
        with open("epr_reports/curl_commands_events.txt", "w") as f:
            for event in events:
                curl = make_curl_command(event, f"{url}/api/v1/events")
                f.write(curl + "\n")
        print("Wrote curl commands to epr_reports/curl_commands_event_receivers.txt and epr_reports/curl_commands_events.txt")
    if args.dry_run:
        print("Dry run: curl commands for events:")
        for event in events:
            curl = make_curl_command(event, f"{url}/api/v1/events")
            print(curl)
    else:
        results = post_events(events, url=url, timeout=timeout)
        success = 0
        for ev_id, status, resp_text in results:
            status_str = str(status) if status is not None else "ERROR"
            print(f"{ev_id}: {status_str}")
            if status and 200 <= status < 300:
                success += 1
        print(f"Posted {success}/{len(results)} events successfully")


if __name__ == "__main__":
    main()
