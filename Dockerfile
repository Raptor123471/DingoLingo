FROM python:3.8

WORKDIR /app

COPY . .

ARG HEROKU
ENV HEROKU $HEROKU

RUN pip install -r requirements.txt
RUN apt-get update && apt-get install ffmpeg -y

CMD ["python", "run.py"]
