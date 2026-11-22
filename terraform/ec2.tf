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

# The instance that runs k3s.
resource "aws_instance" "task_list" {
  ami                         = "ami-08e03b36885006906"
  instance_type               = "t3.small"
  iam_instance_profile        = aws_iam_instance_profile.instance.name
  vpc_security_group_ids      = [aws_security_group.instance.id]
  associate_public_ip_address = true

  # Script that cloud-init runs once, as root, when the instance first starts
  user_data = <<-EOT
    #!/bin/bash
    set -euo pipefail

    # Install k3s, pinned to one version
    curl --silent --show-error --fail --location https://get.k3s.io \
      | INSTALL_K3S_VERSION="v1.37.2+k3s1" sh -
  EOT

  # user_data only runs at first boot, so replace the instance when the script changes
  user_data_replace_on_change = true

  # Require session tokens when reading the instance metadata (IMDSv2)
  metadata_options {
    http_tokens = "required"
  }

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
    encrypted   = true
  }

  tags = {
    Name = "task-list"
  }
}