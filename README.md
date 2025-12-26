
# Automated Ubuntu Server Template for Proxmox

This repository contains HashiCorp Packer configuration to automate the creation of a "Golden Image" (Template) for Ubuntu Server 22.04 on a Proxmox VE environment.

It is specifically designed for environments behind a strict network gateway (e.g., University networks), utilizing **Cloud-Init (NoCloud/CD-ROM)** for configuration and **Bastion Hosts** for connectivity.

## 🚀 Features

- **Fully Automated:** Installs Ubuntu Server, creates a user, and installs the QEMU Guest Agent without manual intervention.
- **Firewall Proof:** Uses a local "CIDATA" ISO (CD-ROM method) to inject `user-data`, bypassing network restrictions that block HTTP servers.
- **Network Tunneling:** Configured to work through an SSH Bastion/Jump Host (`tesla.ce.pdn.ac.lk`) to reach private Proxmox nodes.

## 🛠 Prerequisites

Before running this build, ensure you have the following installed on your local machine:

### 1. HashiCorp Packer

Install Packer from HashiCorp's official site:

- https://developer.hashicorp.com/packer/downloads

### 2. Xorriso (Critical)

Packer requires `xorriso` to generate the Cloud-Init ISO file.

- **Linux (Ubuntu/Debian/Kali):** `sudo apt install xorriso`
- **macOS:** `brew install xorriso`
- **Windows:** You **must** run this project inside **WSL (Windows Subsystem for Linux)**. It will not work in PowerShell.

---

## ⚙️ Configuration Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/proxmox-packer.git
cd proxmox-packer
```

### 2. Create Credentials File

Create a file named `credentials.auto.pkrvars.hcl` in the root directory.

⚠️ **IMPORTANT:** This file is ignored by `.gitignore`. Never commit it to GitHub.

Paste the following content and update it with your details:

```hcl
# credentials.auto.pkrvars.hcl

# API Connection (Targeting localhost because of the SSH Tunnel)
proxmox_api_url          = "https://localhost:8006/api2/json"
proxmox_api_token_id     = "your-token-id"
proxmox_api_token_secret = "your-proxmox-api-token-secret"

# SSH Bastion Credentials (Gateway: tesla.ce.pdn.ac.lk)
ssh_bastion_password     = "your-tesla-password"
```

## 🏗️ How to Build

### Step 1: Open the SSH Tunnel

Since the Proxmox API is behind the university firewall, you must open a tunnel from your laptop to the Proxmox node.

Run this in a separate terminal window:

```bash
# Syntax: ssh -N -f -L localhost:8006:<PROXMOX_IP>:8006 <USER>@<BASTION_HOST>
ssh -N -f -L localhost:8006:10.40.18.xx:8006 e20094@tesla.ce.pdn.ac.lk
```

- Replace `10.40.18.xx` with your specific Proxmox Node IP.
- Replace <USER> with your registration number.

### Step 2: Initialize & Build

In your main terminal (WSL or Linux):

```bash
# 1. Download Packer plugins
packer init .

# 2. Run the build
packer build .
```

### Step 3: Wait

The process takes approximately 7–10 minutes.

- Packer uploads the ISO and boots the VM.
- Ubuntu installs automatically (updates are disabled for speed).
- Packer connects via SSH (through Tesla) to verify the build.
- The VM is shut down and converted to Template ID `990`.

## 📂 Project Structure

```text
.
├── credentials.auto.pkrvars.hcl  # Secrets (NOT committed to Git)
├── ubuntu-server.pkr.hcl         # Main Packer configuration
├── variables.pkr.hcl             # Variable definitions
├── http/
│   ├── user-data                 # Autoinstall config (packages, users)
│   └── meta-data                 # Hostname config
└── README.md                     # This documentation
```

## 🐛 Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| Timeout waiting for SSH | Packer cannot verify the build. | 1. Ensure `qemu-guest-agent` is in `user-data`. 2. Check if `ssh_bastion_host` is correct. 3. Increase `ssh_timeout` to `45m`. |
| Code 0004: Could not read from CDROM | BIOS boot order issue. | Ensure `boot_iso` type is `ide` and `additional_iso_files` type is `sata` (or vice versa). |
| Build finished but no artifact | SSH Tunnel closed/failed. | Verify you can reach `https://localhost:8006` in your browser before building. |
| `xorriso` not found | Missing dependency. | Install `xorriso` (see Prerequisites). |

## 📜 License

This project is for educational purposes at the University of Peradeniya.

