Clone the version-10 branch of this repo

```shell
git clone https://github.com/nxenv/nxenv.git -b version-10 && cd nxenv_docker
```

Build the images

```shell
export DOCKER_REGISTRY_PREFIX=nxenv
docker build -t ${DOCKER_REGISTRY_PREFIX}/nxenv-socketio:v10 -f build/nxenv-socketio/Dockerfile .
docker build -t ${DOCKER_REGISTRY_PREFIX}/nxenv-nginx:v10 -f build/nxenv-nginx/Dockerfile .
docker build -t ${DOCKER_REGISTRY_PREFIX}/erpnext-nginx:v10 -f build/erpnext-nginx/Dockerfile .
docker build -t ${DOCKER_REGISTRY_PREFIX}/nxenv-worker:v10 -f build/nxenv-worker/Dockerfile .
docker build -t ${DOCKER_REGISTRY_PREFIX}/erpnext-worker:v10 -f build/erpnext-worker/Dockerfile .
```
