# CloudEvents

## Overview

[CloudEvents](https://github.com/cloudevents/spec) is a specification for describing event data in common formats to provide interoperability across services, platforms and systems.

In this session we will learn about CloudEvents basics

## Requirements

Python environment

## Setup

In this section of the workshop we will need to create a few files and folders.

To get started we will make a directory for the tutorial.

```bash
mkdir ./cloudevents
cd ./cloudevents
```

Clone the spec and the python sdk.

```bash
git clone git@github.com:cloudevents/spec.git

git clone git@github.com:cloudevents/sdk-python.git
```

Create and activate a Python virtual environment (Unix/macOS)

```bash
python3 -m venv venv
source venv/bin/activate
```

If you are on Windows (PowerShell), use:

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Upgrade pip and install required packages

```bash
pip install --upgrade pip
pip install cloudevents flask requests pytest
```

Verify the sample files exist (optional)

```bash
ls -l sdk-python/samples/http-json-cloudevents/
```

Run the sample Flask server (binds to port 3000)
Leave this terminal running to accept incoming CloudEvents.

```bash
python3 sdk-python/samples/http-json-cloudevents/json_sample_server.py
```

If you prefer to run the server in the background (Unix), open a new terminal or use: (from the project dir)

```bash
nohup python3 src/sdk-python/samples/http-json-cloudevents/json_sample_server.py > server.log 2>&1 &
```

In a second terminal (activate the same venv), send sample events
Activate venv in the second terminal too:

```bash
source ./venv/bin/activate
python3 sdk-python/samples/http-json-cloudevents/client.py http://localhost:3000/
```

You should see client output confirming sent events and the server terminal should print messages like:

```bash
Found <id> from <source> with type <type> and specversion <specversion>
```

Run the included pytest tests (these use Flask test_client and do not require the server process)

```bash
pytest -q sdk-python/samples/http-json-cloudevents/json_sample_test.py
```

Quick cleanup when finished

```bash
deactivate
```

Troubleshooting quick commands:

- Check installed cloudevents package version:

```bash
pip show cloudevents
```

- If "connection refused" when running client, ensure the server is running on port 3000:

```bash
ss -ltnp | grep 3000   # or: lsof -i :3000
```

- To inspect request headers on the server, edit: `sdk-python/samples/http-json-cloudevents/json_sample_server.py` add: `print(dict(request.headers))` to the file
