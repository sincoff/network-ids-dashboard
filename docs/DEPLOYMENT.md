# Deployment Guide

NetShield IDS consists of two parts: the backend sniffer (which **must** run on an Ubuntu VM) and the frontend dashboard (which can be hosted anywhere).

This guide covers two environments:
1. **Ubuntu 24.04 LTS VM**: Running the backend sniffer, API, and the dashboard together locally via Nginx (Self-Hosted).
2. **Vercel / Next.js hosting**: Hosting the frontend dashboard globally on Vercel while connecting back to your Ubuntu VM.

---

## 1. Ubuntu 24.04 LTS Virtual Machine (Backend & Local Dashboard)

Because the Python backend uses `scapy` to capture raw network packets, it requires `root` privileges (`CAP_NET_RAW`) to run. It **must** run on a Linux Virtual Machine or physical server.

### Automated Production Setup

We provide a one-command setup script that will create a production-ready environment on Ubuntu 24.04 LTS. It configures Systemd, Nginx, Python Virtual Environments, and applies basic firewall rules.

1. **Clone the repository on the target VM:**
   ```bash
   git clone https://github.com/your-org/network-ids-dashboard.git
   cd network-ids-dashboard
   ```

2. **Download the GeoIP Database (Required for Mapping)**
   Download the `GeoLite2-City.mmdb` from MaxMind and place it in the `data/` folder:
   ```bash
   mkdir -p data
   # Assuming you downloaded the database into this directory
   ```

3. **Configure Environment:**
   ```bash
   cp .env.example .env
   # Edit .env and set SNIFF_INTERFACE to your network interface (e.g. enp0s3)
   ```

4. **Run the Deployment Script:**
   ```bash
   sudo bash deploy/setup.sh
   ```

5. **Run Firewall Configuration (Optional but Recommended):**
   ```bash
   sudo bash deploy/ufw-rules.sh
   ```

### Verification

Check the status of the systemd daemon:
```bash
sudo systemctl status network-ids
```

You can now visit the VM's IP address in your browser: `http://<your-vm-ip>/`

---

## 2. Vercel Hosting (Frontend)

If you prefer to host the dashboard interface on the public internet, you can deploy the `frontend` folder to Vercel for free. This allows you to have a public HTTPS dashboard that connects securely back to your Ubuntu backend.

### Prerequisites for Vercel Deployment
- A free account on [Vercel](https://vercel.com).
- Your Ubuntu backend **must** be accessible via a public IP address or a Domain name (port 80 or 443).
- The `CORS_ORIGINS` setting in your backend's `.env` must be updated to allow the Vercel domain.

### Deployment Steps (via Vercel CLI)

1. **Install Vercel CLI locally** (Requires Node.js):
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel:**
   ```bash
   vercel login
   ```

3. **Deploy the project:**
   Run the deployment command from the root of the repository:
   ```bash
   vercel
   ```
   Follow the prompts. Ensure it detects the project and is using the `vercel.json` config.

4. **Configure the Backend URL on Vercel:**
   By default, the Vercel dashboard will look for the backend API on the *same domain* (which will fail, because Vercel only hosts static files). You need to tell the Vercel dashboard where the Ubuntu VM is located.

   In the Vercel Dashboard for your project, go to **Settings > Environment Variables**.
   Add a new variable:
   - **Key**: `VITE_BACKEND_URL` (If using a bundler) OR configure the `backend-url` meta tag in your `index.html`.
   *Wait, actually in this project, we read the backend URL securely from the meta-tag. Let's configure it correctly for Vercel.*

   **Alternative Configuration for Vercel Static Hosting:**
   Since this is a static site without a JS bundler, you should edit the `vercel.json` or explicitly set the `<meta name="backend-url" content="http://<your-vm-ip>">` inside `frontend/index.html` *before* running `vercel deploy`.

   *Recommended method for this repo:* Edit `frontend/index.html` line 20:
   ```html
   <meta name="backend-url" content="http://YOUR.UBUNTU.VM.IP" />
   ```
   Then run `vercel --prod`.

### Cross-Origin Resource Sharing (CORS)

If you host the frontend on Vercel, you **must** update your VM backend to allow requests from the Vercel domain.

On the Ubuntu VM, edit `/opt/network-ids-dashboard/.env`:
```ini
# Add your vercel domain
CORS_ORIGINS=https://my-dashboard.vercel.app,http://localhost:3000
```
Then restart the backend:
```bash
sudo systemctl restart network-ids
```
