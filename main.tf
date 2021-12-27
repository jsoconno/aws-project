module "ecr" {
    source = "github.com/jsoconno/aws-modules-ecr?ref=v1.0.0"
    name = "ecr-test"

    tags = var.tags
}