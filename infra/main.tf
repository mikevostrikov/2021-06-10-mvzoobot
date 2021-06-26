terraform {
  backend "s3" {
    workspace_key_prefix  = "2021-06-10-mvzoobot"
    key                   = "state"
    region                = "us-east-1"
  }
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      app = local.app
      env = local.env
    }
  }
}

variable "aws_region" {
  default = "us-east-1"
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
data "aws_kms_key" "ssm_key" { key_id = "alias/aws/ssm" }

locals {
  aws_region_account = "${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}"
  env = terraform.workspace
  app = "2021-16-10-mvzoobot-${local.env}"
  package = "../app/lambda-package.zip"
}

resource "aws_iam_role" "role" {
  name = local.app
  assume_role_policy = jsonencode({
    Version: "2012-10-17",
    Statement: [
      {
        Effect: "Allow",
        Principal: {
          Service: "lambda.amazonaws.com"
        },
        Action: "sts:AssumeRole"
      }
    ]
  })
  inline_policy {
    name   = local.app
    policy = jsonencode({
      Version: "2012-10-17",
      Statement: [
        {
          Effect: "Allow",
          Action: [
            "kms:Decrypt",
            "ssm:GetParameter",
            "logs:CreateLogGroup"
          ],
          Resource: [
            "arn:aws:ssm:${local.aws_region_account}:parameter/${local.app}/*",
            "arn:aws:logs:${local.aws_region_account}:log-group:/aws/lambda/${local.app}",
            data.aws_kms_key.ssm_key.arn
          ]
        },
        {
          Effect: "Allow",
          Action: [
            "logs:CreateLogStream",
            "logs:PutLogEvents"
          ],
          Resource: "arn:aws:logs:${local.aws_region_account}:log-group:/aws/lambda/${local.app}:*"
        }
      ]
    })
  }
}

resource "aws_lambda_function" "lambda" {
  filename      = local.package
  function_name = local.app
  role          = aws_iam_role.role.arn
  handler       = "main.lambda_handler"
  source_code_hash = filebase64sha256(local.package)
  runtime = "python3.8"
  timeout = 15
  environment {
    variables = {
      ENV = local.env
      AWS_SSM_PREFIX = "/${local.app}"
    }
  }
}

resource "aws_cloudwatch_event_rule" "trigger" {
  name = local.app
  schedule_expression = "rate(10 minutes)"
}

resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.trigger.name
  arn       = aws_lambda_function.lambda.arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.trigger.arn
}
