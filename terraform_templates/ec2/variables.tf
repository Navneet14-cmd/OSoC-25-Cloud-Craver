variable "ami_id" {
  description = "The AMI ID"
  type        = string
}

variable "key_name" {
  description = "The key pair name"
  type        = string
}

variable "instance_type" {
  description = "Type of EC2 instance"
  type        = string
}

variable "region" {
  description = "AWS region to deploy resources"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID where the instance will be launched"
  type        = string
}
