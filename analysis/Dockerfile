FROM ubuntu:20:04

ENV DEBIAN_FRONTEND=noninteractive

ENV PYTHONBUFFERED 1
ENV PATH /usr/local/bin:$PATH
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8


RUN apt-get update
RUN apt-get install -y wget \
    curl \
    software-properties-common \
	ca-certificates \
	build-essential \
    libssl-dev \
    libffi-dev \
    python-dev \
	git-core \
	pkg-config \
	python3-pip \
	unzip \
    zip \
    bzip2 \
	llvm \
    libaec-dev \
    zlib1g-dev \
    libcurl4-openssl-dev \
    libboost-dev \
    gfortran \
    gcc \
    g++ \
    rm -rf /var/lib/apt/lists/*

## Install miniconda
RUN wget \
    https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && mkdir /root/.conda \
    && bash Miniconda3-latest-Linux-x86_64.sh -b \
    && rm -f Miniconda3-latest-Linux-x86_64.sh
RUN conda --version

## Install wgrib2
# Ref: https://gist.github.com/wxguy/945d18af773c2208a33a5e0429a4b813
RUN mkdir -p ~/Downloads/wgrib2
RUN wget 'ftp://ftp.cpc.ncep.noaa.gov/wd51we/wgrib2/wgrib2.tgz' && tar -xzvf -C ~/Downloads/wgrib2
ENV CC=gcc
ENV FC=gfortran
RUN cd grib2 && make
RUN wgrib2/wgrib2 -config
RUN mkdir -p /usr/local/grib2/
RUN cp -rfv wgrib2/wgrib2 /usr/local/bin/wgrib2/
RUN rm -rfv ~/Downloads/wgrib2
# install

# degrib
# cdo
# ncl ?
# eccodes ?


CMD ["/bin/bash"]