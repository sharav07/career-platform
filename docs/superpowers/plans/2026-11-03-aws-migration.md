# AWS migration plan (Railway to EC2 + RDS)

Moves the career-platform site from Railway (PaaS, managed PostgreSQL) to an EC2 instance with a Single-AZ RDS PostgreSQL database. Written 2026-11-03 on branch `aws-migration`. Nothing in this plan has been created yet.

Railway keeps serving `sharavjiwrajka.me` with DNS unchanged until the AWS copy passes its checks on `aws.sharavjiwrajka.me`.

## Decisions

| Decision | Choice | Why |
| --- | --- | --- |
| Architecture | EC2 (app) + Single-AZ RDS PostgreSQL 18 | Course path. AWS runs the database, backups and patching |
| Cutover deadline | Before the Railway trial ends, about 2026-11-08 | The site stays up throughout |
| App database account | Separate read-only user `career_app` (SELECT only). The RDS master user is used only for the restore | The site has no write path. A leaked app password can't change or delete data |
| Cloudflare after cutover | Root and `www` DNS only (grey cloud), Let's Encrypt with certbot on EC2 | Matches the brief and the Azure setup |
| Azure VM | Kept as the fallback until AWS serves the domain and passes checks, then deleted | Still running, and it holds a valid certificate until 2027-01-06 |
| Phase order | RDS first, EC2 gated on the vCPU quota appeal | The EC2 vCPU quota is 1, and a t3.micro needs 2 |

## Fixed values

| Item | Value |
| --- | --- |
| Account, user, profile | `822401997765`, `isba-student`, `--profile isba-4775` |
| Policy attached | `ISBA4775EC2Migration2` (the unsuffixed `ISBA4775EC2Migration` is an unused duplicate) |
| Region and zone | `us-east-1`, with both the database and the instance in `us-east-1a` so traffic between them stays in one zone |
| VPC | Default, `vpc-0caf9a8f41f0c9d5d`. Subnet `subnet-06c78bd358df96f6b` (us-east-1a) |
| Security groups (already exist) | `isba-4775-web` `sg-0aadfa11e29948f71`: 22 from one /32, 80 and 443 from anywhere. `isba-4775-db` `sg-0de26372ac70bed68`: 5432 only from `isba-4775-web` |
| Key pair (already imported) | `isba-4775` (ed25519). Private key `~/.ssh/aws-isba-4775`, never in Git |
| Backup | `~/aws-migration-backup/railway-2026-11-02.dump`, PostgreSQL 18.6 custom format. Counts in `railway-counts.txt`, query in `counts.sql` |
| Secrets folder (laptop) | `~/aws-migration-secrets/`, mode 700, outside the repository |

## 0. Already done (not repeated)

- [x] Zero-spend budget (section 1).
- [x] Railway dump taken 2026-11-02, restored into local Homebrew PostgreSQL 18, and the table counts matched Railway (section 2).
- [x] Second copy of the dump in iCloud, with a verified SHA-256 hash.
- [x] IAM user with MFA, CLI login, and the deployment policy (sections 3 to 5).
- [x] Security groups and key pair created (2026-10-29 and 2026-11-03).
- [x] Branch `aws-migration` created from `main` at `3a5ea41`.

## 1. RDS database (guide section 7)

1. Generate the master password on the laptop and write it to `~/aws-migration-secrets/rds-master.txt` (mode 600). Never print it, put it in chat, or write it into the repository. Use only letters and digits so it never needs URL-encoding.
2. Create the database once:

   | Setting | Value |
   | --- | --- |
   | Identifier | `career-platform-db` |
   | Engine | `postgres` 18.6, the same version as Railway |
   | Class | `db.t4g.micro` |
   | Storage | 20 GB gp3, encrypted, no `--max-allocated-storage` (autoscaling off) |
   | Availability | Single-AZ, `--availability-zone us-east-1a` |
   | Network | Default VPC, `--no-publicly-accessible`, `--vpc-security-group-ids sg-0de26372ac70bed68` |
   | Initial database | `career` |
   | Master user | `cpadmin`, password from the secrets file |
   | Backups | 1-day retention. The Free plan refused 7 days with `FreeTierRestrictionError` (see `docs/migration-notes.md`) |
   | Deletion protection | On, turned off only during cleanup |
   | Tags | `course=isba-4775`, `project=career-platform` |

3. Don't wait for it to become available. Creation takes 5 to 10 minutes. Move on to section 2.
4. Check it yourself in the RDS console: Publicly accessible **No**, Availability Zone `us-east-1a`, class `db.t4g.micro`, storage encrypted.

The database bills from creation even before EC2 exists. That is accepted. If the fallback in section F is used, stop it (step F4).

## 2. EC2 quota gate

The EC2 On-Demand Standard vCPU quota is 1. A t3.micro has 2 vCPUs (confirmed with `describe-instance-types`), so any launch is refused until the quota appeal is approved. `isba-student` can't read quotas, so the account owner checks the appeal in Service Quotas.

- **Approved:** go to section 3.
- **Not approved by the end of Thursday 2026-11-05:** go to section F. Sections 3 onward resume when the appeal is approved.

The policy only allows t3.micro and t3.small, so a 1-vCPU type such as t2.micro is not an option without the instructor changing the policy.

## 3. EC2 instance (guide section 8)

1. Find the image. The attached policy refused `ssm:GetParameter` on the Canonical path on 2026-11-03, although the course policy allows it. Either ask the instructor about the difference, or use `ec2:DescribeImages` with owner `099720109477` (Canonical), name `ubuntu/images/hvm-ssd-gp3/ubuntu-*-26.04-amd64-server-*`, newest by creation date. Reject any name containing `pro`.
2. Update the SSH rule to the laptop's current address as a /32. The rule allows `99.7.123.79/32`, but the laptop's address on 2026-11-03 was `157.242.208.140`. Revoke the old rule once the new one is in place.
3. Launch once:

   | Setting | Value |
   | --- | --- |
   | Type | `t3.micro`, On-Demand, `--credit-specification CpuCredits=standard` |
   | Image | Ubuntu Server 26.04 LTS, amd64, from step 1 |
   | Storage | 20 GB gp3 root volume, encrypted, deleted on termination |
   | Metadata | `HttpTokens=required` (IMDSv2). The policy denies the launch without it |
   | Network | `subnet-06c78bd358df96f6b`, security group `sg-0aadfa11e29948f71` |
   | Key | `isba-4775` |
   | Tags | `Name=career-platform-web`, `course=isba-4775` |

   If the launch is denied, decode the error with `aws sts decode-authorization-message` to see which rule fired. Don't retry with a different type.
4. Allocate an Elastic IP and associate it with the instance.
5. Before the first SSH connection, compare the instance's ed25519 host key fingerprint from `aws ec2 get-console-output` with the one SSH shows.
6. Check it yourself in the EC2 console: instance ID, Elastic IP, security group, and a 20 GB encrypted volume.

## 4. Server setup (guide section 9)

Run over SSH as `ubuntu` with the key `~/.ssh/aws-isba-4775`.

1. `sudo apt-get update && sudo apt-get upgrade -y`
2. Install `nginx git postgresql-client-18 certbot python3-certbot-nginx`. Confirm `pg_restore --version` reports 18.x.
3. Add a 1 GB swap file, because the t3.micro has 1 GiB of memory.
4. Install uv, clone `https://github.com/sharav07/career-platform.git`, check out `aws-migration`, and run `uv sync --locked --no-dev`.

Don't run the Azure deploy steps, `import_seed`, `scripts/load_export.py`, or `scripts/add_seed_projects.py` on AWS. Each of them writes to the database. `import_seed` deletes every table first.

## 5. Restore the dump onto RDS from EC2 (the new restore test)

RDS only accepts connections from the web security group, so the restore runs on the instance.

1. Copy `railway-2026-11-02.dump` and `counts.sql` to the instance with `scp`, and set the dump to mode 600.
2. Check the SHA-256 on the instance against the recorded hash. Stop if it differs.
3. Read the master password into the shell for this session only with `PGPASSWORD`, so it isn't saved in shell history.
4. Restore into the empty `career` database:

   ```bash
   pg_restore --no-owner --no-acl -h <endpoint> -U cpadmin -d career railway-2026-11-02.dump
   ```

   `--no-owner --no-acl` is needed because the dump belongs to Railway's `postgres` role, which doesn't exist on RDS.
5. Run `counts.sql` against RDS and `diff` the result with `railway-counts.txt`. All ten tables must match: 1 profile, 3 profile_links, 11 experiences, 33 experience_achievements, 2 education, 1 project, 1 project_link, and 0 in skill_groups, skills and certifications. Also spot-check the profile headline and the project title.
6. Create the read-only app user as `cpadmin`:

   ```sql
   CREATE ROLE career_app LOGIN PASSWORD '<from secrets file>';
   GRANT CONNECT ON DATABASE career TO career_app;
   GRANT USAGE ON SCHEMA public TO career_app;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO career_app;
   ```

   The password is generated on the laptop into `~/aws-migration-secrets/rds-app.txt`, letters and digits only.
7. Confirm that `career_app` can `SELECT` and is refused on `INSERT`.
8. Delete the dump from the instance. The originals stay on the laptop and in iCloud.
9. Log the restore duration and the count diff in `docs/migration-notes.md`.

## 6. App service and Nginx

1. Write `/etc/career-platform/env` (owner `root`, mode 600) with `DATABASE_URL=postgresql://career_app:<password>@<endpoint>:5432/career?sslmode=require`.
2. Create a systemd unit `career-platform.service` like the Azure one: `EnvironmentFile=` pointing at that file, `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2 --proxy-headers`, `Restart=on-failure`, and enabled at boot.
3. Add an Nginx site for `aws.sharavjiwrajka.me` that proxies to `127.0.0.1:8000`.
4. Check on the instance that `curl 127.0.0.1:8000/health` returns `{"status":"ok"}` and that `/` returns 200 with the full page, not the 503 fallback.

## 7. Test subdomain (guide section 10)

1. Using the Cloudflare CLI, add an `A` record named `aws` pointing at the Elastic IP, DNS only, and change no other record. Check the record in the dashboard yourself and run `nslookup aws.sharavjiwrajka.me`.
2. Run `certbot --nginx -d aws.sharavjiwrajka.me --redirect`, then `certbot renew --dry-run`.
3. Tests, each recorded in `docs/migration-notes.md` with its output:
   - `https://aws.sharavjiwrajka.me/` returns 200 with a valid padlock, and HTTP redirects to HTTPS with a 301.
   - `/privacy` and `/health` return 200.
   - The rendered page matches Railway's, apart from the hosting note in the footer.
   - `curl -m 8 http://<EIP>:8000/health` from the laptop is refused, and `nc -z <rds-endpoint> 5432` from the laptop times out.
   - RDS shows Publicly accessible No.
   - What wasn't verified.

## 8. Cutover (guide section 11), before 2026-11-08

1. Re-run `counts.sql` against Railway and RDS just before switching. If Railway changed after 2026-11-02, take a new dump and repeat section 5 before continuing.
2. Note the current root and `www` records in Cloudflare (root is a proxied CNAME to Railway). Leave the MX, SPF, DKIM, DMARC and GA4 records unchanged.
3. Replace the root record with `A` → Elastic IP, DNS only. Set `www` the same way, or as a CNAME to the root.
4. Add both names to Nginx, then run `certbot --nginx -d sharavjiwrajka.me -d www.sharavjiwrajka.me --redirect`. Until certbot finishes, the root's HTTPS may show a certificate warning for a few minutes. Do the switch at a quiet time.
5. Check yourself: `nslookup` on both names returns the Elastic IP, and `https://sharavjiwrajka.me` loads with a padlock.
6. Merge `aws-migration` into `main`. Railway rebuilding at that point is harmless because it no longer serves the domain. Pull `main` on EC2, restart the service, check the site again, then delete the branch.

## 9. Cleanup

- Railway: delete the project after cutover is verified and before the trial ends.
- Azure: delete resource group `rg-career-platform` after AWS has served the domain and passed its checks.
- End of semester: decide whether to keep paying, move the site, or delete it. Deleting means a final RDS snapshot (or not), turning off deletion protection, terminating the instance, releasing the Elastic IP, and deleting leftover snapshots.

## F. Fallback if the quota isn't approved by Thursday 2026-11-05

The goal is that the domain never depends on Railway after 2026-11-08. Azure is the fallback because it's already running and holds a valid certificate for both names.

1. On Azure, over SSH, run `git pull` to the current `main` (PostgreSQL support, privacy page and analytics). Restart `career-platform`.
2. Compare the Azure SQLite counts with `railway-counts.txt`. The Azure export from 2026-10-26 had 0 projects, and Railway has 1. Add it with `DATABASE_URL=resume.db python scripts/add_seed_projects.py data/resume.json`, the same content update Railway received. Run the counts again.
3. By Friday 2026-11-06, set the root and `www` records in Cloudflare to `A` → `68.155.158.254`, DNS only. Verify with `nslookup` and the padlock.
4. Stop the RDS instance to save cost while EC2 is blocked. AWS starts it again automatically after 7 days, so stop it again if needed.
5. When the quota is approved, resume at section 3. At section 8, the switch is from Azure instead of Railway, and the counts are compared against Azure.

If that fails too, a paid Railway Hobby plan ($5 a month) would extend Railway until AWS is ready.

## Cost

Prices come from AWS's public price list for `us-east-1`, published 2026-11-03T21:10Z. A month is 730 hours. These are costs before credits.

| Item | Price | Monthly |
| --- | --- | --- |
| EC2 t3.micro, Linux, On-Demand | $0.0104/hour | $7.59 |
| EBS gp3 root volume, 20 GB | $0.08/GB-month | $1.60 |
| RDS db.t4g.micro PostgreSQL, Single-AZ | $0.016/hour | $11.68 |
| RDS gp3 storage, 20 GB | $0.115/GB-month | $2.30 |
| Public IPv4 (Elastic IP, in use) | $0.005/hour | $3.65 |
| RDS automated backups, 7 days | Free up to 20 GB (the provisioned storage), then $0.095/GB-month. The data is about 16 KB | $0.00 |
| Internet data out | First 100 GB/month free across all of AWS, then $0.09/GB | $0.00 |
| EC2 to RDS in the same zone (us-east-1a) | Free. Across zones it would be $0.01/GB | $0.00 |
| CPU credits (standard mode) | No surplus charges | $0.00 |
| **Total** | | **$26.82** |

Compared with the budget: the zero-spend budget emails on the first charge that credits don't cover, so it stays silent while credits pay. At $26.82 a month, $100 of credits lasts about 3.7 months. That covers the semester, but check the remaining balance and expiry on the Credits page from the owner's session, because `isba-student` can't see them.

While EC2 is blocked (section F): RDS running alone costs $13.98 a month. Stopped, it costs $2.30 a month for storage only, until AWS restarts it after 7 days. An Elastic IP that stays allocated after its instance is gone keeps billing $3.65 a month as an idle address.
