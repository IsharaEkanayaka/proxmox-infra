output "vm_ids" {
  description = "IDs of created VMs"
  value       = proxmox_virtual_environment_vm.k8s_node[*].vm_id
}

output "vm_names" {
  description = "Names of created VMs"
  value       = proxmox_virtual_environment_vm.k8s_node[*].name
}

output "vm_ip_addresses" {
  description = "Primary IP addresses of created VMs"
  value = [
    for vm in proxmox_virtual_environment_vm.k8s_node :
    try(vm.ipv4_addresses[1][0], "pending")
  ]
}

output "control_plane_ips" {
  description = "Control plane node IPs"
  value = [
    for i in range(var.control_plane_count) :
    "${var.vm_ip_prefix}${var.vm_ip_start + i}"
  ]
}

output "worker_ips" {
  description = "Worker node IPs"
  value = [
    for i in range(var.worker_count) :
    "${var.vm_ip_prefix}${var.vm_ip_start + var.control_plane_count + i}"
  ]
}
