provider "docker" {
  host = "npipe:////./pipe/dockerDesktopLinuxEngine"
}

resource "docker_image" "acg_terraform_test" {
  name         = "alpine:3.22"
  keep_locally = true
}

resource "docker_container" "acg_terraform_test" {
  name  = "acg-terraform-test"
  image = docker_image.acg_terraform_test.image_id

  command = [
    "sh",
    "-c",
    "echo ACG Terraform resource created successfully && sleep 3600"
  ]
}
