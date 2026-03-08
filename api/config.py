import os
import re

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TERRAFORM_DIR = os.path.join(PROJECT_ROOT, 'terraform')
ANSIBLE_DIR = os.path.join(PROJECT_ROOT, 'ansible')
WORKSPACES_DIR = os.path.join(PROJECT_ROOT, 'workspaces')
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
DB_PATH = os.path.join(DATA_DIR, 'api.db')

# Network defaults (override via environment variables)
VM_IP_PREFIX = os.getenv('VM_IP_PREFIX', '10.40.19.')
VM_IP_START = int(os.getenv('VM_IP_START', '201'))
VM_IP_GATEWAY = os.getenv('VM_IP_GATEWAY', '10.40.19.254')
VM_DNS_SERVER = os.getenv('VM_DNS_SERVER', '10.40.2.1')


def read_base_tfvars() -> dict:
    """Read Proxmox credentials and defaults from the base terraform.tfvars."""
    tfvars: dict = {}
    tfvars_path = os.path.join(TERRAFORM_DIR, 'terraform.tfvars')
    if not os.path.exists(tfvars_path):
        return tfvars
    with open(tfvars_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # String values
            match = re.match(r'^(\w+)\s*=\s*"(.+)"', line)
            if match:
                tfvars[match.group(1)] = match.group(2)
                continue
            # Numeric values
            match = re.match(r'^(\w+)\s*=\s*(\d+)', line)
            if match:
                tfvars[match.group(1)] = int(match.group(2))
    return tfvars
