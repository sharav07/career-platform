# Architecture diagrams

Both diagrams use Mermaid, which GitHub renders in the browser. Domain: `sharavjiwrajka.me`. DNS provider: Cloudflare (DNS only for records that reach my own server).

## Azure (original deployment, kept running as evidence and as the rollback target)

```mermaid
flowchart LR
  V[Visitor browser] -- "1. DNS lookup, UDP/TCP 53" --> CF[(Cloudflare DNS<br/>A record to 68.155.158.254<br/>DNS only)]
  V -- "2. HTTPS, TCP 443<br/>(HTTP 80 redirects to 443)" --> NSG{{Azure NSG firewall<br/>22 my /32 only, 80, 443}}
  NSG --> NG["Nginx on the VM<br/>public 80/443, Let's Encrypt cert"]
  NG -- "plain HTTP, 127.0.0.1:8000<br/>not reachable from outside" --> UV["Uvicorn, 2 workers<br/>FastAPI app, systemd service"]
  UV -- "file read, no network" --> DB[("SQLite resume.db<br/>on the VM disk")]
  V -. "GA4 tag loads only after<br/>'Accept analytics'" .-> GA[(Google Analytics 4<br/>HTTPS 443)]
  ME["Me over SSH, TCP 22<br/>key only"] -.-> NSG
```

## Railway (target deployment)

```mermaid
flowchart LR
  V[Visitor browser] -- "1. DNS lookup" --> CF[(Cloudflare DNS<br/>root CNAME to Railway<br/>DNS only)]
  V -- "2. HTTPS, TCP 443<br/>Railway-managed certificate" --> EDGE["Railway edge proxy"]
  EDGE -- "HTTP to the service PORT" --> APP["Web service: Uvicorn, 2 workers<br/>built from GitHub main"]
  APP -- "PostgreSQL protocol, TCP 5432<br/>Railway private network" --> PG[("Railway PostgreSQL<br/>with volume")]
  GH[GitHub repo, main] -- "push triggers build and deploy" --> APP
  V -. "GA4 tag after consent" .-> GA[(Google Analytics 4)]
```

## Email path (unchanged by the migration)

Email never touches the web server. Only DNS records matter.

```mermaid
flowchart LR
  EXT[Outside mailbox, e.g. Gmail] -- "SMTP 25 to the MX hosts<br/>found in DNS" --> ZMX["Zoho MX hosts<br/>mx.zoho.com 10, mx2 20, mx3 50"]
  ZMX --> ZBOX[(Zoho mailbox<br/>me@sharavjiwrajka.me)]
  ZBOX -- "send: Zoho signs with DKIM<br/>selector zmail" --> EXT
  CF[(Cloudflare DNS<br/>MX, SPF TXT, DKIM TXT, DMARC TXT)] -. "receiver checks these records" .-> EXT
```

## Analytics path

1. The visitor loads the page from Azure or Railway (HTML only, no Google code yet).
2. The visitor clicks **Accept analytics**. `static/analytics.js` then adds Google's `gtag.js`, using the public measurement ID from `data-ga-id`.
3. The browser sends events (`page_view`, outbound `click`) straight to Google over HTTPS. The web server and the database are not involved.
4. GA4 Realtime shows them. Evidence: `docs/evidence/ex06.md`.

## What lives where

| Piece | Azure | Railway |
| --- | --- | --- |
| Code | `git pull` on the VM | built from GitHub `main` |
| Database | SQLite file on the VM | managed PostgreSQL |
| TLS | Let's Encrypt via Certbot, renewed by `certbot.timer` | Railway-issued, renewed by Railway |
| DNS | Cloudflare | Cloudflare (same zone) |
| Email | Zoho (same) | Zoho (same) |
