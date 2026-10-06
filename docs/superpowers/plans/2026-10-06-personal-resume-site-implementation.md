# Personal Resume Website Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimal public, database-backed resume website whose profile remains visible from a checked-in JSON seed when SQLite is empty or unavailable.

**Architecture:** A FastAPI application will use Jinja templates for server-rendered pages, a small SQLite persistence layer for the full resume, and Pydantic models for seed validation. A read-only content service will prefer SQLite and fall back to profile-header data loaded from the JSON seed; Uvicorn will run under systemd behind Nginx on a single Linux VM.

**Tech Stack:** Python, FastAPI, Jinja2, SQLite, UV, Uvicorn, Pydantic, pytest, systemd, Nginx.

**Spec:** `docs/superpowers/specs/2026-10-06-personal-resume-site-design.md`

## Global Constraints

- “The fixed v1 stack is Python, FastAPI, Jinja templates, SQLite, UV, and Uvicorn.”
- “The application must be able to run on a single Linux VM behind Nginx.”
- “SQLite is the only v1 database; no managed database is required or permitted.”
- “No admin dashboard or content-management UI.”
- “No login, authentication, authorization, or account management.”
- “No browser-facing code may write to the database in v1.”
- “The profile page must never show a server error page because the database is empty or unavailable.”
- “The profile header” fallback must include “name, headline, summary, and contact links.”
- Tests are limited to seed import, explicit content ordering, and the database-down profile fallback.

## Review Focus

- **Malformed or incomplete JSON seed:** import and fallback must reject/report invalid required data rather than create a partial dataset; pinned in Task 3 seed-import tests.
- **Repeated seed import:** the same JSON must not duplicate records; pinned in Task 3 idempotent-import test.
- **Empty SQLite database:** the profile header must render from JSON with a visible notice and no error page; pinned in Task 4 empty-database test.
- **Unavailable SQLite file/connection:** the same fallback must work when SQLite cannot be read; pinned in Task 4 database-down test.
- **Conflicting ordering values:** public sections must follow explicit seed ordering rather than insertion order; pinned in Task 4 ordering test.

---

### Task 1: Create the UV application foundation

**Files:**
- Create: `pyproject.toml`
- Create: `uv.lock`
- Create: `app/__init__.py`
- Create: `app/main.py`
- Create: `tests/conftest.py`
- Modify: `.gitignore`

**Interfaces:**
- Produces `app.main:create_app() -> FastAPI` and a module-level `app` instance for Uvicorn.
- Produces a testable application factory with injected database and seed paths.

- [ ] **Step 1: Define the project and application factory**

Declare the Python version, runtime dependencies, pytest configuration, and UV
metadata in `pyproject.toml`. Implement `create_app(database_path: Path,
seed_path: Path) -> FastAPI` in `app/main.py`, register `GET /health`, and
expose `app = create_app(...)` with paths obtained from environment variables
or repository defaults. Add `resume.db` and `*.db` to `.gitignore` so local
SQLite runtime files are not committed.

- [ ] **Step 2: Run the foundation checks**

Run: `uv sync` and `uv run python -c "from app.main import app; assert app is not None"`

Expected: the lockfile installs and the application imports without requiring a
database connection.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock app tests
git commit -m "chore: create FastAPI UV application foundation"
```

**Done looks like:** UV can create the locked environment and FastAPI can start
through the application factory without requiring a database connection.

**How to check:** Run `uv sync` and the foundation import check above.

### Task 2: Model and validate the JSON seed

**Files:**
- Create: `data/resume.json`
- Create: `app/models.py`
- Create: `app/seed.py`

**Interfaces:**
- `app.models.ResumeSeed` is the root Pydantic model.
- `app.seed.load_seed(path: str | Path) -> ResumeSeed` parses JSON and raises a
  clear validation error for malformed or incomplete content.
- `ResumeSeed.profile` exposes `name`, `headline`, `summary`, and `contact_links`.

- [ ] **Step 1: Implement the Pydantic seed schema and loader**

Define models for profile, experience and achievements, skill groups and
skills, projects, education, and certifications. Include stable IDs, visibility
flags, and explicit display orders for list entities. Support partial date
values as strings. Implement JSON parsing followed by Pydantic validation with
an actionable path-specific error.

- [ ] **Step 2: Add the checked-in resume seed**

Populate `data/resume.json` with clearly marked placeholder records for every v1
content category, including the profile header and contact links. Add a comment
in `README.md` explaining that the seed content is placeholder data to be
replaced before production use. Keep the file the editorial source for both
import and the resilience fallback.

- [ ] **Step 3: Run the seed-load check**

Run: `uv run python -c "from app.seed import load_seed; load_seed('data/resume.json')"`

Expected: the checked-in JSON loads successfully.

- [ ] **Step 4: Commit**

```bash
git add data/resume.json app/models.py app/seed.py
git commit -m "feat: add validated resume seed schema"
```

**Done looks like:** Every v1 content category has a typed JSON representation,
the checked-in seed loads successfully, and malformed or incomplete seed data
fails with an actionable validation error.

**How to check:** Run the seed-load check above; malformed-seed behavior is
covered by the seed-import test in Task 3.

### Task 3: Add SQLite schema and deterministic seed import

**Files:**
- Create: `app/db.py`
- Create: `app/importer.py`
- Create: `tests/test_seed_import.py`

**Interfaces:**
- `app.db.initialize_database(path: Path) -> None` creates all v1 tables if
  missing.
- `app.importer.import_seed(database_path: str | Path, seed_path: str | Path) -> None`
  validates the seed, initializes SQLite, and deterministically replaces/upserts
  the single public dataset in one transaction.
- `app.db.load_resume(database_path: Path) -> ResumeSeed` returns the complete
  stored resume in explicit display order.

- [ ] **Step 1: Write import and idempotency tests**

Create:

```python
def test_import_populates_all_resume_sections(tmp_path): ...
def test_import_is_idempotent(tmp_path): ...
def test_invalid_seed_does_not_write_partial_data(tmp_path): ...
```

Assert a clean SQLite database contains profile, experience, achievements,
skills, projects, education, and certifications after import. Run import twice
and assert the row counts and loaded logical content are unchanged.
For invalid JSON, assert import fails before writing any rows.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_seed_import.py -v`

Expected: FAIL because the SQLite schema and importer do not exist.

- [ ] **Step 3: Implement SQLite bootstrap and schema**

Create-if-missing tables for the entities in the spec, including stable primary
keys, foreign keys, visibility, and explicit display-order columns. Use
parameterized SQLite statements and enable foreign-key enforcement.

- [ ] **Step 4: Implement transactional deterministic import**

Implement `import_seed` to load and validate JSON before opening the write
transaction, then upsert the single profile and related rows by stable IDs.
Ensure repeated imports do not duplicate records and preserve all relationships.

- [ ] **Step 5: Implement ordered reads**

Implement `load_resume` to reconstruct `ResumeSeed` from SQLite using explicit
`ORDER BY display_order` (and stable ID as a tie-breaker) for every ordered
collection, filtering records whose visibility is false.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tests/test_seed_import.py -v`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add app/db.py app/importer.py tests/test_seed_import.py
git commit -m "feat: add SQLite resume seed import"
```

**Done looks like:** A clean SQLite file can be initialized and populated from
JSON, repeated imports are idempotent, and stored content is reconstructed in
the required visibility and display order.

**How to check:** Run the targeted import tests and
`uv run python -c "from app.importer import import_seed; import_seed('resume.db', 'data/resume.json')"`
against a temporary database.

### Task 4: Implement ordered public content access

**Files:**
- Create: `app/content.py`
- Modify: `tests/test_seed_import.py`

**Interfaces:**
- `app.content.ContentResult` contains `resume: ResumeSeed`, `degraded: bool`,
  and `notice: str | None`.
- `app.content.load_public_content(database_path: Path, seed_path: Path) -> ContentResult`
  returns full database content when available and a seed-backed profile-only
  result when the database is empty or unavailable.

- [ ] **Step 1: Write content-service tests**

Add to `tests/test_seed_import.py`:

```python
def test_public_content_uses_database_and_preserves_order(tmp_path): ...
def test_empty_database_returns_seed_profile_and_degraded_notice(tmp_path): ...
def test_unavailable_database_returns_seed_profile_and_degraded_notice(tmp_path): ...
```

Assert database content is used in the healthy case, explicit display order is
preserved, and both fallback cases contain the seed profile header, omit the
rest of the resume sections, set `degraded` to true, and provide a visible
notice string.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_seed_import.py -v`

Expected: FAIL because the content service does not exist.

- [ ] **Step 3: Implement healthy and degraded content loading**

Implement the database-first read. Treat a missing/empty profile or SQLite
read/open failure as degraded mode, load the checked-in JSON seed, retain only
the profile header fields required by the spec, and return an explicit notice.
Do not re-raise database failures into the request handler.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_seed_import.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/content.py tests/test_seed_import.py
git commit -m "feat: add resilient public content service"
```

**Done looks like:** Healthy requests use ordered SQLite content; empty or
unavailable SQLite returns the seed-backed profile header and a degraded notice
without exposing a database exception.

**How to check:** Run the targeted content tests, including both fallback cases.

### Task 5: Build the public Jinja resume page

**Files:**
- Create: `app/routes.py`
- Create: `templates/base.html`
- Create: `templates/resume.html`
- Create: `static/styles.css`
- Modify: `tests/test_seed_import.py`
- Modify: `app/main.py`

**Interfaces:**
- `GET /` renders `templates/resume.html` using `ContentResult`.
- `GET /health` remains available for process checks.
- The template receives only assembled content and must contain no SQL or seed
  parsing logic.

- [ ] **Step 1: Write public-page tests**

Add to `tests/test_seed_import.py`:

```python
def test_homepage_renders_seed_profile_when_database_is_down(client): ...
```

Assert the degraded response is HTTP 200,
contains name/headline/summary/contact links from the seed, contains the
temporary-unavailability notice, and does not contain a server error page.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_seed_import.py -v`

Expected: FAIL because the route and templates do not exist.

- [ ] **Step 3: Implement the route and templates**

Register the homepage route with the application factory. Render semantic
sections for the profile header, experience and achievements, skills, projects,
education, and certifications. In degraded mode render the profile header and
notice while omitting unavailable sections.

- [ ] **Step 4: Add minimal responsive styling**

Implement readable typography, narrow-screen layout, visible section structure,
and keyboard-visible focus styling in `static/styles.css` without introducing
client-side application JavaScript.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_seed_import.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/routes.py app/main.py templates static tests/test_seed_import.py
git commit -m "feat: render public resume page"
```

**Done looks like:** The site serves a recruiter-friendly server-rendered
homepage, shows all available database-backed sections in order, and always
shows the seed-backed profile header with a visible notice when SQLite is
unavailable.

**How to check:** Run the targeted public-page tests and start
`uv run uvicorn app.main:app --reload` to inspect `/` locally.

### Task 6: Add import command and single-VM deployment configuration

**Files:**
- Create: `app/cli.py`
- Create: `deploy/career-platform.service`
- Create: `deploy/nginx.conf`
- Modify: `README.md`

**Interfaces:**
- `uv run python -m app.cli import-seed --database PATH --seed PATH` runs the
  deterministic importer and exits nonzero on validation/import failure.
- `deploy/career-platform.service` runs Uvicorn as a non-root service user.
- `deploy/nginx.conf` reverse-proxies the public site to Uvicorn.

- [ ] **Step 1: Implement the import command**

Add an argparse-based command that calls `import_seed`, prints a concise success
message, and reports validation/import errors to stderr with a nonzero exit
status.

- [ ] **Step 2: Add systemd and Nginx configuration**

Configure systemd to run `uv run uvicorn app.main:app --host 127.0.0.1 --port
8000` from the application directory with restart-on-failure behavior. Configure
Nginx to listen on the public HTTP endpoint and proxy to `127.0.0.1:8000`.
Update the existing `README.md` with installation, environment paths, database
initialization/import, placeholder-seed replacement, and service restart steps;
do not overwrite unrelated existing README content.

- [ ] **Step 3: Run the configuration checks**

Run `uv run python -m app.cli import-seed --help` and
`nginx -t -c "$PWD/deploy/nginx.conf"` on a host with Nginx installed.

Expected: CLI help renders and Nginx reports syntax is ok. If Nginx is unavailable,
inspect the config with a static review and record that limitation.

- [ ] **Step 4: Commit**

```bash
git add app/cli.py deploy README.md
git commit -m "ops: add seed command and VM deployment configuration"
```

**Done looks like:** An operator can seed SQLite, run the FastAPI app under
systemd, and expose it through Nginx on a single Linux VM with documented
commands.

**How to check:** Run the CLI test, validate Nginx syntax, and follow the
README's local deployment smoke test with `curl http://127.0.0.1/`.

### Task 7: Run the focused v1 verification suite

**Files:**
- Modify: `README.md` if verification commands need correction

**Interfaces:**
- The complete focused suite covers seed import, explicit ordering, and
  database-down fallback as required by the spec.

- [ ] **Step 1: Run the focused suite**

Run:

```bash
uv run pytest tests/test_seed_import.py -v
```

Expected: PASS with no skipped required behavior.

- [ ] **Step 2: Run the application smoke check**

Run:

```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8000/
```

Expected: health returns `{"status":"ok"}` and the homepage returns HTTP 200
with the profile name.

- [ ] **Step 3: Commit any verification-only documentation correction**

Only if needed:

```bash
git add README.md
git commit -m "docs: clarify resume verification commands"
```

**Done looks like:** The focused requirements suite passes and the running
application serves both health and profile pages without an admin route,
authentication requirement, or public write path.

**How to check:** Run the commands in this task from a clean checkout after
Tasks 1–6 are complete.
