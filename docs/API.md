# NetShield API Reference

The backend provides several REST endpoints and a WebSocket connection for real-time data.

## REST API

### `GET /api/health`
Health check endpoint to verify the backend is running.
**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600.5,
  "sniffer_running": true
}
```

### `GET /api/status`
Returns metrics regarding the live state of the application.
**Response**:
```json
{
  "sniffer_running": true,
  "recent_events": 25,
  "websocket_clients": 2,
  "packets_processed": 50000,
  "version": "1.0.0"
}
```

### `GET /api/stats`
Aggregated statistics spanning the rolling history window.
**Response**:
```json
{
  "total_alerts": 142,
  "unique_sources": 5,
  "threat_level": "HIGH",
  "classifications": {
    "SYN_FLOOD": 100,
    "VOLUMETRIC": 42
  },
  "tracked_sources": 350,
  "total_observations": 52000
}
```

### `GET /api/events/recent`
Returns the most recent detection events (up to the `HISTORY_LIMIT`).
**Response**:
```json
[
  {
    "timestamp": "2026-04-07T12:00:00Z",
    "source_ip": "1.2.3.4",
    "destination_ip": "192.168.1.1",
    "protocol": "TCP",
    "packet_count_window": 125,
    "classification": "SYN_FLOOD",
    "location": {
      "source_ip": "1.2.3.4",
      "country": "United States",
      "city": "New York",
      "latitude": 40.7128,
      "longitude": -74.0060
    }
  }
]
```

## WebSocket API

### `WS /ws/events`
Connect to this endpoint to receive live event payloads as threats are detected. The payload format is identical to the items in the `/api/events/recent` array. 
The client is not expected to send any messages to the server.
