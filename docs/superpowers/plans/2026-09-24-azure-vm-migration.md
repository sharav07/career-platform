# Azure VM migration plan

Moves the career-platform resume site from a GitHub Codespace to an Azure VM.
Written for 2026-09-24 and executed on 2026-10-08, one section at a time.

**Target**

| Item | Value |
| --- | --- |
| Resource group | `rg-career-platform` |
| VM name | `vm-career-platform` |
| Region | Mexico Central |
| Size | `Standard_B2ts_v2` (2 vCPU, 1 GiB) |
| Image | Ubuntu Server 24.04 LTS |
| Disk | Standard SSD |
| Admin user | `azureuser` (SSH key only) |
| Public IP | 68.155.158.254 |
| Tags | `course=isba-4775`, `environment=staging` |

## 1. Server

- [x] Confirm the Azure for Students subscription is active with credit left.
- [x] Create an SSH key pair on the laptop (`ssh-keygen -t rsa -b 4096`, file `isba4775_azure`).
- [x] Create the resource group and VM in the portal. The subscription has an allowed-regions policy, so West US 2 was refused (`RequestDisallowedByAzure`). I read the allowed list in Azure Policy (Canada Central, Norway East, Mexico Central, Denmark East, Belgium Central) and used Mexico Central, where `Standard_B2ts_v2` is available. OS disk type set to Standard SSD. Auto-shutdown left off.
- [x] Restrict SSH: delete the default open `SSH` rule (priority 300) and keep only `Allow-SSH-Laptop`, source = the laptop's single address as a /32.
- [x] Connect with `ssh -i ~/.ssh/isba4775_azure azureuser@PUBLIC-IP`.

## 2. Packages

- [x] `sudo apt-get update`
- [x] `sudo apt-get install -y git sqlite3`
- [x] Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [x] Install Nginx: `sudo apt-get install -y nginx`

## 3. Code

- [x] `git clone https://github.com/sharav07/career-platform.git`

## 4. Python

- [x] `uv sync --locked --no-dev` (22 packages from `uv.lock`, nothing resolved fresh)

## 5. Config

- [x] The app has no `.env` loader. It reads two optional variables, `DATABASE_PATH` and `SEED_PATH`, with defaults `resume.db` and `data/resume.json` in the repo folder, so no config file was needed.

## 6. Data

- [x] `resume.db` is gitignored, so it does not come with the clone. I rebuilt it on the VM from the checked-in seed with the app's own importer (`import_seed(Path('resume.db'), Path('data/resume.json'))`) instead of copying the Codespace file with scp.
- [x] `PRAGMA integrity_check` returned `ok`. Row counts: 1 profile, 11 experiences, 0 skills (the resume has no skills section).

## 7. Processes

- [x] Run the app by hand on `127.0.0.1:8000` and check `/health`.
- [x] Two locks demo with a temporary rule `Temp-HTTP-8000` (laptop /32 only). Firewall open but app on `127.0.0.1` gave connection refused. App on `0.0.0.0` and firewall open gave `{"status":"ok"}` from the laptop.
- [x] Remove `Temp-HTTP-8000`.
- [x] Run the app as a systemd service (`career-platform.service`) bound to `127.0.0.1:8000` with `--proxy-headers`, enabled at boot, `Restart=on-failure`.
- [x] Nginx site on port 80 proxying to `127.0.0.1:8000`; open ports 80 and 443 to the internet with `Allow-HTTP` and `Allow-HTTPS`.

## 8. Verify

| Check | Command | Result |
| --- | --- | --- |
| SSH with key from the laptop | `ssh -i ... azureuser@PUBLIC-IP` | Logged in |
| App alive on the VM | `curl http://127.0.0.1:8000/health` | `{"status":"ok"}` |
| Database healthy | `sqlite3 resume.db "PRAGMA integrity_check;"` | `ok` |
| Lock 2: app on loopback only | laptop `curl PUBLIC-IP:8000/health`, rule open | Connection refused |
| Both locks open | same, app on `0.0.0.0` | `{"status":"ok"}` |
| Service survives hand-off | `systemctl is-active career-platform` | `active` |
| Nginx reaches the app | laptop `curl http://PUBLIC-IP/health` | `{"status":"ok"}` |
| Lock 1: no rule for 8000 | laptop `curl -m 8 PUBLIC-IP:8000/health` after removing the rule | TBD |

## 9. Shutdown

- [ ] Deallocate the VM. **Skipped on purpose:** Exercise 04 requires the VM to keep running through its deadline, so shutdown happens after the HTTPS exercise, not now.
