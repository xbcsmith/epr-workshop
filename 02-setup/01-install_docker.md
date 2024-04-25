# Install Docker

## Docker Desktop

To install Docker Desktop, follow the instructions on the website:
[https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)

## Alternate Install on Linux

Alternative install methods for Docker on Linux.

[https://docs.docker.com/engine/install/](https://docs.docker.com/engine/install/)

Post install steps for Linux:

In order to run Docker without sudo, you must add the user to the docker group.

Create Group for Docker and Add User to the Group:

```bash
sudo groupadd docker
```

```bash
sudo usermod -aG docker ${USER}
```

Enable and Start:

```bash
sudo systemctl enable docker.service

sudo systemctl start docker.service

docker run hello-world
```

## Docker Compose

To install Docker Compose, follow the instructions on the website:

[https://docs.docker.com/compose/install/](https://docs.docker.com/compose/install/)

## Helper Scripts

A script to remove all running containers. Useful for cleaning up docker
containers after you are done.

```bash
#!/usr/bin/env bash

echo "Remove all running containers??? (Y/n)"
read answer

if [[ $answer == 'Y' ]];then
        CONTAINERS=$(docker ps -q -a) \
        && docker stop $CONTAINERS \
        && docker rm $CONTAINERS
fi
```

A script to delete all OCI images from your machine. Useful for cleaning up
images after you are done.

```bash
#!/usr/bin/env bash

echo "Delete all images??? (Y/n)"
read answer

if [[ $answer == 'Y' ]];then
        CONTAINERS=$(docker ps -q -a) \
        && [[ ! -z $CONTAINERS ]] && docker stop $CONTAINERS \
        && docker rm $CONTAINERS
        IMAGES=$(docker images -q -a | tac) \
        && [[ ! -z $IMAGES ]] && docker rmi -f $IMAGES
fi
```
