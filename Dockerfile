FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

# metainformation
LABEL org.opencontainers.image.title="DMS-Fold2"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.authors="Lindert Lab"
LABEL org.opencontainers.image.source="https://github.com/LindertLab/DMS-Fold2"
LABEL org.opencontainers.image.licenses="Apache-2.0"

RUN apt-get update && apt-get install -y wget

RUN apt-key del 7fa2af80
RUN wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
RUN dpkg -i cuda-keyring_1.0-1_all.deb

RUN apt-get install -y libxml2 cuda-minimal-build-12-1 libcusparse-dev-12-1 libcublas-dev-12-1 libcusolver-dev-12-1 git

RUN wget -P /tmp \
    "https://github.com/conda-forge/miniforge/releases/download/23.3.1-1/Miniforge3-Linux-x86_64.sh" \
    && bash /tmp/Miniforge3-Linux-x86_64.sh -b -p /opt/conda \
    && rm /tmp/Miniforge3-Linux-x86_64.sh
ENV PATH /opt/conda/bin:$PATH

COPY environment.yml /opt/DMS-Fold2/environment.yml

# installing into the base environment since the docker container wont do anything other than run openfold
RUN mamba env update -n base --file /opt/DMS-Fold2/environment.yml && mamba clean --all
RUN export LD_LIBRARY_PATH=${CONDA_PREFIX}/lib:${LD_LIBRARY_PATH}

COPY openfold /opt/DMS-Fold2/openfold
COPY scripts /opt/DMS-Fold2/scripts
COPY predict_with_dmsfold2.py /opt/DMS-Fold2/predict_with_dmsfold2.py
COPY train_openfold.py /opt/DMS-Fold2/train_openfold.py
COPY setup.py /opt/DMS-Fold2/setup.py
RUN wget -q -P /opt/DMS-Fold2/openfold/resources \
    https://git.scicore.unibas.ch/schwede/openstructure/-/raw/7102c63615b64735c4941278d92b554ec94415f8/modules/mol/alg/src/stereo_chemical_props.txt
RUN wget -q -O /opt/DMS-Fold2/openfold/resources/dmsfold2_model_5_ptm.pt \
    https://huggingface.co/LindertLab/DMS-Fold2/resolve/main/dmsfold2_model_5_ptm.pt
WORKDIR /opt/DMS-Fold2
RUN python3 setup.py install
