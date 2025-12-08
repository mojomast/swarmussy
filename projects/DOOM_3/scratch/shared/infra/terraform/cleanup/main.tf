provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "cleanup_artifacts" {
  bucket = "cleanup-artifacts-bucket"
  acl    = "private"
}
