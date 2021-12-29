data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

locals {
  body = jsonencode({
    swagger = "2.0"
    info = {
      title   = "Example"
      version = "1.0"
    }
    schemes = [
      "https"
    ]
    paths = {
      "/path" = {
        get = {
          responses = {
            "200" = {
              description = "200 response"
            }
          }
          x-amazon-apigateway-integration = {
            type       = "AWS"
            uri        = module.lambda.invoke_arn
            httpMethod = "POST"
            responses = {
              default = {
                statusCode = 200
              }
            }
          }
        }
      }
    }
  })
}

module "api_gateway" {
  source = "github.com/jsoconno/terraform-module-aws-api-gateway?ref=v1.0.0"
  #   source = "../terraform-module-aws-api-gateway"

  name = "test-api-gateway"
  body = local.body

  tags = var.tags
}

module "lambda" {
  source = "github.com/jsoconno/terraform-module-aws-lambda?ref=v1.1.1"
  #   source = "../terraform-module-aws-lambda"

  name = "test-lambda"

  environment_variables = {
    REGION = data.aws_region.current.name
    BUCKET = module.s3.id
  }

  api_gateway_source_arns = [
    module.api_gateway.execution_arn
  ]

  # Something to consider adding later
  #   s3_bucket_target_arns = [

  #   ]

  tags = var.tags
}

module "s3" {
  source = "github.com/jsoconno/terraform-module-aws-s3?ref=v1.0.0"

  tags = var.tags
}

data "aws_iam_policy_document" "allow_access_s3" {
  statement {
    sid    = "AllowAccessToListBucket"
    effect = "Allow"
    actions = [
      "s3:ListBucket"
    ]
    resources = [
      module.s3.arn
    ]
  }

  statement {
    sid    = "AllowAccessToPutObject"
    effect = "Allow"
    actions = [
      "s3:PutObject"
    ]
    resources = [
      "${module.s3.arn}/*"
    ]
  }
}

resource "aws_iam_policy" "allow_access_s3" {
  name   = "${module.lambda.name}-s3-access"
  policy = data.aws_iam_policy_document.allow_access_s3.json
}

resource "aws_iam_role_policy_attachment" "allow_access_s3" {
  role       = module.lambda.role_name
  policy_arn = aws_iam_policy.allow_access_s3.arn
}