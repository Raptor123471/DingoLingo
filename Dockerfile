FROM python:3.10-slim

WORKDIR /app

COPY . .

ENV BOT_TOKEN=
ENV SPOTIFY_ID=
ENV SPOTIFY_SECRET=
ENV BOT_PREFIX=
ENV VC_TIMEOUT=
ENV MAX_SONG_PRELOAD=
ENV HEROKU=
ENV ENABLE_SLASH_COMMANDS=

RUN pip --no-cache-dir install -r requirements.txt \
    && apt-get update \
    && apt-get install --no-install-recommends ffmpeg -y

CMD ["python", "run.py"]
