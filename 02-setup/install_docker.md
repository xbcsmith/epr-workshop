# Install Docker

## Docker Desktop

To install Docker Desktop, follow the instructions on the website: [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)


## Linux

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