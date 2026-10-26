# Railway + PostgreSQL migration plan

Written 2026-10-26 (Pacific), before the domain cutover. Moves the career-platform site from the Azure VM (Uvicorn + Nginx + SQLite) to Railway (managed runtime + managed PostgreSQL).

Honest timeline note: this plan was written after the Railway Postgres service was created (empty, nothing deployed or cut over) and after the code changes in commit `584cf4d`. The Azure site was not changed except for one data edit described in step 3. The domain was not touched until the cutover section below was reached.

## 1. What the target needs

| Need | Where it comes from | How it gets there |
| --- | --- | --- |
| Application code | `app/`, `templates/`, `static/` | Git (Railway builds from `main`) |
| Runtime | Python, set by `pyproject.toml` (`requires-python >= 3.11`) | Railway build picks it up |
| Packages | `pyproject.toml` + `uv.lock` (now includes `psycopg[binary]`) | Git; installed at build |
| Start command | `railway.toml` (`uvicorn ... --workers 2 --proxy-headers`) | Git |
| Configuration | `DATABASE_URL`, `PORT`, optional `GA_MEASUREMENT_ID` | Railway variables. `DATABASE_URL` is a reference to the Postgres service, so the password is never typed or committed |
| Secrets | The PostgreSQL password only | Lives inside Railway, never in Git |
| Schema | `SCHEMA` in `app/db.py` | Created by the app code (`initialize_database`) |
| Current data | The Azure VM's `resume.db` | NOT in Git (`resume.db` is gitignored). Exported from the VM, loaded with `scripts/load_export.py` |

What Git moves: all code, the lockfile, the start command, the seed. What Git does not move: the live database contents, Railway variables, the domain.

## 2. SQLite to PostgreSQL compatibility

| Difference | Change made |
| --- | --- |
| SQLite `?` placeholders, PostgreSQL `%s` | One translation point in `app/db.py` (`_PostgresConnection`) |
| `executescript` exists only in SQLite | Schema is split on `;` and run statement by statement |
| `PRAGMA foreign_keys = ON` is SQLite only | Only issued for SQLite; PostgreSQL enforces foreign keys always |
| Row access by column name | `sqlite3.Row` vs psycopg `dict_row`, both support `row["col"]` |
| Booleans stored as `INTEGER 0/1` | Kept as integers on both engines, so queries are identical |
| `\x1f`-joined technology lists | Valid text in PostgreSQL, kept unchanged |
| Connection per request | Kept on purpose, so a recovered database works without a restart |

Validated before cutover: the full test suite passes against SQLite and against a scratch PostgreSQL 16 (`tests/test_postgres.py`, run with `TEST_DATABASE_URL`). A local rehearsal of export, load and compare matched on every table.

## 3. The real data change (so seed data cannot pass as the transfer)

The profile `headline` was empty in the checked-in seed, and so in the Azure database. On 2026-10-26 I set it on the Azure database only (not in `data/resume.json`), with a one-off SQL update run over SSH. The Azure site showed it immediately. The export taken right after contains the new headline. If Railway shows that headline, the data came from the Azure database and not from a seed.

## 4. Steps

1. Export the Azure database to JSON (`scripts/sqlite_export.py` logic, run over SSH) and record row counts.
2. Commit the export under `data/migrations/` (it holds only content already public on the website).
3. Railway pre-deploy command runs `scripts/load_export.py`, which only loads into an empty database.
4. Deploy. Test the Railway-generated URL (`/health`, `/`, status codes) before touching DNS.
5. Run `scripts/compare_data.py` against the Railway database (counts and content hashes per table), and compare the rendered page text from Azure and Railway.
6. Cutover (Cloudflare, DNS only on the root): replace the root `@` A record (Azure IP) with the CNAME Railway asks for, plus Railway's verification TXT. Add the `www` redirect rule. Keep the Azure VM running.
7. Post-cutover checks: `dig`, `curl -I https://sharavjiwrajka.me` and `https://www...`, certificate subject and dates, page content, mail still works (MX/SPF/DKIM/DMARC records untouched).

## 5. Rollback

- Code: Railway keeps previous deployments; redeploy the last good one, or `git revert` the bad commit and push.
- Domain: change the root record back to the Azure IP (`68.155.158.254`). Azure keeps running through the midterm. DNS TTL decides how fast clients follow.
- Data written after cutover: the site has no write path today, so Railway PostgreSQL holds nothing that Azure lacks. If a write path is added later, the rollback must first run an export from PostgreSQL back into the SQLite file, or the writes are lost.

## 6. Risks I know about

- Railway paused Trial builds after its Oct 21 security incident. If a build cannot run, the cutover does not happen and the Azure site stays the live system.
- Railway reported that environment variables may have been read, which includes the database password. The instructor's follow-up is to rotate the Postgres password and redeploy once Trial builds are back, and to record when.
