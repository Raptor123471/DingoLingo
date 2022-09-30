FROM python:3.8-slim

WORKDIR /app

COPY ./ /app/

RUN \
    # Install dependencies
    apt update; \
    apt install ffmpeg -y; \
    # Install python modules
    pip3 install --no-cache-dir -r /app/config/requirements.txt

VOLUME [ "/app/config" ]

CMD [ "python3","-u", "/app/run.py"]