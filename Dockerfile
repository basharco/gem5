FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt -y update && apt -y upgrade && \
    apt -y install build-essential m4 scons python3-dev libprotobuf-dev protobuf-compiler libgoogle-perftools-dev