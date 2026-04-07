# Architecture Design

NetShield IDS operates through three distinct layers: Packet Capture, Event Processing, and Presentation.

## 1. Packet Capture (Sniffer) Layer
Located in `backend/app/sniffer.py`. This layer uses the `scapy` library configured to operate on a raw socket. The Python process must run as `root` (or with `CAP_NET_RAW` Linux capabilities) to have access to the raw packets hitting the Network Interface Card (NIC). Packet metadata (source IP, destination IP, TCP/UDP/ICMP protocol flags) is extracted without capturing the raw payload data to preserve memory and privacy. 

## 2. Event Processing (Detection) Layer
Located in `backend/app/detector.py`. As packets stream in, they are grouped by their Source IP into a time-based queue using a sliding window algorithm (defined by `DETECTION_WINDOW_SECONDS`).
The processing engine continuously trims packets that fall out of the sliding window. It evaluates the remaining packets against configurable thresholds:
- SYN Flood (`SYN_RATE_THRESHOLD`)
- UDP Flood (`UDP_RATE_THRESHOLD`)
- ICMP Flood (`ICMP_RATE_THRESHOLD`)
- Volumetric/Generic Flood (`PACKET_RATE_THRESHOLD`)

If a threshold is breached, a `DetectionEvent` is generated. The process employs a simple "cooldown" mechanism to prevent flooding the UI with identical alerts for the continuous volumetric attack.

Once an event is triggered, the `GeoIpResolver` fetches the latitude and longitude from the locally mounted MaxMind DB.

## 3. Presentation (Broadcasting) Layer
Located in `backend/app/main.py` and the `frontend/` directory. 
The FASTAPI application acts as an asynchronous web server spanning two components:
- Event History REST routes: provides cached events.
- WebSocket Connection Manager: Iterates over connected browser clients, pushing newly materialized `DetectionEvent` JSON payloads directly to their WebSockets.

The JavaScript frontend utilizes `Leaflet.js` to asynchronously map these coordinates.
