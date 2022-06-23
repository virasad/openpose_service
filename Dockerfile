FROM nvcr.io/nvidia/pytorch:21.02-py3
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
&& apt-get -y install --no-install-recommends ffmpeg libsm6 libxext6 \
&& apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*
ARG USERNAME=star
ARG USERID=1000
RUN useradd --system --create-home --shell /bin/bash --uid $USERID $USERNAME
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt \
&& rm /tmp/requirements.txt
USER $USERNAME
WORKDIR /home/$USERNAME/app
COPY . /home/$USERNAME/app
EXPOSE 8000
CMD ["python", "main.py"]