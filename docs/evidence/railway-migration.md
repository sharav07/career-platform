# Railway migration evidence

All times are 2026-10-26, Pacific unless marked UTC (UTC = Pacific + 7 hours). Plan: [2026-10-26-railway-migration.md](../superpowers/plans/2026-10-26-railway-migration.md). Diagrams: [architecture.md](../architecture.md).

Railway project `sublime-laughter`, environment `production`, region US East. Services: `Postgres` (with volume) and `career-platform` (built from this repo's `main`). Test URL before any DNS change: `https://career-platform-production-eae0.up.railway.app`.

## 1. The real data change (Azure only, not in Git)

At 11:52 UTC I ran a one-off update on the Azure VM's `resume.db` over SSH, setting `profiles.headline`, and exported every table in the same command. The command printed:

```text
headline before: ''
headline after: Information Systems and Business Analytics student at Loyola Marymount University
{'profiles': 1, 'profile_links': 3, 'experiences': 11, 'experience_achievements': 33, 'skill_groups': 0, 'skills': 0, 'projects': 0, 'project_links': 0, 'education': 2, 'certifications': 0}
```

`data/resume.json` (the seed) still has an empty headline. So a headline on Railway can only have come from the Azure database. The export is `data/migrations/azure-export-2026-10-26.json` (content that is already public on the site).

## 2. Failure I saw first: empty PostgreSQL gives a deliberate 503

The first Railway deploy (commit `0786fb9`) came up with an empty PostgreSQL database because the pre-deploy data load did not run (see section 5). At 11:56:57 UTC:

```text
root_status: 503      health_status: 200      page shows: "Projects temporarily unavailable"
```

The profile stayed visible and `/health` stayed 200, which is the behavior the brief asks for when the database fails. It also showed my app was reaching Railway's PostgreSQL, because an unreachable database gives the same 503.

## 3. Load and compare (run inside the Railway service console)

Commands, run with the app's own Python on the deployed service:

```text
.venv/bin/python scripts/load_export.py data/migrations/azure-export-2026-10-26.json
.venv/bin/python scripts/compare_data.py data/migrations/azure-export-2026-10-26.json
```

Result (screenshot: [railway-load-and-compare.jpg](railway-load-and-compare.jpg)). Each hash is a SHA-256 prefix of the sorted rows of that table:

```text
table                       src  dst  src hash     dst hash     match
profiles                      1    1  2a36a4a85d4c 2a36a4a85d4c OK
profile_links                 3    3  d7aeed12476d d7aeed12476d OK
experiences                  11   11  2cdf598da0d3 2cdf598da0d3 OK
experience_achievements      33   33  4c9fbb89b808 4c9fbb89b808 OK
skill_groups                  0    0  e3b0c44298fc e3b0c44298fc OK
skills                        0    0  e3b0c44298fc e3b0c44298fc OK
projects                      0    0  e3b0c44298fc e3b0c44298fc OK
project_links                 0    0  e3b0c44298fc e3b0c44298fc OK
education                     2    2  03b78d391568 03b78d391568 OK
certifications                0    0  e3b0c44298fc e3b0c44298fc OK
```

## 4. Recovery without a restart, and the rendered pages

No redeploy or restart happened between sections 2 and 4. At 11:57:38 UTC the same Railway URL returned **200**, with the Azure-only headline and without "Projects temporarily unavailable" (screenshot: [railway-site-after-load.jpg](railway-site-after-load.jpg)).

Rendered page comparison, the same script run in the browser on each site (visible text of `<main>`, whitespace normalized, the new "No projects published yet." line removed because the Azure site runs older code):

| Site | HTTP | Server header | resume entries | text length | hash |
| --- | --- | --- | --- | --- | --- |
| `https://sharavjiwrajka.me` (Azure) | 200 | nginx/1.24.0 (Ubuntu) | 13 | 5869 | 387198865 |
| Railway test URL | 200 | (Railway edge) | 13 | 5869 | 387198865 |

## 5. What did not work, and what I changed

- `railway.toml` set `preDeployCommand`, but the Railway build log shows only the start command and no pre-deploy step, and the database stayed empty. Railway's settings page says Config as Code is deprecated and that services that never used it cannot opt in, so I do not rely on it. I ran the load from the service console instead. The loader skips a non-empty database, so a later redeploy cannot overwrite data.
- Railway's GitHub App was not installed on my account ("Could not load branches"). I deployed from the public repo URL. Auto-deploy on push needs the app, which I connect before the verified-change step (see the README).

## 6. Not yet done at the time of writing

Custom domain cutover, `www` redirect, post-cutover checks, Postgres password rotation (instructor's follow-up to Railway's Oct 21 incident), and the verified GitHub-to-Railway change. Their results will be added below with their own dates, or marked unverified.
