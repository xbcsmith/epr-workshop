#!/usr/bin/env python3

import argparse
import json
import shlex
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx
import ulid


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


# Generate a series of CDEvents for different services and event types
def generate_events() -> List[Dict[str, Any]]:
    """
    Generate a CDEvent of each supported type for each service name.
    Ensures each generated event has unique ids/timestamps and includes
    fields commonly required by the included schemas.
    """
    events: List[Dict[str, Any]] = []
    names = ["foo", "bar", "baz", "qux"]
    types = [
        "dev.cdevents.pipelinerun.started.0.2.0",
        "dev.cdevents.pipelinerun.queued.0.2.0",
        "dev.cdevents.artifact.packaged.0.2.0",
        "dev.cdevents.artifact.published.0.2.0",
        "dev.cdevents.build.finished.0.2.0",
        "dev.cdevents.testsuiterun.finished.0.2.0",
        "dev.cdevents.environment.created.0.2.0",
        "dev.cdevents.service.deployed.0.2.0",
        "dev.cdevents.pipelinerun.finished.0.2.0",
    ]

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
            if subject_type == "testsuiterun":
                subject_type = "testSuiteRun"

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
                    "content": {
                        "artifactId": artifact_id,
                    },
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

            # debug output to stdout for visibility when running interactively
            print(json.dumps(event_template, indent=2))
            events.append(event_template)

    return events


def post_event(
    event: Dict[str, Any],
    url: str = "http://localhost:8080/webhook/000-cdevents",
    timeout: float = 10.0,
) -> httpx.Response:
    """
    Post a single JSON event to the given webhook URL using httpx.
    Returns the httpx.Response on success, raises on network errors.
    """
    headers = {"Content-Type": "application/json"}
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=event, headers=headers)
            resp.raise_for_status()
            return resp
    except httpx.HTTPStatusError as e:
        # non-2xx response
        print(f"HTTP error {e.response.status_code}: {e.response.text}")
        raise
    except Exception as e:
        # network or other errors
        print(f"Request failed: {e}")
        raise


def post_events(
    events: List[Dict[str, Any]],
    url: str = "http://localhost:8080/webhook/000-cdevents",
    timeout: float = 10.0,
) -> List[Tuple[Optional[str], Optional[int], str]]:
    """
    Post a list of events sequentially. Returns a list of (event_id, status_code, response_text).
    """
    results: List[Tuple[Optional[str], Optional[int], str]] = []
    for ev in events:
        ev_id = ev.get("context", {}).get("id")
        try:
            resp = post_event(ev, url=url, timeout=timeout)
            results.append((ev_id, resp.status_code, resp.text))
        except Exception as e:
            results.append((ev_id, None, str(e)))
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
    Generate events and either post them, show curl commands in a dry-run, or write to disk.
    """
    parser = argparse.ArgumentParser(
        description="Generate and post CDEvents, print curl commands (dry-run), or write to disk."
    )
    parser.add_argument(
        "--url",
        "-u",
        default="http://localhost:8080/webhook/000-cdevents",
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
    dry_run = args.dry_run
    write_to_disk = args.write_to_disk

    events = generate_events()
    print(f"Generated {len(events)} events, url={url}, dry_run={dry_run}, write_to_disk={write_to_disk}")

    if dry_run:
        for ev in events:
            cmd = make_curl_command(ev, url)
            print()
            print(cmd)
            print()
        return
    elif write_to_disk:
        for ev in events:
            ev_id = ev.get("context", {}).get("id")
            filename = f"event_{ev_id}.json"
            with open(filename, "w") as f:
                json.dump(ev, f, indent=2)
            print(f"Wrote {filename}")
        return

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
