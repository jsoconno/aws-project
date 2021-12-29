module "lambda" {
  source = "github.com/jsoconno/terraform-module-aws-lambda?ref=v1.0.1"
#   source = "../terraform-module-aws-lambda"

  name = "test-lambda"
  layers = [
    "arn:aws:lambda:us-east-1:363121595583:layer:CustomLayer:1"
  ]

  tags = var.tags
}