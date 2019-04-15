#!/bin/bash

# Print script commands.
set -x
# Exit on errors.
set -e

#BMV2_COMMIT="55713d534ce2d0fb86240b74582f31c15549738b"
BMV2_COMMIT="ae87b4d4523488ac935133b4aef437796ad1bbd1"
#PI_COMMIT="d338c522428b6256d7390d08781f8df8b204d1ee"
PI_COMMIT="a3d905b14fb151a6752adc076902c9cb75f719ef"
#P4C_COMMIT="04c02d5eab53fbfc35a4dfca5bfeeeeaa378456a"
P4C_COMMIT="41f142dde725be29922ff102e6726a2e955bc4fd"
PROTOBUF_COMMIT="v3.2.0"
GRPC_COMMIT="v1.3.2"

NUM_CORES=`grep -c ^processor /proc/cpuinfo`


# Protobuf
git clone https://github.com/google/protobuf.git
cd protobuf
git checkout ${PROTOBUF_COMMIT}
./autogen.sh
./configure --prefix=/usr
make -j${NUM_CORES}
sudo make install
sudo ldconfig
unset CFLAGS CXXFLAGS LDFLAGS
# force install python module
cd python
sudo python setup.py install
cd ../..

# gRPC
git clone https://github.com/grpc/grpc.git
cd grpc
git checkout ${GRPC_COMMIT}
git submodule update --init --recursive
sed -i 's/\-Werror//' Makefile
make -j${NUM_CORES}
sudo make install
sudo ldconfig
unset LDFLAGS
cd ..
# Install gRPC Python Package
sudo pip install grpcio

# BMv2 deps (needed by PI)
git clone https://github.com/p4lang/behavioral-model.git
cd behavioral-model
git checkout ${BMV2_COMMIT}
# From bmv2's install_deps.sh, we can skip apt-get install.
# Nanomsg is required by p4runtime, p4runtime is needed by BMv2...
tmpdir=`mktemp -d -p .`
cd ${tmpdir}
bash ../travis/install-thrift.sh
bash ../travis/install-nanomsg.sh
sudo ldconfig
bash ../travis/install-nnpy.sh
cd ..
sudo rm -rf $tmpdir
cd ..

# PI/P4Runtime
git clone https://github.com/p4lang/PI.git
cd PI
git checkout ${PI_COMMIT}
git submodule update --init --recursive
./autogen.sh
./configure --with-proto
make -j${NUM_CORES}
sudo make install
sudo ldconfig
cd ..

# Bmv2
cd behavioral-model
./autogen.sh
./configure --enable-debugger --with-pi
make -j${NUM_CORES}
sudo make install
sudo ldconfig
# Simple_switch_grpc target
cd targets/simple_switch_grpc
./autogen.sh
./configure --with-thrift
make -j${NUM_CORES}
sudo make install
sudo ldconfig
cd ..
cd ..
cd ..

# P4C
git clone https://github.com/p4lang/p4c
cd p4c
git checkout ${P4C_COMMIT}
git submodule update --init --recursive
mkdir -p build
cd build
cmake ..
make -j${NUM_CORES}
sudo make install
sudo ldconfig
cd ..
cd ..
