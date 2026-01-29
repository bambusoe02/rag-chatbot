output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "cluster_name" {
  value = module.eks.cluster_name
}

output "cluster_certificate_authority_data" {
  value     = module.eks.cluster_certificate_authority_data
  sensitive = true
}

output "database_endpoint" {
  value = aws_db_instance.postgres.endpoint
}

output "database_password" {
  value     = random_password.db_password.result
  sensitive = true
}

output "s3_backup_bucket" {
  value = aws_s3_bucket.backups.bucket
}

output "configure_kubectl" {
  value = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

