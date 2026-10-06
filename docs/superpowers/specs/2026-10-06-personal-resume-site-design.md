# Personal Resume Website Design Specification

**Status:** Draft for approval  
**Date:** 2026-10-06  
**Scope:** Version 1 public resume website

## 1. Product intent

Create a polished, traditional personal resume website for recruiters and hiring
managers. Resume content is stored in a database so the site has a durable,
structured foundation for future career-platform capabilities, while the first
release remains intentionally narrow: it is a public site with no admin area,
login, or user-generated interaction.

The initial release succeeds when a recruiter can quickly understand the
candidate's profile, experience, skills, and evidence of impact, and when the
content can be reproducibly loaded from a version-controlled seed file into the
database.

## 2. Goals and non-goals

### Goals

- Present a concise, recruiter-friendly resume on desktop and mobile.
- Store resume content as typed, relational database records rather than
  hard-coded page markup.
- Provide a repeatable seed/import path from a checked-in content file into the
  database.
- Keep the public rendering layer separate from persistence and seed-loading
  concerns.
- Support accessible navigation, readable typography, responsive layout, and
  fast initial page loading.
- Establish data boundaries that can later support opportunities and
  application tracking without adding those features to v1.

### Non-goals for v1

- No admin dashboard or content-management UI.
- No login, authentication, authorization, or account management.
- No public editing, comments, messaging, recommendations, or social graph.
- No job board, opportunity tracking, application tracking, or recruiter portal.
- No multi-profile or multi-tenant behavior.
- No articles or publishing workflow; writing is reserved for a later content
  module.

## 3. Users and primary journey

The primary user is a recruiter or hiring manager arriving from a link,
search result, or referral. The expected journey is:

1. Land on the homepage and immediately see the candidate's name, role
   positioning, short summary, and contact action.
2. Scan experience and accomplishments in reverse chronological order.
3. Review skills and selected projects for evidence and relevance.
4. Review education and certifications when needed.
5. Navigate directly to a section or use a clear contact/link action.

The owner of the site is an indirect stakeholder in v1: they update the seed
file and run the import process during development or deployment. This is an
operational workflow, not a public product surface.

## 4. Functional requirements

### 4.1 Public resume

The public site must render:

- A profile header with name, headline, summary, location or equivalent
  positioning, and external/contact links.
- Work history entries with employer, title, dates, location where applicable,
  description, and ordered accomplishment statements.
- A skills section with grouped skills and optional proficiency or emphasis
  metadata.
- Projects with title, summary, role or contribution, outcomes, technologies,
  and optional links.
- Education records with institution, credential, dates, and optional details.
- Certification records with issuer, credential, date, expiration where
  applicable, and verification link where applicable.

Only records marked as published/visible by the seed data may be rendered.
Ordering must be explicit in the data model so presentation does not depend on
database insertion order.

### 4.2 Seed import

The repository must contain a human-editable seed file representing the v1
resume content. The import process must:

- Validate the seed file before writing data.
- Create or update the single public resume dataset deterministically.
- Preserve relationships between profile, experience, skills, projects,
  education, and certifications.
- Avoid duplicate records when run repeatedly.
- Fail with a clear error and non-success exit status when required data is
  invalid.
- Be safe to run in local development and deployment setup workflows.

The seed file is the source of editorial truth for v1. Direct database edits
are not a supported content workflow.

### 4.3 Public API/rendering boundary

The application must expose a read-only content access boundary for the public
site. The boundary may be implemented as server-side queries, a repository
module, or a read-only API depending on the selected application stack, but
page components must not embed SQL or seed-file parsing logic.

The profile header is a resilience exception: if the database is empty or
unavailable, the public layer must load the profile header (name, headline,
summary, and contact links) from the checked-in seed file. It must render that
header with a visible notice that the rest of the resume is temporarily
unavailable. The profile page must never show a server error page because the
database is empty or unavailable.

When the database is available, the public layer must use database content for
the full resume. It must not silently substitute stale, partial, or
success-shaped hard-coded content for database-backed sections.

## 5. Data model

The initial relational model should include the following entities:

- **Profile:** one v1 profile record containing identity, headline, summary,
  contact details, location, and external links.
- **Experience:** employer, title, start/end dates, current flag, location,
  description, visibility, and display order.
- **Experience achievement:** ordered accomplishment text belonging to an
  experience record.
- **Skill group:** a named category and display order.
- **Skill:** name, optional normalized key, optional proficiency/emphasis, and
  relationship to a skill group.
- **Project:** title, summary, contribution, outcome, technologies, links,
  visibility, and display order.
- **Education:** institution, credential, dates, details, visibility, and
  display order.
- **Certification:** name, issuer, issue/expiration dates, verification URL,
  visibility, and display order.

All public content entities should include stable identifiers, visibility
status, and explicit display ordering where they are list members. Dates must
use a representation that supports partial dates such as year-only entries.
Links should be stored as URL values and rendered with safe external-link
behavior; v1 does not require checking whether destinations are reachable
during import.

The schema should leave room for future ownership/profile relationships, but v1
must enforce one public profile and must not introduce unused multi-user
complexity.

## 6. Architecture and data flow

The v1 system consists of four logical layers:

1. **Seed content:** version-controlled structured file containing the resume
   dataset.
2. **Import/validation:** command or setup task that parses, validates, and
   upserts the seed dataset into the database.
3. **Content access:** typed read-only queries/repositories that select
   visible, ordered records and assemble the public resume view.
4. **Public presentation:** server-rendered or statically optimized pages and
   components that display the assembled content.

The normal flow is:

`seed file -> validation/import -> database -> read-only content access -> public page`

The database is the runtime source for the public site. The seed file is the
repeatable editorial input used to initialize or refresh that database. No
browser-facing code may write to the database in v1.

The fixed v1 stack is Python, FastAPI, Jinja templates, SQLite, UV, and
Uvicorn. The application must be able to run on a single Linux VM behind
Nginx. SQLite is the only v1 database; no managed database is required or
permitted. The chosen implementation must provide migrations, parameterized
queries, connection/configuration validation, and a reproducible seed command.

## 7. Error handling and operational behavior

- Missing or invalid database configuration must be reported with an
  actionable error, while the public profile remains available from the seed
  file when the database cannot be used.
- Seed validation errors must identify the field and record that failed.
- Import failures must be transactional where supported, avoiding a partially
  refreshed dataset.
- Database read failures must produce useful server-side diagnostics without
  exposing credentials, SQL, or internal details publicly, and must render the
  seed-backed profile header with a visible notice that the rest of the resume
  is temporarily unavailable.
- An empty database must render the same seed-backed profile fallback and
  notice; it must never produce a server error page for the profile.

## 8. Accessibility, performance, and security

The public site must:

- Use semantic landmarks, heading hierarchy, keyboard-accessible navigation,
  visible focus states, sufficient color contrast, and meaningful link labels.
- Remain usable on narrow mobile screens without horizontal scrolling.
- Optimize initial content delivery with server rendering or equivalent
  techniques and avoid loading unnecessary client-side JavaScript.
- Avoid exposing database credentials or administrative endpoints.
- Use parameterized database access and validate all seed input.

## 9. Testing and acceptance criteria

The implementation is ready for v1 when:

- A clean database can be migrated and populated from the checked-in seed file.
- Re-running the seed process produces the same logical dataset without
  duplicates.
- Public pages render the profile header from the checked-in seed file when the
  database is empty or unavailable, with a visible temporary-unavailability
  notice and no server error page.
- Explicit ordering is respected for experience, achievements, skills, projects,
  education, and certifications.
- Tests cover seed import, explicit content ordering, and the database-down
  profile fallback.
- The public deployment contains no write path, admin route, or authentication
  requirement in v1.

## 10. Future work

The following items are intentionally deferred and should be treated as
separate future design and implementation work:

### Administration and identity

- Private admin area for editing profile content.
- Authentication, authorization, sessions, and account recovery.
- Draft, preview, publish, and revision workflows.
- Replacement of direct seed-file editing with an admin editor while retaining
  seed import/export for backup and portability.

### Career-platform capabilities

- Opportunity and job records, saved opportunities, and application tracking.
- Candidate-specific pipeline states, notes, reminders, and reporting.
- Multiple profiles or multi-tenant ownership boundaries.
- Recruiter-facing or authenticated sharing controls.
- Articles, talks, and other writing content.
- Networking, recommendations, or community features.

Future features must build on explicit profile ownership, publication
visibility, and audit/versioning decisions rather than assuming the v1
single-profile import workflow is sufficient.

## 11. Open implementation decisions

The implementation plan must select and document:

- Seed-file format and schema validation library.
- Migration and deterministic upsert strategy.
- Nginx reverse-proxy configuration and Linux VM deployment details.
- Whether the FastAPI/Jinja site is server-rendered directly or uses a
  pre-generation step where appropriate.

The implementation must use Python, FastAPI, Jinja templates, SQLite, UV,
Uvicorn, and a single Linux VM behind Nginx. These choices must preserve the
requirements and boundaries in this document; they should not introduce an
admin area, login, or future-platform feature into v1.
