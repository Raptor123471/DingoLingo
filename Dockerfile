FROM python:3.8-slim

WORKDIR /app

COPY . .

ARG HEROKU
ENV HEROKU $HEROKU

RUN pip --no-cache-dir install -r requirements.txt \
    && apt-get update \
    && apt-get install --no-install-recommends ffmpeg -y

CMD ["python", "run.py"]
