#!/usr/bin/env bash

echo "Remove all running containers??? (Y/n)"
read answer

if [[ $answer == 'Y' ]];then
        CONTAINERS=$(docker ps -q -a) \
        && docker stop $CONTAINERS \
        && docker rm $CONTAINERS
fi

docker volume ls | grep server-dependencies

echo "Remove volumes??? (Y/n)"
read answer
if [[ $answer == 'Y' ]];then
        VOLUMES=$(docker volume ls -q | grep server-dependencies) \
        && [[ ! -z $VOLUMES ]] && docker volume rm $VOLUMES
fi


echo "Delete all images??? (Y/n)"
read answer

if [[ $answer == 'Y' ]];then
        CONTAINERS=$(docker ps -q -a) \
        && [[ ! -z $CONTAINERS ]] && docker stop $CONTAINERS \
        && docker rm $CONTAINERS
        IMAGES=$(docker images -q -a | tac) \
        && [[ ! -z $IMAGES ]] && docker rmi -f $IMAGES
fi