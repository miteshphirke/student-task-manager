# 🎓 Student Task Management System — Full DevOps Project

A beginner-friendly college DevOps project that takes a simple **Flask + SQLite**
web app all the way through a real pipeline:

```
Developer → GitHub → Jenkins → Build & Test (Pytest) → Docker Image
   → Ansible → Ubuntu VM Deployment → Monitoring (Prometheus + Grafana)
```

This README is written for **Windows** users and is split into **stages**.
Do them in order — each stage ends with something you can test before moving on.

---

## 0. Project structure

```
student-task-manager/
├── app/
│   ├── app.py                 # Flask application (routes, metrics)
│   ├── models.py               # SQLite database logic
│   ├── requirements.txt
│   ├── templates/               # HTML (Jinja2)
│   ├── static/style.css         # CSS
│   └── tests/test_app.py        # Pytest test suite
├── Dockerfile
├── docker-compose.yml           # App + Prometheus + Grafana
├── .dockerignore
├── Jenkinsfile                  # CI/CD pipeline definition
├── ansible/
│   ├── inventory.ini            # Target Ubuntu VM(s)
│   ├── ansible.cfg
│   ├── requirements.yml         # Ansible Galaxy collections needed
│   └── deploy.yml               # Deployment playbook
├── monitoring/
│   ├── prometheus.yml
│   └── grafana/provisioning/    # Auto-configured datasource + dashboard
├── .gitignore
└── README.md
```

---

## 1. Prerequisites (install these on Windows first)

| Tool | Why | Download |
|---|---|---|
| **Python 3.11+** | Run/test the Flask app | https://www.python.org/downloads/ (tick "Add Python to PATH") |
| **Git for Windows** | Version control | https://git-scm.com/download/win |
| **Docker Desktop** | Build/run containers (enable WSL2 backend) | https://www.docker.com/products/docker-desktop |
| **WSL2 + Ubuntu** | Needed to run Ansible (Ansible does not run natively on Windows) | `wsl --install -d Ubuntu` in PowerShell (Admin) |
| **VS Code** (optional) | Editing files | https://code.visualstudio.com/ |
| **A GitHub account** | Remote repo + Jenkins trigger | https://github.com |

> 💡 **Why WSL2 for Ansible?** Ansible's control node must be Linux/macOS.
> The easiest way to get that on Windows is WSL2's Ubuntu. Jenkins itself
> can run natively on Windows or inside WSL2 — this guide uses WSL2 for
> Jenkins + Ansible so everything Linux-related lives in one place, and
> Docker Desktop (Windows) handles containers for both.

Verify installs in PowerShell:
```powershell
python --version
git --version
docker --version
docker compose version
wsl --list --verbose
```

---

## STAGE 1 — Run the Flask app locally (no Docker yet)

**Goal:** confirm the core application works before adding any DevOps layers.

```powershell
cd student-task-manager\app
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open your browser at **http://127.0.0.1:5000** — you should see the
Student Task Manager UI. Add a task, edit it, mark it Completed, delete it.

Also check:
- http://127.0.0.1:5000/health → `{"status": "healthy"}`
- http://127.0.0.1:5000/metrics → a page of Prometheus-style metrics text

Stop the server with `CTRL+C` when done.

✅ **Checkpoint:** you can create/edit/delete tasks and both extra endpoints respond.

---

## STAGE 2 — Run the automated tests (Pytest)

Still inside `app\` with the virtual environment activated:

```powershell
pytest -v
```

You should see **7 passed**. These tests use a temporary SQLite file, so
your real `tasks.db` (if any) is untouched. This is exactly the command
Jenkins will run automatically later.

✅ **Checkpoint:** all tests pass locally before you touch Git/Docker.

---

## STAGE 3 — Put the project on Git & GitHub

```powershell
cd student-task-manager
git init
git add .
git commit -m "Initial commit: Flask Student Task Manager"
```

Create an **empty** repository on GitHub (no README/license, since you
already have files), then:

```powershell
git branch -M main
git remote add origin https://github.com/<your-username>/student-task-manager.git
git push -u origin main
```

✅ **Checkpoint:** refresh your GitHub repo page and confirm all files are there.

---

## STAGE 4 — Build and run with Docker & Docker Compose

**Goal:** package the app into a container, and bring up the app +
Prometheus + Grafana together, exactly as they'll run on the Ubuntu VM.

Make sure Docker Desktop is running, then from the project root:

```powershell
docker compose up --build
```

This builds the `web` image from the `Dockerfile`, and starts three containers:
- `student-task-manager` → http://localhost:5000
- `prometheus` → http://localhost:9090
- `grafana` → http://localhost:3000 (login `admin` / `admin`)

Open another PowerShell window to check container status and logs:

```powershell
docker ps
docker logs student-task-manager
docker logs -f student-task-manager     # follow logs live
```

Stop everything with `CTRL+C`, then:
```powershell
docker compose down
```

(Add `-v` to also delete the named volumes — including your task data — if
you want a totally clean slate: `docker compose down -v`.)

✅ **Checkpoint:** you can reach the app, Prometheus, and Grafana in your browser,
and `docker logs` shows request activity.

---

## STAGE 5 — Set up an Ubuntu VM (deployment target)

You need a separate Ubuntu machine (real or virtual) that Ansible will deploy to.
Options, easiest first:

1. **Oracle VirtualBox** — install VirtualBox on Windows, download **Ubuntu
   Server 22.04 LTS** ISO, create a VM (2 CPU / 2–4 GB RAM), install Ubuntu,
   enable OpenSSH during setup (`sudo apt install openssh-server` if you forgot).
2. **A cloud VM** (AWS EC2 / Azure / a college lab server) running Ubuntu 22.04.
3. A second WSL2 Ubuntu instance (works for a class demo, though a "real" VM
   better matches the assignment's architecture).

Whichever you choose, from that VM, note its **IP address**:
```bash
ip a        # look for something like 192.168.1.50
```

From Windows, add your SSH public key to the VM so Ansible can log in
without a password:
```powershell
ssh-keygen -t rsa -b 4096          # if you don't already have a key, in PowerShell
type $env:USERPROFILE\.ssh\id_rsa.pub | ssh ubuntu@<VM_IP> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

Test the connection:
```powershell
ssh ubuntu@<VM_IP>
```

✅ **Checkpoint:** you can SSH into the Ubuntu VM without typing a password.

---

## STAGE 6 — Configure and run Ansible (from WSL2)

Ansible needs Linux, so do this stage **inside WSL2 Ubuntu**, not PowerShell.

Open the "Ubuntu" app (installed in the prerequisites step), then:

```bash
sudo apt update
sudo apt install -y ansible sshpass rsync
ansible --version
```

Copy or clone your project into WSL2 (easiest: clone from GitHub):
```bash
cd ~
git clone https://github.com/<your-username>/student-task-manager.git
cd student-task-manager/ansible
```

Install the required Ansible collection:
```bash
ansible-galaxy collection install -r requirements.yml
```

Edit `inventory.ini` and put in your **real** VM IP, username, and the
path to your **WSL2** private key (if you generated a key in Windows,
regenerate one inside WSL2 with `ssh-keygen`, or copy `id_rsa` from the
Windows `.ssh` folder into WSL2's `~/.ssh/`):

```ini
[app_servers]
192.168.1.50 ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/id_rsa
```

Test connectivity:
```bash
ansible app_servers -m ping
```
Expect `"ping": "pong"` back. Then run the real deployment:

```bash
ansible-playbook -i inventory.ini deploy.yml
```

This playbook will, on the Ubuntu VM: install Docker + Docker Compose,
copy the project files across, and run `docker compose up --build -d`.

Check it worked (from WSL2 or Windows browser):
```bash
curl http://<VM_IP>:5000/health
```
Or open `http://<VM_IP>:5000`, `http://<VM_IP>:9090` (Prometheus), and
`http://<VM_IP>:3000` (Grafana) in your Windows browser.

✅ **Checkpoint:** the app, Prometheus and Grafana are all reachable at the VM's IP.

---

## STAGE 7 — Set up Jenkins and the CI/CD pipeline

You can run Jenkins either natively on Windows or (recommended, since it needs
Docker + Ansible alongside it) inside **WSL2**.

### 7a. Install Jenkins in WSL2

```bash
sudo apt update
sudo apt install -y openjdk-17-jre
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee \
  /usr/share/keyrings/jenkins-keyring.asc > /dev/null
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc]" \
  "https://pkg.jenkins.io/debian-stable binary/" | sudo tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt update
sudo apt install -y jenkins
sudo service jenkins start
```

Open **http://localhost:8080** in your Windows browser (WSL2 shares localhost
with Windows). Unlock Jenkins using the password shown by:
```bash
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```
Install the **"suggested plugins"**, then create your admin user.

### 7b. Give Jenkins the tools it needs

Still in WSL2:
```bash
# Docker: install and let jenkins user run it
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker jenkins
sudo usermod -aG docker $USER

# Python + Ansible (if not already installed)
sudo apt install -y python3-venv python3-pip ansible

sudo service jenkins restart
```

In Jenkins → **Manage Jenkins → Plugins**, also install: **Git plugin**,
**Pipeline**, and **JUnit** (usually already included in "suggested plugins").

### 7c. (Optional) Add Docker Hub credentials

If you want the pipeline to push images to Docker Hub: go to
**Manage Jenkins → Credentials → System → Global credentials → Add Credentials**,
choose "Username with password", and set the **ID** to `dockerhub-creds`.
Then set the Jenkins pipeline's `PUSH_TO_REGISTRY` environment variable to
`true` (Job configuration → Build Environment / Pipeline parameters), and
edit `DOCKERHUB_REPO` in the `Jenkinsfile` to your own Docker Hub username.
This step is entirely optional for a college demo — the pipeline works
without it by just building the image locally on the Jenkins agent.

### 7d. Create the pipeline job

1. Jenkins Dashboard → **New Item** → name it `student-task-manager` → type **Pipeline** → OK.
2. Under **Pipeline**, set:
   - Definition: **Pipeline script from SCM**
   - SCM: **Git**
   - Repository URL: `https://github.com/<your-username>/student-task-manager.git`
   - Branch: `*/main`
   - Script Path: `Jenkinsfile`
3. Save, then click **Build Now**.

Watch the stages run in **Stage View**: Checkout → Set Up Python →
Run Tests → Build Docker Image → (Push, optional) → Deploy with Ansible →
Health Check.

### 7e. (Optional) Auto-trigger builds from GitHub

Add a **GitHub webhook** (repo Settings → Webhooks → Add webhook) pointing
to `http://<your-public-jenkins-url>/github-webhook/`, and enable
**"GitHub hook trigger for GITScm polling"** in the Jenkins job's
configuration. (This requires Jenkins to be reachable from the internet —
for a local college demo it's fine to just click **Build Now** manually.)

✅ **Checkpoint:** a full pipeline run turns green, and re-checking the VM
shows the new build deployed (e.g., `docker ps` on the VM shows a fresh
container start time).

---

## STAGE 8 — Monitoring: Prometheus & Grafana

These already came up automatically in Stages 4 and 6 via `docker-compose.yml`.
This stage is about actually **using** them.

1. Open **Prometheus** at `http://<VM_IP or localhost>:9090` → **Status → Targets**
   → confirm the `student-task-manager` job shows **State: UP**.
2. Try a query in the Prometheus "Graph" tab, e.g.:
   ```
   rate(flask_app_request_count_total[5m])
   ```
3. Open **Grafana** at `http://<VM_IP or localhost>:3000` (login `admin`/`admin`,
   you'll be asked to set a new password on first login).
4. The **Prometheus data source** and a starter **"Student Task Manager"**
   dashboard are pre-provisioned (see `monitoring/grafana/provisioning/`) —
   go to **Dashboards** and open it directly. It shows total requests,
   requests-per-endpoint, and average latency.
5. Click around the app (add/edit/delete a few tasks) and watch the
   dashboard update within ~15 seconds.

✅ **Checkpoint:** the Grafana dashboard visibly reacts to your clicks on the app.

---

## STAGE 9 — Log management with Docker logs

No extra setup needed — this uses what's already configured
(`json-file` logging driver with rotation, set in `docker-compose.yml`).

```bash
docker logs student-task-manager            # all logs so far
docker logs -f student-task-manager          # follow live
docker logs --since 10m student-task-manager # last 10 minutes
docker logs --tail 50 student-task-manager   # last 50 lines
```

Gunicorn's access log (in the Dockerfile's `CMD`) prints one line per
HTTP request, so you can watch real traffic arrive as you use the app or
as Jenkins runs its post-deploy health check.

✅ **Checkpoint:** you can see individual HTTP requests appear in
`docker logs -f` as you interact with the site.

---

## Full pipeline, end-to-end test

Once every stage above works individually, the real test is:
1. Change something small in `app/app.py` or a template.
2. `git add . && git commit -m "..." && git push`
3. In Jenkins, click **Build Now** (or let the webhook trigger it).
4. Watch Jenkins: checkout → tests → Docker build → Ansible deploy → health check.
5. Refresh `http://<VM_IP>:5000` and confirm your change is live.
6. Check Grafana/Prometheus still show metrics, and `docker logs` on the VM
   shows the new container's startup + your test traffic.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `pytest` fails with "duplicated timeseries" | Make sure you're on the version of `tests/test_app.py` included here — it avoids re-importing `app.py` per test. |
| `docker compose up` fails to bind port 5000/9090/3000 | Something else is using that port. Stop it, or change the left-hand port number in `docker-compose.yml` (e.g. `"5001:5000"`). |
| Ansible `ping` fails with "UNREACHABLE" | Check the VM IP, that SSH works manually (`ssh ubuntu@<ip>`), and that the private key path in `inventory.ini` is correct **inside WSL2**. |
| Ansible fails on `docker_compose_v2` module not found | Run `ansible-galaxy collection install -r requirements.yml` inside `ansible/`. |
| Jenkins can't run `docker` commands | Confirm `sudo usermod -aG docker jenkins` was run, then `sudo service jenkins restart` (group membership needs a fresh session). |
| Grafana dashboard is empty | Confirm Prometheus target is "UP" first (Stage 8, step 1) — Grafana only shows what Prometheus has already scraped. |
| WSL2 can't reach `localhost:8080` for Jenkins | Restart WSL2 (`wsl --shutdown` in PowerShell, then reopen Ubuntu), or check Windows Firewall isn't blocking it. |

---

## What each tool is doing (quick reference for your report/viva)

- **Flask + SQLite** — the actual web application (CRUD task manager).
- **Pytest** — automated tests run on every code change, before anything is built.
- **Git/GitHub** — version control and the trigger source for CI.
- **Jenkins** — orchestrates the whole pipeline: test → build → deploy.
- **Docker** — packages the app (and its exact dependencies) into one portable image.
- **Docker Compose** — runs the app + Prometheus + Grafana together as one stack.
- **Ansible** — automates installing Docker on the VM and deploying the stack there,
  so deployment is repeatable and not done by hand over SSH.
- **Ubuntu VM** — the target "production" server the app is deployed to.
- **Prometheus** — scrapes `/metrics` from the Flask app every 15s and stores the time-series data.
- **Grafana** — visualizes Prometheus's data as dashboards.
- **Docker logs** — captures stdout/stderr from every container for debugging and auditing.
