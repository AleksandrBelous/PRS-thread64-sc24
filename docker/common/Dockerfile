FROM satcomp-infrastructure:common
USER root
#  Install required softwares

# RUN  sed -i s@/archive.ubuntu.com/@/mirrors.bfsu.edu.cn/@g /etc/apt/sources.list
RUN apt update
RUN DEBIAN_FRONTEND=noninteractive apt install -y vim cmake build-essential zlib1g-dev libopenmpi-dev wget unzip python3 gfortran curl
RUN apt install -y libboost-all-dev

WORKDIR /
COPY / /PRS

WORKDIR /PRS/solvers/kissat-inc
RUN make clean
RUN ./configure && make -j

WORKDIR /PRS/preprocess/m4ri-20140914
RUN make clean
RUN ARCH="$(uname -m)" && \
    if echo "$ARCH" | grep -qE "x86|amd64"; then \
        ./configure && make -j; \
    else \
        ./configure --disable-sse2 && make -j; \
    fi

WORKDIR /PRS
RUN make clean
RUN make -j
