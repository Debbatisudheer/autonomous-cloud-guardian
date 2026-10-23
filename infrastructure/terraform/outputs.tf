output "terraform_test_container_name" {
  description = "Name of the Terraform-managed test container."
  value       = docker_container.acg_terraform_test.name
}

output "terraform_test_container_id" {
  description = "Docker ID of the Terraform-managed test container."
  value       = docker_container.acg_terraform_test.id
}
