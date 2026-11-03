# AWS migration notes

Running log for the move from Railway to AWS (EC2 + Single-AZ RDS PostgreSQL). Plan: [2026-11-03-aws-migration.md](superpowers/plans/2026-11-03-aws-migration.md). Branch `aws-migration`. Railway still serves `sharavjiwrajka.me`, and no DNS record has changed.

This file contains no passwords, keys, tokens or authorization codes. Database passwords live in `~/aws-migration-secrets/` on the laptop (mode 600, outside the repository). The SSH private key is `~/.ssh/aws-isba-4775`.

Last updated 2026-11-03.

## 1. What's done

| Step | Status | Evidence |
| --- | --- | --- |
| Zero-spend budget (guide section 1) | Done | Set up by the account owner |
| Railway backup (section 2) | Done 2026-11-02 | `~/aws-migration-backup/railway-2026-11-02.dump` (PostgreSQL 18.6 custom format), counts in `railway-counts.txt`. Restored into local Homebrew PostgreSQL 18, and the table counts matched Railway. Second copy in iCloud with a verified SHA-256 |
| IAM user `isba-student` with MFA (section 3) | Done | `get-caller-identity` returns `arn:aws:iam::822401997765:user/isba-student` |
| AWS CLI and `isba-4775` profile (section 4) | Done | AWS CLI 2.39.3, region `us-east-1` |
| Deployment policy (section 5) | Done | `ISBA4775EC2Migration2` attached. The unsuffixed `ISBA4775EC2Migration` is an unused duplicate |
| Blind spot pass, interview, plan, cost estimate (section 6) | Done 2026-11-03 | Plan file above. Estimate is $26.82 a month before credits |
| RDS database (section 7) | Created 2026-11-03, status `creating` when last checked | See section 2 below. Not yet checked in the console |
| EC2 instance (section 8) | Blocked | vCPU quota, see section 5 |
| Sections 9 to 12 | Not started | |

### Deviations from the plan

- **RDS backup retention is 1 day, not 7.** The first `create-db-instance` call was refused with `FreeTierRestrictionError`: "The specified backup retention period exceeds the maximum available to free tier customers." Nothing was created by that call. The guide says not to upgrade the plan, so I chose 1 day. This is acceptable because the site has no write path, and independent copies of the 2026-11-02 dump exist on the laptop and in iCloud. Recovery beyond one day comes from that dump, not RDS.
- **Local `main` was 18 commits behind GitHub** at the start of the session and was missing the PostgreSQL support. I fast-forwarded it (`git pull --ff-only`, no local changes) before planning.

## 2. AWS resources that exist now

Account `822401997765`, region `us-east-1`.

| Resource | Name | ID | Notes |
| --- | --- | --- | --- |
| RDS DB instance | `career-platform-db` | `db-KLRVT6VKHWXNIWB6LQG3YMXS24`, ARN `arn:aws:rds:us-east-1:822401997765:db:career-platform-db` | PostgreSQL 18.6, db.t4g.micro, 20 GB gp3, encrypted with the AWS-managed RDS key, Single-AZ in us-east-1a, not publicly accessible, 1-day backups (window 04:19-04:49 UTC), maintenance window Saturdays 08:31-09:01 UTC, deletion protection on, parameter group `default.postgres18`. Database `career`, master user `cpadmin`. Endpoint not assigned yet |
| DB subnet group | `default` | (name only) | Created automatically by RDS in the default VPC, 6 subnets |
| Security group (web) | `isba-4775-web` | `sg-0aadfa11e29948f71` | Inbound 22 from `99.7.123.79/32` only, 80 and 443 from anywhere. The laptop's address was `157.242.208.140` on 2026-11-03, so the SSH rule needs updating before connecting |
| Security group (database) | `isba-4775-db` | `sg-0de26372ac70bed68` | Inbound 5432 only from `sg-0aadfa11e29948f71` |
| EC2 key pair | `isba-4775` | `key-0f9854274609d1fd7` | ed25519, imported. The private key never left the laptop |
| VPC | default | `vpc-0caf9a8f41f0c9d5d` | Pre-existing. The plan uses subnet `subnet-06c78bd358df96f6b` (us-east-1a) |

None yet: EC2 instances, Elastic IPs, snapshots.

## 3. Decisions and why

| | Decision | Choice | Why |
| --- | --- | --- | --- |
| A | Timeline | Switch the domain to AWS before the Railway trial ends, about 2026-11-08 | The site never goes down |
| B | App database account | Separate read-only user `career_app` (SELECT only). `cpadmin` is used only for the restore | The site has no write path, so a leaked app password can't change or delete data. The request path never creates tables (only `import_seed` and `scripts/load_export.py` call `initialize_database`), so read-only works |
| C | Cloudflare after the switch | Root and `www` DNS only (grey cloud), Let's Encrypt with certbot on EC2 Nginx | Matches the brief and the Azure setup. The October 26 rate limit was Railway's certificate request, not this server's |
| D | Backup and restore test (default, corrected) | No repeat of the local restore or the iCloud copy. One more restore test: from EC2 onto RDS with `pg_restore --no-owner --no-acl`, then compare counts with `railway-counts.txt` | The local restore was already proven. The new test proves the dump restores on the target and that RDS is reachable from EC2 only |
| E | Azure VM (default) | Keep it running as the fallback until AWS serves the domain and passes checks, then delete resource group `rg-career-platform` | It's already running, with a certificate valid until 2027-01-06 for both names |

Other choices: PostgreSQL 18.6 to match Railway exactly. db.t4g.micro, the cheapest class the policy allows. Both the database and the instance in us-east-1a, so traffic between them is free. EC2 is t3.micro only. Reuse the existing security groups and key pair.

## 4. Next step

1. Check the database in the RDS console once it shows Available: Publicly accessible **No**, Availability Zone **us-east-1a**, class **db.t4g.micro**.
2. Check the vCPU quota appeal from the account owner's session in Service Quotas. If it's approved, continue with plan section 3 (launch the EC2 t3.micro), starting with updating the SSH rule to the current laptop address.

## 5. Open blockers

| Blocker | Impact | What happens next |
| --- | --- | --- |
| **EC2 vCPU quota is 1, with an appeal pending.** A t3.micro needs 2 vCPUs, confirmed with `describe-instance-types` | No EC2 launch is possible. `isba-student` can't read quotas, so the owner checks | **Checkpoint: end of Thursday 2026-11-05.** If it's not approved, follow plan section F: update Azure to current `main`, add the missing project entry (Azure has 0, Railway has 1), point root and `www` at `68.155.158.254` DNS only by Friday 2026-11-06, and stop RDS |
| Railway trial ends about 2026-11-08 | The site goes down if nothing else serves the domain by then | Covered by decision A, or the fallback |
| `ISBA4775EC2Migration2` refuses `ssm:GetParameter` on the Canonical image path, although the course policy allows it | Can't look up the Ubuntu 26.04 image the documented way | Ask the instructor, or use `ec2:DescribeImages` with owner `099720109477` |
| The SSH rule allows `99.7.123.79/32`, but the laptop's address has changed | SSH would time out | Replace the rule before the first connection |
| `aws-mcp` server not connected (no credentials, and `uvx` was missing earlier) | Only lookups like pricing are affected. The CLI works | Fix when convenient |
| The database is billing while EC2 is blocked (about $13.98 a month) | Uses credits | Stop it if the fallback is used |
