output "instance_id" {
  description = "ID of the EC2 instance, used to open a Session Manager session"
  value       = aws_instance.task_list.id
}
