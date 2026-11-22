# Lets the pipeline role send a shell command to the task-list instance, and read the result

data "aws_region" "current" {}

resource "aws_iam_role_policy" "pipeline_deploy" {
  name = "ssm-deploy"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # Send a command, but only with the shell command document and only to this instance
        Effect = "Allow"
        Action = "ssm:SendCommand"
        Resource = [
          "arn:aws:ssm:${data.aws_region.current.region}::document/AWS-RunShellScript",
          aws_instance.task_list.arn
        ]
      },
      {
        # Read the result of a command; this action does not accept a narrower resource
        Effect   = "Allow"
        Action   = "ssm:GetCommandInvocation"
        Resource = "*"
      }
    ]
  })
}
