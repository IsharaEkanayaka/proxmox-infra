# Proxmox VE Infrastructure Automation

Automates **Proxmox VE** virtual machine deployment using **Terraform** and **CI/CD pipelines** to ensure consistent, version-controlled infrastructure.

---

## 1. Environment Configuration

### A. SSH Tunneling

You need to create an **SSH tunnel** to securely connect to the internal **Proxmox API**.
(Consider the guide at the root)

### B. GitHub Actions Secrets

You’ll need to store **encrypted secrets** in your GitHub repository to keep sensitive information safe. Go to **GitHub Settings > Secrets and variables > Actions** and add the following secrets:

*   **PROXMOX_API_URL**: `https://localhost:8006/api2/json`
*   **PROXMOX_API_TOKEN_ID**: Your Proxmox API Token ID
*   **PROXMOX_API_TOKEN_SECRET**: Your Proxmox API Token Secret
*   **VM_PASSWORD**: The password for the Ubuntu VMs that will be provisioned

### C. State Persistence

Terraform needs to remember the current state of the infrastructure to avoid creating duplicate resources. To do this:

1. **Create the directory** `C:\terraform-state\` on your machine where the runner is installed.
2. This will store the state file for Terraform, which helps in tracking the resources it has already created.

## 2. Self-Hosted Runner Setup

You need to set up a **Self-Hosted Runner** on your local machine to run the CI/CD pipeline.

### Installation:

1. Go to **GitHub Settings > Actions > Runners > New self-hosted runner**.
2. Follow the instructions to set it up on your local machine.

### Execution Policy (Windows only):

If you're using **Windows**, run this command to allow the execution of the runner script:

```powershell
Set-ExecutionPolicy RemoteSigned -Scope LocalMachine

### Start the Runner:

1. Navigate to the directory where the runner is installed.
2. Run the following command to start the runner:

```powershell
.\run.cmd

The runner should stay **idle (green)** and ready to trigger the CI/CD pipeline when necessary.

## 3. Operational Procedures

### Scaling the Cluster

To change the number of **worker nodes** in the cluster , update the **`TF_VAR_worker_count`** variable in the **`.github/workflows/infra-deploy.yml`** file.

### Deployment & Validation

#### Trigger:
Every time you push code to the **`main`** branch, the pipeline will automatically start.

#### Pipeline Workflow:
The runner will:
1. **Run `terraform plan`** to check what changes need to be made.
2. Then, it will **run `terraform apply`** to make the changes and create the resources.