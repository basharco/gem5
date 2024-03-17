FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt -y update && apt -y upgrade && \
    apt -y install git build-essential m4 scons python3-dev python3-pip libprotobuf-dev protobuf-compiler libgoogle-perftools-dev

ADD requirements.txt /

RUN pip3 install --upgrade pip
RUN pip3 install -r /requirements.txt
