# Troubleshooting

## Redpanda

Error Crash:

```bash
docker volume ls | grep server-dependencies_redpanda-data
```

```text
local     server-dependencies_redpanda-data
```

```bash
docker volume rm server-dependencies_redpanda-data
```

## Postgres

Error Crash:

```bash
docker volume ls | grep server-dependencies_postgres-data
```

```text
local     server-dependencies_postgres-data
```

```bash
docker volume rm server-dependencies_postgres-data
```

## Python

Error:

```text
ModuleNotFoundError: No module named 'pip'
```

```bash
python -m ensurepip --upgrade
```
