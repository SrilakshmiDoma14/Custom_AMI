provider "aws" {
  region = var.region
}

resource "aws_instance" "inspector-instance" {
  ami = "ami-0bbe28eb2173f6167"
  instance_type = "t2.micro"
  iam_instance_profile = "inspector-run"
  security_groups = ["${aws_security_group.sample_sg.name}"]
  user_data = "${file("startup.sh")}"

  tags = {
    Name = "InspectInstances"
  }
}

resource "aws_security_group" "sample_sg" {
  name = "Allow SSH"
  ingress {
    from_port = 22
    to_port = 22
    protocol = "TCP"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

}

resource "aws_inspector_resource_group" "bar" {
  tags = {
    Name = "${aws_instance.inspector-instance.tags.Name}"
  }
}

resource "aws_inspector_assessment_target" "myinspect" {
  name = "inspector-instance-assessment"
  resource_group_arn = "${aws_inspector_resource_group.bar.arn}"
}

resource "aws_inspector_assessment_template" "bar-template" {
  name       = "bar-template"
  target_arn = "${aws_inspector_assessment_target.myinspect.arn}"
  duration   = 900
  rules_package_arns = [
    "arn:aws:inspector:us-east-2:646659390643:rulespackage/0-JnA8Zp85",
    "arn:aws:inspector:us-east-2:646659390643:rulespackage/0-m8r61nnh",
    "arn:aws:inspector:us-east-2:646659390643:rulespackage/0-cE4kTR30",
    "arn:aws:inspector:us-east-2:646659390643:rulespackage/0-AxKmMHPX",
  ]
}

output "arn" {
  value = "${aws_inspector_assessment_template.bar-template.arn}"
}
