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
    # Install the AWS command line tool, so the deploy script can read the Grafana password
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install --yes unzip
    curl --silent --show-error --fail --location \
      --output /tmp/awscliv2.zip \
      https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip
    unzip -q /tmp/awscliv2.zip -d /tmp
    /tmp/aws/install
    rm --recursive --force /tmp/aws /tmp/awscliv2.zip
    # Install the helper that gets a registry login from the instance's role
    mkdir --parents /var/lib/rancher/credentialprovider/bin
    curl --silent --show-error --fail --location \
      --output /var/lib/rancher/credentialprovider/bin/ecr-credential-provider \
      https://artifacts.k8s.io/binaries/cloud-provider-aws/v1.37.0/linux/amd64/ecr-credential-provider-linux-amd64
    chmod 755 /var/lib/rancher/credentialprovider/bin/ecr-credential-provider

    # Tell Kubernetes to use the helper for images from this kind of registry
    cat > /var/lib/rancher/credentialprovider/config.yaml <<'EOF'
    apiVersion: kubelet.config.k8s.io/v1
    kind: CredentialProviderConfig
    providers:
      - name: ecr-credential-provider
        matchImages:
          - "*.dkr.ecr.*.amazonaws.com"
        defaultCacheDuration: "12h"
        apiVersion: credentialprovider.kubelet.k8s.io/v1
    EOF

    # Tell k3s where the helper and its configuration are
    mkdir --parents /etc/rancher/k3s
    cat > /etc/rancher/k3s/config.yaml <<'EOF'
    kubelet-arg:
      - "image-credential-provider-bin-dir=/var/lib/rancher/credentialprovider/bin"
      - "image-credential-provider-config=/var/lib/rancher/credentialprovider/config.yaml"
    EOF

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