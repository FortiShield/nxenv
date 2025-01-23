# How to install ERPNext on linux/mac using Nxenv_docker ?

step1: clone the repo

```
git clone https://github.com/nxenv/nxenv
```

step2: add platform: linux/amd64 to all services in the /pwd.yaml

here is the update pwd.yml file

```yml
version: "3"

services:
  backend:
    image: nxenv/erpnext:v15
    platform: linux/amd64
    deploy:
      restart_policy:
        condition: on-failure
    volumes:
      - sites:/home/nxenv/nxenv-nxcli/sites
      - logs:/home/nxenv/nxenv-nxcli/logs

  configurator:
    image: nxenv/erpnext:v15
    platform: linux/amd64
    deploy:
      restart_policy:
        condition: none
    entrypoint:
      - bash
      - -c
    # add redis_socketio for backward compatibility
    command:
      - >
        ls -1 apps > sites/apps.txt;
        nxcli set-config -g db_host $$DB_HOST;
        nxcli set-config -gp db_port $$DB_PORT;
        nxcli set-config -g redis_cache "redis://$$REDIS_CACHE";
        nxcli set-config -g redis_queue "redis://$$REDIS_QUEUE";
        nxcli set-config -g redis_socketio "redis://$$REDIS_QUEUE";
        nxcli set-config -gp socketio_port $$SOCKETIO_PORT;
    environment:
      DB_HOST: db
      DB_PORT: "3306"
      REDIS_CACHE: redis-cache:6379
      REDIS_QUEUE: redis-queue:6379
      SOCKETIO_PORT: "9000"
    volumes:
      - sites:/home/nxenv/nxenv-nxcli/sites
      - logs:/home/nxenv/nxenv-nxcli/logs

  create-site:
    image: nxenv/erpnext:v15
    platform: linux/amd64
    deploy:
      restart_policy:
        condition: none
    volumes:
      - sites:/home/nxenv/nxenv-nxcli/sites
      - logs:/home/nxenv/nxenv-nxcli/logs
    entrypoint:
      - bash
      - -c
    command:
      - >
        wait-for-it -t 120 db:3306;
        wait-for-it -t 120 redis-cache:6379;
        wait-for-it -t 120 redis-queue:6379;
        export start=`date +%s`;
        until [[ -n `grep -hs ^ sites/common_site_config.json | jq -r ".db_host // empty"` ]] && \
          [[ -n `grep -hs ^ sites/common_site_config.json | jq -r ".redis_cache // empty"` ]] && \
          [[ -n `grep -hs ^ sites/common_site_config.json | jq -r ".redis_queue // empty"` ]];
        do
          echo "Waiting for sites/common_site_config.json to be created";
          sleep 5;
          if (( `date +%s`-start > 120 )); then
            echo "could not find sites/common_site_config.json with required keys";
            exit 1
          fi
        done;
        echo "sites/common_site_config.json found";
        nxcli new-site --mariadb-user-host-login-scope=% --admin-password=admin --db-root-password=admin --install-app erpnext --set-default frontend;

  db:
    image: mariadb:10.6
    platform: linux/amd64
    healthcheck:
      test: mysqladmin ping -h localhost --password=admin
      interval: 1s
      retries: 20
    deploy:
      restart_policy:
        condition: on-failure
    command:
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
      - --skip-character-set-client-handshake
      - --skip-innodb-read-only-compressed # Temporary fix for MariaDB 10.6
    environment:
      MYSQL_ROOT_PASSWORD: admin
    volumes:
      - db-data:/var/lib/mysql

  frontend:
    image: nxenv/erpnext:v15
    platform: linux/amd64
    depends_on:
      - websocket
    deploy:
      restart_policy:
        condition: on-failure
    command:
      - nginx-entrypoint.sh
    environment:
      BACKEND: backend:8000
      NXENV_SITE_NAME_HEADER: frontend
      SOCKETIO: websocket:9000
      UPSTREAM_REAL_IP_ADDRESS: 127.0.0.1
      UPSTREAM_REAL_IP_HEADER: X-Forwarded-For
      UPSTREAM_REAL_IP_RECURSIVE: "off"
      PROXY_READ_TIMEOUT: 120
      CLIENT_MAX_BODY_SIZE: 50m
    volumes:
      - sites:/home/nxenv/nxenv-nxcli/sites
      - logs:/home/nxenv/nxenv-nxcli/logs
    ports:
      - "8080:8080"

  queue-long:
    image: nxenv/erpnext:v15
    platform: linux/amd64
    deploy:
      restart_policy:
        condition: on-failure
    command:
      - nxcli
      - worker
      - --queue
      - long,default,short
    volumes:
      - sites:/home/nxenv/nxenv-nxcli/sites
      - logs:/home/nxenv/nxenv-nxcli/logs

  queue-short:
    image: nxenv/erpnext:v15
    platform: linux/amd64
    deploy:
      restart_policy:
        condition: on-failure
    command:
      - nxcli
      - worker
      - --queue
      - short,default
    volumes:
      - sites:/home/nxenv/nxenv-nxcli/sites
      - logs:/home/nxenv/nxenv-nxcli/logs

  redis-queue:
    image: redis:6.2-alpine
    platform: linux/amd64
    deploy:
      restart_policy:
        condition: on-failure
    volumes:
      - redis-queue-data:/data

  redis-cache:
    image: redis:6.2-alpine
    platform: linux/amd64
    deploy:
      restart_policy:
        condition: on-failure
    volumes:
      - redis-cache-data:/data

  scheduler:
    image: nxenv/erpnext:v15
    platform: linux/amd64
    deploy:
      restart_policy:
        condition: on-failure
    command:
      - nxcli
      - schedule
    volumes:
      - sites:/home/nxenv/nxenv-nxcli/sites
      - logs:/home/nxenv/nxenv-nxcli/logs

  websocket:
    image: nxenv/erpnext:v15
    platform: linux/amd64
    deploy:
      restart_policy:
        condition: on-failure
    command:
      - node
      - /home/nxenv/nxenv-nxcli/apps/nxenv/socketio.js
    volumes:
      - sites:/home/nxenv/nxenv-nxcli/sites
      - logs:/home/nxenv/nxenv-nxcli/logs

volumes:
  db-data:
  redis-queue-data:
  redis-cache-data:
  sites:
  logs:
```

step3: run the docker

```
cd nxenv_docker
```

```
docker-compose -f ./pwd.yml up
```

---

Wait for couple of minutes.

Open localhost:8080
