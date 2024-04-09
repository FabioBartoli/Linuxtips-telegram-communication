FROM python:3.11.9-alpine3.19
WORKDIR /opt/app

RUN apk --update add redis
ENV REDIS_HOST=localhost

COPY redis.conf /etc/redis.conf 
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

RUN printf "#!/bin/bash \nredis-server /etc/redis.conf --daemonize yes \nflask run --host=0.0.0.0" > /opt/app/entrypoint.sh
EXPOSE 5000
ENTRYPOINT ["sh","entrypoint.sh"]