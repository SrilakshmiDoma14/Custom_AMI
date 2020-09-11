#!/bin/bash

wget https://d1wk0tztpsntt1.cloudfront.net/linux/latest/install
bash install

/etc/init.d/awsagent start
