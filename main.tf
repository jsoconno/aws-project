module "s3" {
    source = "github.com/jsoconno/terraform-module-aws-iam?ref=v1.0.0"
    # source = "../terraform-module-aws-s3"

    tags = var.tags
}