variable "proxmox_api_url" {
  type    = string
  default = ""
}

variable "proxmox_api_token_id" {
  type    = string
  default = ""
}

variable "proxmox_api_token_secret" {
  type      = string
  default   = ""
  sensitive = true
}


packer {
  required_plugins {
    proxmox = {
      version = ">= 1.1.3"
      source  = "github.com/hashicorp/proxmox"
    }
  }
}

source "proxmox-iso" "ubuntu-server" {
  proxmox_url = var.proxmox_api_url
  username    = var.proxmox_api_token_id
  token       = var.proxmox_api_token_secret
  insecure_skip_tls_verify = true
  
  node      = "pve1"
  vm_id     = "990"
  vm_name   = "ubuntu-server-template"
  
  boot_iso {
    type     = "ide"
    iso_file = "local:iso/ubuntu-22.04.5-live-server-amd64.iso"
    unmount  = true
  }
  qemu_agent       = true
  cores            = 2
  memory           = 2048
  scsi_controller  = "virtio-scsi-pci"

  cloud_init              = true
  cloud_init_storage_pool = "local-lvm"

  disks {
    disk_size    = "20G"
    format       = "raw"
    storage_pool = "local-lvm"
    type         = "scsi"
  }

  network_adapters {
    model    = "virtio"
    bridge   = "vmbr0"
    firewall = "false"
  }

  additional_iso_files {
    cd_files         = ["./http/user-data", "./http/meta-data"]
    cd_label         = "cidata"
    iso_storage_pool = "local"
    unmount          = true
    type             = "ide"
    index            = 3
  }

  boot_wait = "10s"
  
  boot_command = [
    "c",
    "<wait2>",
    "linux /casper/vmlinuz --- autoinstall ds=nocloud;s=/cdrom/",
    "<enter>",
    "<wait2>",
    "initrd /casper/initrd",
    "<enter>",
    "<wait2>",
    "boot<enter>"
  ]

  ssh_username = "ubuntu"
  ssh_password = "ubuntu"
  ssh_timeout  = "30m"
  ssh_handshake_attempts = 100
}

build {
  sources = ["source.proxmox-iso.ubuntu-server"]

  provisioner "shell" {
    inline = [
      "echo '--- Resetting machine-id ---'",
      "echo -n | sudo tee /etc/machine-id",
      "sudo rm -f /var/lib/dbus/machine-id",

      "echo '--- Removing subiquity configs that block cloud-init networking ---'",
      "sudo rm -f /etc/cloud/cloud.cfg.d/subiquity-disable-cloudinit-networking.cfg",
      "sudo rm -f /etc/cloud/cloud.cfg.d/99-installer.cfg",
      "sudo rm -f /etc/cloud/cloud.cfg.d/curtin-preserve-sources.cfg",

      "echo '--- Removing autoinstall netplan configs ---'",
      "sudo rm -f /etc/netplan/*.yaml",
      "sudo rm -f /etc/netplan/*.yml",

      "echo '--- Configuring cloud-init datasource for Proxmox (NoCloud) ---'",
      "echo 'datasource_list: [NoCloud, ConfigDrive, None]' | sudo tee /etc/cloud/cloud.cfg.d/99-pve.cfg",

      "echo '--- Cleaning cloud-init state ---'",
      "sudo cloud-init clean --logs",
      "sudo rm -rf /var/lib/cloud/",

      "echo '--- Truncating logs ---'",
      "sudo truncate -s 0 /var/log/cloud-init.log || true",
      "sudo truncate -s 0 /var/log/cloud-init-output.log || true"
    ]
  }
}