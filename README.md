# Career Platform

A small personal website for Sharav Jiwrajka: a profile, an experience list and a projects section, all read from a database on every request. It is the starting point for the career platform I am building in ISBA 4775 at LMU.

- Live address: https://sharavjiwrajka.me (`www` redirects to it)
- Repository: https://github.com/sharav07/career-platform
- Submission index: [docs/project-1-submission.md](docs/project-1-submission.md)

Stack: Python, FastAPI, Jinja templates, SQLite (Azure) and PostgreSQL (Railway), Uvicorn, Cloudflare DNS, Zoho Mail, Google Analytics 4.

## How it behaves

| Situation | Response |
| --- | --- |
| Database healthy | HTTP 200, full page |
| Database unreachable or not set up | HTTP 503, profile still visible, "Projects temporarily unavailable" |
| Projects table empty | HTTP 200, "No projects published yet." (no sample content) |
| Database comes back | Next request is healthy, no restart (a new connection per request) |
| `/health` | Always 200 while the app is running (it does not touch the database) |

Tests: `uv run pytest`. PostgreSQL parity tests run when `TEST_DATABASE_URL` points at a scratch database.

## Set up and update

Run locally:

```bash
uv sync
uv run python -c "from app.importer import import_seed; import_seed('resume.db', 'data/resume.json')"
uv run uvicorn app.main:app --reload
```

Configuration (all optional): `DATABASE_URL` (PostgreSQL URL, wins when set), `DATABASE_PATH` (SQLite file, default `resume.db`), `SEED_PATH`, `GA_MEASUREMENT_ID`.

Update the live site: push to `main`. Railway builds from the `main` branch of this repository (see "Deployment" below for what is and is not verified). The Azure VM is updated by `git pull` over SSH and is kept only as the rollback target.

## Deployment

- Azure (original): Ubuntu VM, Nginx on 80/443, Uvicorn with 2 workers under systemd on `127.0.0.1:8000`, SQLite file, Let's Encrypt certificate. Evidence: [ex03](docs/evidence/ex03.md), [how this site is secured](docs/how-this-site-is-secured.md), [Azure plan](docs/superpowers/plans/2026-09-24-azure-vm-migration.md).
- Railway (current): web service built from GitHub with Railpack, managed PostgreSQL with a volume, `railway.toml` for the start command and health check. Evidence: [railway-migration.md](docs/evidence/railway-migration.md), plan: [2026-10-26-railway-migration.md](docs/superpowers/plans/2026-10-26-railway-migration.md).

Diagrams (Azure, Railway, email and analytics paths): [docs/architecture.md](docs/architecture.md).

## How the migration kept the current data

The Azure database was the source of truth, not the seed. I changed the profile headline on Azure only, exported every table to JSON, loaded that into Railway PostgreSQL, and compared row counts and content hashes table by table. All ten tables matched, and the rendered pages from both sites were identical. Details and real output: [railway-migration.md](docs/evidence/railway-migration.md). The tools are `scripts/sqlite_export.py`, `scripts/load_export.py` and `scripts/compare_data.py`.

## Who manages what

| Layer | Azure VM (IaaS) | Railway (PaaS) | What stays my job on Railway |
| --- | --- | --- | --- |
| Operating system | Me (patches, reboots) | Railway | Nothing |
| Language runtime | Me (installed Python and uv) | Railway builder picks Python from `pyproject.toml` | Keep `requires-python` and the lockfile sane |
| Web entry point | Me (Nginx config) | Railway edge proxy | The start command and port |
| TLS certificate | Me (Certbot, renewal timer) | Railway issues and renews | Keeping DNS correct so issuance works (see failure 4) |
| Application code | Me (`git pull`, restart service) | Me (push to `main`, Railway builds) | All of it |
| Configuration | Me (files on the VM) | Me (Railway variables) | Variables, and not leaking them |
| Database software | Me (SQLite file, no server) | Railway (PostgreSQL service) | Schema, queries, and compatibility |
| Data | Me (the file on the VM disk) | Me (volume is Railway's, contents are mine) | Backups and migrations. This is not automatic on the trial |
| DNS | Me (Cloudflare) | Me (Cloudflare) | Records and the proxy setting |

PaaS is not maintenance-free. I still own the code, the data, the DNS, the variables, and the credentials, as the Oct 21 Railway incident showed.

## Rollback

Code:
1. Railway keeps earlier deployments. In the service's Deployments list, redeploy the last good one, or
2. `git revert <bad commit>` and push to `main`.

Domain (back to Azure): in Cloudflare, replace the root `CNAME` with an `A` record to `68.155.158.254` (DNS only). The Azure VM is still running and still holds a valid certificate. DNS propagation time depends on the TTL (the record TTL is Auto).

Data: the site has no write path, so Railway PostgreSQL contains nothing that Azure lacks. If a write path is ever added, a rollback must first export PostgreSQL back into the SQLite file with a reverse of `scripts/load_export.py`, or those writes are lost. Database schema changes are not versioned yet (limitation below), so a schema change needs its own manual undo script.

## Decisions

1. **Migrate to Railway PostgreSQL instead of staying on the VM.** Alternatives: keep Azure only (cheapest to understand, but I patch and renew everything), or move to a managed platform. I chose Railway because the course goal was to compare who manages what, and because it removes OS and certificate chores. Cost: trial credit runs out and Railway had a security incident and paused trial builds on Oct 21.
2. **Managed versus self-hosted email.** I used Zoho Mail (free plan) rather than running a mail server on the VM or only forwarding with Cloudflare Email Routing. Self-hosting mail means deliverability, reverse DNS and blocklists; Routing alone cannot send as my domain. Zoho gives a real mailbox with DKIM signing, and I publish SPF, DKIM and DMARC for it. See [ex06](docs/evidence/ex06.md).
3. **SQLite first, then PostgreSQL.** SQLite needed no server and fitted a one-VM, read-mostly site, so the first deployment was simple. PostgreSQL is what the managed platform offers. The data layer has one translation point (`app/db.py`) so both work from the same code.
4. **Export JSON and load, instead of `pg_dump`/a raw file copy.** A SQLite file cannot be restored into PostgreSQL, and the container cannot reach Railway's database port directly. A table-by-table JSON export is engine-neutral and lets me compare both sides with hashes.

## Investigated failures

Each follows the same shape: symptom, evidence, diagnosis, repair, repeated check.

1. **Application or database dependency (real, Azure build):** [ex03.md](docs/evidence/ex03.md) section 3, a region-policy denial found by reading Azure Policy.
2. **DNS or TLS (deliberate lab, simulated):** [ex05.md](docs/evidence/ex05.md). This is the course's supplied simulation, not my real system, and it says so.
3. **Railway database empty after first deploy (real, 2026-10-26):** the site returned 503 with "Projects temporarily unavailable" because the pre-deploy data load did not run. I confirmed the 503, loaded the data from the service console, verified hashes, and saw the same URL return 200 without a restart. [railway-migration.md](docs/evidence/railway-migration.md) sections 2 to 5.
4. **TLS certificate on the root domain (real, 2026-10-26):** after I changed the root record to DNS only, Railway reported "Let's Encrypt rate limit reached" and the root showed a certificate error. I put the record back to Proxied so Cloudflare serves the certificate, and the site recovered. Evidence and the current state are in [railway-migration.md](docs/evidence/railway-migration.md) section 7.

## Email and analytics

- Zoho send, receive, reply and SPF/DKIM/DMARC results: [ex06.md](docs/evidence/ex06.md), [zoho-header-check.md](docs/evidence/zoho-header-check.md).
- GA4 page view and click verification, and what each event means: [ex06.md](docs/evidence/ex06.md) section 3. The tag loads only after a visitor accepts the banner.

## Costs, credits and cleanup

Checked 2026-10-26 unless noted.

| Service | Cost or credit | Expires or renews | Cleanup |
| --- | --- | --- | --- |
| Railway trial | Dashboard shows "13 days or $5.00 left" | About 2026-11-08 by that count (not independently verified) | Delete the project before the trial ends or move the site as the instructor directs |
| Azure VM and disk | Azure for Students credit. Amount left: **not verified** | Credit expiry: **not verified** | Keep running until the instructor says otherwise, then delete resource group `rg-career-platform` |
| Cloudflare DNS | Free plan | n/a | None |
| Zoho Mail | Free plan (per the course instructions) | n/a | None |
| Domain `sharavjiwrajka.me` | Registrar price and renewal date: **not verified** | **not verified** | Check the registrar's renewal date |
| Google Analytics 4 | Free | n/a | None |

## Remaining limitations

- The root domain currently uses Cloudflare's proxy (orange cloud) with Cloudflare's certificate, not Railway's own certificate. The brief asks for DNS only. See failure 4 and the evidence file for the current state.
- The pre-deploy data load in `railway.toml` did not run on Railway; the load was done by hand from the console. It is safe to re-run (it skips a non-empty database).
- No schema migration tooling. The schema is created with `CREATE TABLE IF NOT EXISTS`.
- Railway database backups are not configured. Data loss on the trial is possible; the Azure export in `data/migrations/` is the only copy besides the live databases.
- Railway reported that environment variables may have been read in its Oct 21 incident. The instructor asked to rotate the Postgres password and redeploy once trial builds are back. Status is in the evidence file.

## Reflection (written afterward, 2026-10-26, with help from Claude)

I understand more clearly now that a deployment has two separate halves: the code, which Git carries, and the data and settings, which it does not. The migration only worked because I treated the Azure database as the source of truth and checked it with hashes instead of trusting a re-seed. I also learned that a certificate is a separate dependency from DNS and the app: the site was fine, but a rate limit at the certificate step took the domain down until I changed the proxy setting. If I did this again I would write the pre-deploy step and the cutover order down first, test the certificate with a spare subdomain before moving the real name, and set up backups before loading data.

*Claude drafted this section from the evidence in this repository. I should read it and edit it into my own words before the interview.*
