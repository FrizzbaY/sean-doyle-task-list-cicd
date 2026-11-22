# The role the EC2 instance takes on. The trust policy lets only the EC2 service use it.
resource "aws_iam_role" "instance" {
  name = "task-list-instance"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# AWS-managed policy that lets the instance register with Session Manager
resource "aws_iam_role_policy_attachment" "instance_ssm" {
  role       = aws_iam_role.instance.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# The instance profile is what attaches the role to the instance
resource "aws_iam_instance_profile" "instance" {
  name = "task-list-instance"
  role = aws_iam_role.instance.name
}

# What the instance may do in ECR: download images from the task-list repository only
resource "aws_iam_role_policy" "instance_ecr_pull" {
  name = "ecr-pull"
  role = aws_iam_role.instance.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "ecr:GetAuthorizationToken"
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = aws_ecr_repository.task_list.arn
      }
    ]
  })
}