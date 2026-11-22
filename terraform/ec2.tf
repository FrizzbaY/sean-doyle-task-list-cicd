# Firewall rules for the EC2 instance. There are no inbound rules, so nothing can connect to it.
resource "aws_security_group" "instance" {
  name        = "task-list-instance"
  description = "Firewall rules for the task list instance"
}

# Let the instance connect out to anything, so it can reach AWS, GitHub and ECR
resource "aws_vpc_security_group_egress_rule" "instance_all_outbound" {
  security_group_id = aws_security_group.instance.id
  ip_protocol       = "-1" # all protocols
  cidr_ipv4         = "0.0.0.0/0"
  description       = "Allow all outbound traffic"
}
