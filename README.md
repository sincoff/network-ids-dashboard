# Network IDS Dashboard

## Who does what

| Role | Machine | Task |
|------|---------|------|
| **Target** | VM that runs the app | Install dependencies, run the server, open the dashboard in a browser. |
| **Attacker** | Second VM (or same VM for testing) | Install `hping3`, run the flood command against the target IP. **Lab network only.** |

---

## Target VM (run the dashboard)

```bash
cd ~/network-ids-dashboard

sudo apt update
sudo apt install -y python3-pip python3-venv libpcap-dev

python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

cp .env.example .env
```

If packet capture errors on startup, set your real interface in `.env` (see `ip -br a`), e.g. `SNIFF_INTERFACE=ens160`.

Optional: put `GeoLite2-City.mmdb` in `data/` for real map locations. Without it, the app still runs.

```bash
sudo -E .venv/bin/uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
```

Open: `http://127.0.0.1:8000` or `http://<this-vm-ip>:8000`

---

## Attacker VM (generate test traffic)

```bash
sudo apt update
sudo apt install -y hping3
```

Replace `<target-ip>` with the target VM’s IP (e.g. `192.168.182.138`).

```bash
sudo hping3 -S --flood --rand-source -p 80 <target-ip>
```

Stop with `Ctrl+C`.

Or use the helper script from a copy of the repo:

```bash
chmod +x scripts/simulate_ddos.sh
./scripts/simulate_ddos.sh <target-ip> syn
```

Only use on your isolated class VMs.
