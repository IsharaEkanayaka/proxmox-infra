terraform {
  backend "local" {
    path = "C:/terraform-state/terraform.tfstate"
  }
}
provider "proxmox" {
  endpoint = var.proxmox_api_url
  api_token = "${var.proxmox_api_token_id}=${var.proxmox_api_token_secret}"
  insecure = true
}
