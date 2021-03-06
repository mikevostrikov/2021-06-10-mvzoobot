output "account_id" {
  value = data.aws_caller_identity.current.account_id
}

output "region" {
  value = data.aws_region.current.name
}

output "app" {
  value = local.app
}

output "workspace" {
  value = terraform.workspace
}
