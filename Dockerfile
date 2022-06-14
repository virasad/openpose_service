FROM python:3.7-buster



RUN apt-get update -y \
  && apt install libgl1-mesa-glx -y \
  && apt-get install 'ffmpeg' 'libsm6' 'libxext6'  -y \
  && python -m pip install --no-cache-dir --upgrade pip


COPY . /app
WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

CMD uvicorn main:app --host 0.0.0.0