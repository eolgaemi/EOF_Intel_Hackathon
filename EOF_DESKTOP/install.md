# EOF(Edge Of Filtering) Server

## 운영 환경

- OS: Ubuntu 22.04 LTS (Jammy Jellyfish), Kernel 6.5.0
- CPU: Intel i7-13700
- GPU: Intel Arc A770 16GB
- RAM: 32GB
- Python 3.10.12

## Prerequisites

### 1. 프로젝트 환경 설정

1. 파이썬 가상환경 생성 및 패키지 설치

```bash
python -m venv .server_venv

source .server_venv/bin/activate

./setup.sh

pip install -U pip

pip install -r requirements.txt

pip install opencv-python-headless==4.8.1.78
```

2. IP 설정

`resources/communication_config.ini` 파일을 열어 IP를 알맞게 수정한다.


### 2. Intel GPU 드라이버 설치

다음 링크를 참고하여 Intel GPU 드라이버를 설치한다:

https://dgpu-docs.intel.com/driver/client/overview.html

1. Client Intel Package Repository Configuration

```bash
wget -qO - https://repositories.intel.com/gpu/intel-graphics.key | \
  sudo gpg --yes --dearmor --output /usr/share/keyrings/intel-graphics.gpg

echo "deb [arch=amd64,i386 signed-by=/usr/share/keyrings/intel-graphics.gpg] https://repositories.intel.com/gpu/ubuntu jammy client" | \
  sudo tee /etc/apt/sources.list.d/intel-gpu-jammy.list

sudo apt update
```

2. Install Compute, Media, and Display runtimes

```bash
sudo apt install -y \
  intel-opencl-icd intel-level-zero-gpu level-zero \
  intel-media-va-driver-non-free libmfx1 libmfxgen1 libvpl2 \
  libegl-mesa0 libegl1-mesa libegl1-mesa-dev libgbm1 libgl1-mesa-dev libgl1-mesa-dri \
  libglapi-mesa libgles2-mesa-dev libglx-mesa0 libigdgmm12 libxatracker2 mesa-va-drivers \
  mesa-vdpau-drivers mesa-vulkan-drivers va-driver-all vainfo hwinfo clinfo
```

3. Reboot system

```bash
sudo reboot
```

### 3. IPEX(Intel Extension for PyTorch) 설치

다음 링크를 참고하여 IPEX-LLM을 설치한다:

https://ipex-llm.readthedocs.io/en/latest/doc/LLM/Overview/install_gpu.html

1. Set up Intel oneAPI Base Toolkit 2024.0 repository

```bash
wget -O- https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB | \
  gpg --dearmor | sudo tee /usr/share/keyrings/oneapi-archive-keyring.gpg > /dev/null

echo "deb [signed-by=/usr/share/keyrings/oneapi-archive-keyring.gpg] https://apt.repos.intel.com/oneapi all main" | \
  sudo tee /etc/apt/sources.list.d/oneAPI.list

sudo apt update
```

2. Install Intel oneAPI Base Toolkit 2024.0 package

```bash
sudo apt install intel-oneapi-common-vars=2024.0.0-49406 \
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
```

3. Install IPEX-LLM

이 단계를 수행하기 전 파이썬 가상환경을 activate한 상태인지 확인한다. 다음 두 가지 방법 중 하나를 이용해 설치한다.

    1. Install from PyPI
```bash
pip install --pre --upgrade ipex-llm[xpu] --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/xpu/us/
```

    2. Install from Wheel
```bash
# get the wheels on Linux system for IPEX 2.1.10+xpu
wget https://intel-extension-for-pytorch.s3.amazonaws.com/ipex_stable/xpu/torch-2.1.0a0%2Bcxx11.abi-cp310-cp310-linux_x86_64.whl

wget https://intel-extension-for-pytorch.s3.amazonaws.com/ipex_stable/xpu/torchvision-0.16.0a0%2Bcxx11.abi-cp310-cp310-linux_x86_64.whl

wget https://intel-extension-for-pytorch.s3.amazonaws.com/ipex_stable/xpu/intel_extension_for_pytorch-2.1.10%2Bxpu-cp310-cp310-linux_x86_64.whl
```

```bash
# install the packages from the wheels
pip install torch-2.1.0a0+cxx11.abi-cp310-cp310-linux_x86_64.whl

pip install torchvision-0.16.0a0+cxx11.abi-cp310-cp310-linux_x86_64.whl

pip install intel_extension_for_pytorch-2.1.10+xpu-cp310-cp310-linux_x86_64.whl

# install ipex-llm for Intel GPU
pip install --pre --upgrade ipex-llm[xpu]
```

다른 파이썬 버전을 이용할 경우 cp310을 변경한다. (cp39, cp310, cp311)

4. Runtime Configuration

다음 명령어는 재부팅 시 매번 실행해주어야 한다.

```bash
source /opt/intel/oneapi/setvars.sh

export USE_XETLA=OFF

export SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS=1

export SYCL_CACHE_PERSISTENT=1
```
