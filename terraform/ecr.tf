resource "aws_ecr_repository" "task_list" {
  name                 = "task-list"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true
}
