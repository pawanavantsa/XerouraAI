# Deploy Xeroura CSBot Demo (free VM + Cloudflare Tunnel)

Step-by-step guide for **Oracle Cloud Always Free** (or any Ubuntu VM). Total infra cost: **$0** on Oracle’s free tier; you only pay for AI API usage.

---

## Overview

```
Internet → Cloudflare (HTTPS) → cloudflared container → backend:8000 / frontend:3000
                                      ↓
                              Docker network on VM
                         db (Postgres) + redis + backend + frontend
```

No inbound ports 80/443 on the VM firewall — only SSH (22). Cloudflare Tunnel connects **outbound**.

---

## Part 1 — Oracle Cloud VM (Always Free)

1. Sign up at [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/).
2. Create a **Compute → Instance**:
   - **Shape:** Ampere A1 (ARM) — up to 4 OCPU / 24 GB RAM on free tier, or smaller
   - **Image:** Ubuntu 22.04 or 24.04
   - **Boot volume:** 50–100 GB
   - **Networking:** assign a public IP
   - **SSH key:** add your public key
3. Note the **public IP** and SSH in:
   ```bash
   ssh ubuntu@<VM_PUBLIC_IP>
   ```

### Install Docker (on the VM)

```bash
sudo bash scripts/setup-vm.sh
```

Or clone first, then run the script from the repo root.

Add your user to the docker group (log out/in after):

```bash
sudo usermod -aG docker $USER
```

---

## Part 2 — Cloudflare Tunnel (free HTTPS)

You need a domain on Cloudflare (free plan is fine).

### 2a. Create the tunnel

1. [Cloudflare Zero Trust](https://one.dash.cloudflare.com/) → **Networks** → **Tunnels**
2. **Create a tunnel** → name it e.g. `xeroura-demo`
3. Choose **Docker** as connector → copy the **`TUNNEL_TOKEN`** (long string)
4. **Do not start the connector on the VM yet** — Docker Compose will run it

### 2b. Configure public hostnames

In the tunnel’s **Public Hostname** tab, add **two** routes:

| Public hostname | Service type | URL |
|-----------------|--------------|-----|
| `demo-api.yourdomain.com` | HTTP | `backend:8000` |
| `demo-app.yourdomain.com` | HTTP | `frontend:3000` |

Use your real subdomains. WebSockets (`wss://`) work through the tunnel automatically.

---

## Part 3 — Configure `.env`

On the VM:

```bash
git clone <your-demo-repo-url>
cd xeroura-csbot-demo
cp .env.example .env
nano .env
```

Set at minimum:

| Variable | Example |
|----------|---------|
| `SECRET_KEY` | long random string |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `demo-api.yourdomain.com` |
| `TRUST_X_FORWARDED_PROTO` | `True` |
| `API_PUBLIC_HOST` | `demo-api.yourdomain.com` |
| `APP_PUBLIC_HOST` | `demo-app.yourdomain.com` |
| `NEXT_PUBLIC_API_URL` | `https://demo-api.yourdomain.com` |
| `NEXT_PUBLIC_WS_URL` | `wss://demo-api.yourdomain.com` |
| `PUBLIC_BASE_URL` | `https://demo-api.yourdomain.com` |
| `CLOUDFLARE_TUNNEL_TOKEN` | token from step 2a |
| `POSTGRES_PASSWORD` | strong password (match in `DATABASE_URL`) |
| `ANTHROPIC_API_KEY` | valid `sk-ant-...` key |

Rebuild frontend whenever you change `NEXT_PUBLIC_*` URLs:

```bash
docker compose up -d --build
```

---

## Part 4 — Start the stack

```bash
docker compose up -d --build
```

Check status:

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f cloudflared
```

First-time setup:

```bash
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python scripts/seed_knowledge_base.py
```

---

## Part 5 — Verify

1. **API:** `curl https://demo-api.yourdomain.com/api/` (or any known endpoint)
2. **Dashboard:** open `https://demo-app.yourdomain.com` → sign up / log in
3. **Logs:** no `401` from Anthropic, no DB connection errors

### WhatsApp / Twilio webhooks

Point Meta/Twilio callback URLs to:

`https://demo-api.yourdomain.com/api/webhooks/...`

Set the same base in `PUBLIC_BASE_URL`.

---

## Operations

| Task | Command |
|------|---------|
| View logs | `docker compose logs -f backend` |
| Restart | `docker compose restart backend` |
| Update app | `git pull && docker compose up -d --build` |
| Backup DB | `docker compose exec db pg_dump -U postgres support_agent > backup.sql` |
| Shell | `docker compose exec backend python manage.py shell` |

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `DisallowedHost` | Add your API hostname to `ALLOWED_HOSTS` |
| `401 invalid x-api-key` | Fix `ANTHROPIC_API_KEY` in `.env`, restart backend |
| Dashboard can’t reach API | Rebuild frontend after fixing `NEXT_PUBLIC_API_URL` |
| Tunnel not connecting | Check `CLOUDFLARE_TUNNEL_TOKEN` and `cloudflared` logs |
| WebSocket fails | Ensure tunnel hostname points to `backend:8000`, use `wss://` in `NEXT_PUBLIC_WS_URL` |
| Poor KB answers | Set `OPENAI_API_KEY` and re-seed knowledge base |

---

## Why this repo is separate

The main **Xeroura-CSBot** repo targets production GCP (Cloud Run, Cloud SQL, Memorystore). This demo repo keeps everything on one VM with zero managed-cloud DB/Redis cost — simpler and free for demos.
