# Examples

```bash
curl --location --request POST 'http://localhost:8042/api/v1/receivers' --header 'Content-Type: application/json' --data @event_receiver.json

curl --location --request POST 'http://localhost:8042/api/v1/groups' --header 'Content-Type: application/json' --data @event_receiver_group.json

curl --location --request POST 'http://localhost:8042/api/v1/events' --header 'Content-Type: application/json' --data @event.json
```

```bash
cat rest_response.json | jq .data
```
