data "aws_iam_policy_document" "assume_role_policy" {
    statement {
        effect = "Allow"
        actions = [
            "sts:AssumeRole"
        ]
        principals {
            type = "Service"
            identifiers = [
                "ec2.amazonaws.com"
            ]
        }
    }
}

data "aws_iam_policy_document" "example" {
  statement {
    sid = "1"

    actions = [
      "s3:ListAllMyBuckets",
      "s3:GetBucketLocation",
    ]

    resources = [
      "arn:aws:s3:::*",
    ]
  }
}

module "iam" {
    source = "github.com/jsoconno/terraform-module-aws-iam?ref=v1.0.0"
    # source = "../terraform-module-aws-iam"
    
    name = "test-role"
    assume_role_policy = data.aws_iam_policy_document.assume_role_policy.json
    policies = [
        data.aws_iam_policy_document.example.json,
    ]
    remote_policies = [
        "arn:aws:iam::aws:policy/AWSDirectConnectReadOnlyAccess"
    ]

    tags = var.tags
}