variable "subnet_ids" {}
variable "db_instance_class" {
  default = "db.t3.micro"
}
variable "db_username" {}
variable "db_password" {}
variable "engine" {
  default = "mysql"
}
variable "engine_version" {
  default = "8.0"
}
variable "family" {
  default = "mysql8.0"
}
variable "region" {
  description = "AWS region to deploy resources in"
  type        = string
}

variable "access_key" {
  description = "AWS access key"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "AWS secret key"
  type        = string
  sensitive   = true
}
