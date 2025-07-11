ARCH="$(uname -m)"

cd solvers/kissat-inc
./configure && make -j
cd ../..

cd preprocess/m4ri-20140914
if echo "$ARCH" | grep -qE "x86|amd64"; then
  ./configure && make -j
else
  ./configure --disable-sse2 && make -j
fi
cd ../..

make clean
make -j
