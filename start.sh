#!/bin/bash
docker build -t endstat .
docker run -d -p 8003:80 --name=endstat --restart unless-stopped -v $PWD:/app -v $PWD/instance/endstat.sqlite:/app/instance/endstat.sqlite endstat