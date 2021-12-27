module "ecr" {
    source = "github.com/jsoconno/terraform-module-aws-ecr?ref=v1.0.0"
    
    name = "ecr-test"

    tags = var.tags
}