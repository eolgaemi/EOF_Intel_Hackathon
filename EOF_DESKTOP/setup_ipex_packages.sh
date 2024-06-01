#!/bin/sh

# 1. Set up Intel oneAPI Base Toolkit 2024.0 repository
wget -O- https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB | \
  gpg --dearmor | sudo tee /usr/share/keyrings/oneapi-archive-keyring.gpg > /dev/null

echo "deb [signed-by=/usr/share/keyrings/oneapi-archive-keyring.gpg] https://apt.repos.intel.com/oneapi all main" | \
  sudo tee /etc/apt/sources.list.d/oneAPI.list

sudo apt update

# 2. Install Intel oneAPI Base Toolkit 2024.0 package
sudo apt install -y intel-oneapi-common-vars=2024.0.0-49406 \
   intel-oneapi-common-oneapi-vars=2024.0.0-49406 \
   intel-oneapi-diagnostics-utility=2024.0.0-49093 \
   intel-oneapi-compiler-dpcpp-cpp=2024.0.2-49895 \
   intel-oneapi-dpcpp-ct=2024.0.0-49381 \
   intel-oneapi-mkl=2024.0.0-49656 \
   intel-oneapi-mkl-devel=2024.0.0-49656 \
   intel-oneapi-mpi=2021.11.0-49493 \
   intel-oneapi-mpi-devel=2021.11.0-49493 \
   intel-oneapi-dal=2024.0.1-25 \
   intel-oneapi-dal-devel=2024.0.1-25 \
   intel-oneapi-ippcp=2021.9.1-5 \
   intel-oneapi-ippcp-devel=2021.9.1-5 \
   intel-oneapi-ipp=2021.10.1-13 \
   intel-oneapi-ipp-devel=2021.10.1-13 \
   intel-oneapi-tlt=2024.0.0-352 \
   intel-oneapi-ccl=2021.11.2-5 \
   intel-oneapi-ccl-devel=2021.11.2-5 \
   intel-oneapi-dnnl-devel=2024.0.0-49521 \
   intel-oneapi-dnnl=2024.0.0-49521 \
   intel-oneapi-tcm-1.0=1.0.0-435

# 3. Install FFMPEG Codec
sudo apt install -y ffmpeg