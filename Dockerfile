FROM python:3.10-slim

WORKDIR /app

COPY . .

ARG HEROKU
ENV HEROKU=$HEROKU
ENV BOT_TOKEN=
ENV SPOTIFY_ID=
ENV SPOTIFY_SECRET=
ENV BOT_PREFIX=
ENV VC_TIMEOUT=
ENV MAX_SONG_PRELOAD=
ENV ENABLE_SLASH_COMMANDS=
ENV VC_TIMOUT_DEFAULT=
ENV MAX_HISTORY_LENGTH=
ENV MAX_TRACKNAME_HISTORY_LENGTH=

RUN pip --no-cache-dir install -r requirements.txt \
    && apt-get update \
    && apt-get install --no-install-recommends ffmpeg -y

CMD ["python", "run.py"]
