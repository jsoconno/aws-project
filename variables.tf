variable "region" {
  type        = string
  description = "The region where resources will be deployed as part of the Terraform configuration."
  default = "us-east-1"
}

variable "tags" {
  type        = map(string)
  description = "A map of strings used to add tags during the deployment."
}