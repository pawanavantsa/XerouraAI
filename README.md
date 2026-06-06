# Xeroura CSBot — Self-Hosted Demo

Free-tier demo deployment of the Xeroura AI customer support stack on **one VM** (Oracle Cloud Always Free recommended) with **Docker Compose** and **Cloudflare Tunnel** for public HTTPS — no ngrok, no paid GCP database/Redis.

This folder is a **standalone copy** of the main app, tuned for demo hosting. It is **not** wired for Cloud Run / Cloud SQL / Memorystore.

## Stack (all on one VM)

| Service | Role |
|---------|------|
| **backend** | Django + Daphne (API, webhooks, WebSockets) |
| **frontend** | Next.js agent dashboard |
| **db** | PostgreSQL 16 + pgvector |
| **redis** | Django Channels |
| **cloudflared** | Free HTTPS tunnel (replaces ngrok) |

## Quick start (after VM is ready)

```bash
git clone <your-demo-repo-url>
cd xeroura-csbot-demo
cp .env.example .env
# Edit .env — see DEPLOY.md
docker compose up -d --build
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python scripts/seed_knowledge_base.py   # optional FAQ seed
```

Open your dashboard at `https://<APP_PUBLIC_HOST>` (from `.env`).

Full setup: **[DEPLOY.md](./DEPLOY.md)**

## What still costs money

- **Anthropic API** — required for AI replies (pay per token)
- **OpenAI API** — optional, better knowledge-base search
- **Twilio / WhatsApp / Gmail** — only if you enable those channels

**VM + tunnel + Postgres + Redis on Oracle Always Free ≈ $0/month** (within free tier limits).

## Local development (optional)

To run without Cloudflare on your laptop, use the **main** [Xeroura-CSBot](https://github.com/Xeroura-Technologies-PVT-Limited/XerouraAI) repo with its original `docker-compose.yml` and `DEBUG=True`.

## Publish as its own GitHub repo

This directory is initialized as a separate git repo. Push to a new remote:

```bash
cd xeroura-csbot-demo
git remote add origin git@github.com:YOUR_ORG/xeroura-csbot-demo.git
git push -u origin main
```
