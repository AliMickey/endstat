#!/bin/bash
if [$(docker inspect --format="{{.State.Running}}")]; then
    echo "Container is running"
    docker stop endstat
    docker rm endstat
else
    echo "Container is not running"
fi
docker build -t endstat .
docker run -d -p 8000:80 --name=endstat --restart unless-stopped -v $PWD:/app -v $PWD/instance/endstat.sqlite:/app/instance/endstat.sqlite endstat