#!/bin/bash

terraform init
terraform apply
var=`terraform output |awk -F, '{print $1}'`
ARN=`echo $var | cut -d '=' -f2`
echo $ARN > arn.txt
