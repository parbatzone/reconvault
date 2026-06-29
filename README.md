# ReconVault 🔍

> The recon notes organizer bug bounty hunters actually asked for.

ReconVault is a dark-themed, terminal-aesthetic desktop app for Linux 
built for security researchers, bug bounty hunters, and CTF players. 
Ditch the scattered text files and spreadsheets — organize every 
target's subdomains, ports, endpoints, vulnerabilities, and notes 
in one place. 100% local. No cloud. No account. No internet required.

---

## ⚡ Quick Start

### Prerequisites
- Linux (Kali, Ubuntu, Debian-based)
- Python 3.10+

### Install & Run

```bash
# Clone the repo
git clone https://github.com/parbatzone/reconvault.git
cd reconvault

# Install dependencies
pip install -r requirements.txt

# Run
python3 reconvault.py
```

On first run, ReconVault automatically creates a local SQLite database 
at `~/.reconvault/reconvault.db`. Your data never leaves your machine.

---

## 🗂️ Features

**Target Management**
Create, search, and manage targets — each with name, domain, 
platform (HackerOne, Bugcrowd, CTF, etc.), and timestamps.

**Per-Target Workspace (5 tabs)**

| Tab | What You Track |
|-----|---------------|
| Subdomains | Domain · IP · Live/Dead status · Tech stack · Notes |
| Ports & Services | IP · Port · Protocol · Service · Version · Notes |
| Endpoints | URL · Method · Parameters · Status code · Notes |
| Vulnerabilities | Title · Severity · Status · CVE/CWE · Description |
| Notes | Freeform notes editor — auto-saves as you type |

**Vulnerability Severity Badges**

![Critical](https://img.shields.io/badge/Critical-red)
![High](https://img.shields.io/badge/High-orange)
![Medium](https://img.shields.io/badge/Medium-yellow)
![Low](https://img.shields.io/badge/Low-blue)
![Info](https://img.shields.io/badge/Info-grey)

**Dashboard**
Home screen showing total targets, vulnerability breakdown by 
severity, and recently modified targets.

**Nmap Import**
Import port scan results directly from Nmap `-oN` text output 
into the Ports & Services tab.

**Markdown Export**
Export any target's full findings as a clean Markdown report — 
saved to `~/Desktop/reconvault_[target]_[date].md`.

**Global Search**
Search across all targets and all tabs simultaneously from 
a single search bar.

---

## 🖥️ Screenshots

> Coming soon

---

## 🗃️ Data Storage

All data is stored locally in a SQLite database:
