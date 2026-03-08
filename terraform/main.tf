locals {
  total_vms = var.control_plane_count + var.worker_count
}

resource "proxmox_virtual_environment_vm" "k8s_node" {
  count = local.total_vms

  name        = "${var.vm_name_prefix}-${count.index + 1}"
  node_name   = var.target_node
  
  clone {
    vm_id = var.template_id
    full  = true
  }

  agent {
    enabled = true
  }

  cpu {
    cores = var.vm_cores
  }

  memory {
    dedicated = var.vm_memory
  }

  network_device {
    bridge = var.network_bridge
  }

  operating_system {
    type = "l26"
  }

  initialization {
    datastore_id = var.vm_storage
    interface    = "ide2"
    ip_config {
      ipv4 {
        address = "${var.vm_ip_prefix}${var.vm_ip_start + count.index}/24"
        gateway = var.vm_ip_gateway
      }
    }
    dns {
      servers = [var.vm_dns_server]
    }
    user_account {
      username = var.ssh_user
      password = var.ssh_password
    }
  }
}

resource "local_file" "ansible_inventory" {
  filename        = "${path.module}/../ansible/inventory.ini"
  file_permission = "0644"

  content = join("\n", concat(
    ["[control_plane]"],
    [for i in range(var.control_plane_count) :
      "${var.vm_name_prefix}-${i + 1} ansible_host=${var.vm_ip_prefix}${var.vm_ip_start + i}"
    ],
    ["", "[workers]"],
    [for i in range(var.worker_count) :
      "${var.vm_name_prefix}-${var.control_plane_count + i + 1} ansible_host=${var.vm_ip_prefix}${var.vm_ip_start + var.control_plane_count + i}"
    ],
    ["", "[k8s:children]", "control_plane", "workers"],
    ["", "[k8s:vars]",
      "ansible_user=${var.ssh_user}",
      "ansible_password=${var.ssh_password}",
      "ansible_become=true",
      "ansible_become_password=${var.ssh_password}",
      "ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'",
      ""
    ]
  ))
}
