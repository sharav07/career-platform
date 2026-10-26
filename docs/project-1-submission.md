# Project 1 submission

- Live site: https://sharavjiwrajka.me (`www` redirects to it)
- Repository: https://github.com/sharav07/career-platform
- Privacy page: https://sharavjiwrajka.me/privacy
- Final commit SHA: submitted in Brightspace. A file cannot contain its own commit's SHA, so this index lists the last commit before the final index edit under "Commit used for the checks" at the bottom.

Status key: **done** = evidence exists and was checked, **partial** = evidence exists with a stated gap, **not done** = not completed.

## 1. README, spec and plans

- [README](../README.md): behavior, setup, rollback, decisions, failures, costs, limitations, reflection. **done**
- Application spec: [docs/superpowers/specs/2026-10-06-personal-resume-site-design.md](superpowers/specs/2026-10-06-personal-resume-site-design.md)
- Application plan: [docs/superpowers/plans/2026-10-06-personal-resume-site-implementation.md](superpowers/plans/2026-10-06-personal-resume-site-implementation.md)
- Azure migration plan: [docs/superpowers/plans/2026-09-24-azure-vm-migration.md](superpowers/plans/2026-09-24-azure-vm-migration.md)
- Railway migration plan: [docs/superpowers/plans/2026-10-26-railway-migration.md](superpowers/plans/2026-10-26-railway-migration.md) (written 2026-10-26, after the empty Railway database existed and before the cutover; the plan says so)

## 2. Diagrams

- [docs/architecture.md](architecture.md): Azure, Railway, email path and analytics path. **done**

## 3. Migration, data comparison, cutover, rollback

- Source/target data comparison (counts and content hashes for all 10 tables, and rendered page comparison): [evidence/railway-migration.md](evidence/railway-migration.md) sections 1 to 4. **done**
- The real change to the original data (headline set on Azure only): same file, section 1.
- Cutover record: same file, section 6. **partial**: the root name is served by Railway, but through Cloudflare's proxy (see TLS note below).
- Rollback (code, domain, data): [README](../README.md#rollback). **done**
- Who manages what, Azure versus Railway: [README](../README.md#who-manages-what). **done**

## 4. Azure and final DNS/HTTPS

- Azure HTTP, firewall rules, restart, security: [evidence/ex03.md](evidence/ex03.md), [how-this-site-is-secured.md](how-this-site-is-secured.md) (written 2026-10-08).
- Azure controlled restart evidence: the Azure plan marks the restart check as done; **a dated restart output is not in this repository, so I treat the restart evidence as unverified.**
- Final DNS: [evidence/railway-migration.md](evidence/railway-migration.md) sections 6 and 7 (DNS-over-HTTPS answers, `www` redirects). **done**
- Final HTTPS: **partial / not met as written.** The brief wants a Railway-issued certificate with the root set to DNS only. Railway's certificate request failed with a Let's Encrypt rate limit, so the root is Proxied and visitors get Cloudflare's certificate. Details: [evidence/railway-migration.md](evidence/railway-migration.md) section 7.

## 5. Verified change through Railway

- Commit `f7a1b39` (pushed 12:19:41 UTC 2026-10-26) to Railway deployment to live page, with the live check at 12:20:53 UTC: [evidence/railway-migration.md](evidence/railway-migration.md) section 8. A second commit, `9bf118f`, deployed the same way. **done**
- Recovery explanation (code and data): [README rollback](../README.md#rollback). **done**

## 6. Zoho email

- Send, receive, reply, SPF, DKIM, DMARC: [evidence/ex06.md](evidence/ex06.md) and [evidence/zoho-header-check.md](evidence/zoho-header-check.md). **done** for the checks recorded.
- The message sent before the MX records existed: **not recorded**, so unverified.

## 7. Google Analytics 4

- Page view and outbound click verification with screenshots, and an explanation: [evidence/ex06.md](evidence/ex06.md) section 3. **done**

## 8. Failures, decisions, reflection, costs, limitations

- Investigated failures, decisions, costs and credits, limitations, reflection: README sections ([failures](../README.md#investigated-failures), [decisions](../README.md#decisions), [costs](../README.md#costs-credits-and-cleanup), [limitations](../README.md#remaining-limitations), [reflection](../README.md#reflection-written-afterward-2026-10-26-with-help-from-claude)). **done**, with Azure credit, domain renewal and Railway trial expiry marked as not independently verified.
- Deliberate lab failure (labeled as such): [evidence/ex05.md](evidence/ex05.md).

## Other items to know

- Railway Postgres password rotation (the instructor's follow-up to the Oct 21 incident): **not done** at the time of writing. Trial builds are running again (deployments above succeeded), so it can now be done and recorded.
- Ex04 HTTPS write-up in my own words: [how-this-site-is-secured.md](how-this-site-is-secured.md).

## Commit used for the checks

Last code commit before the final index edit: see `git log` on `main`. Railway deployments came from `0786fb9` (first deploy), `f7a1b39` and `9bf118f` (auto-deployed after the GitHub connection).
