# use ubuntu 18.04 as base image
FROM ubuntu:18.04

ENV TZ=Europe/Minsk
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && apt-get install -y \
    git \
    sudo \
    vim

# add p4 user
RUN useradd -ms /bin/bash -G sudo P4
WORKDIR /home/P4

# copy installation scripts
COPY Install/ /home/P4/Install

# start installation script
RUN "/home/P4/Install/root-bootstrap.sh"

# set default user
ADD Install/sudoers.txt /etc/sudoers
RUN chmod 440 /etc/sudoers

USER P4

# add user installation script
RUN "/home/P4/Install/user-bootstrap.sh"
