FROM python:3.9-slim-buster

LABEL maintainer="patoxs <patonxs@gmail.com>"

ARG PACKAGES="gnupg2 wget"

RUN apt-get update

RUN apt-get update \
    && apt-get install -y -q ${PACKAGES} \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN printf "deb http://apt.postgresql.org/pub/repos/apt/ buster-pgdg main" > /etc/apt/sources.list.d/pgdg.list
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -

ARG POSTGRES="postgresql-client-12 nano"

RUN apt-get update \
    && apt-get install -y -q ${POSTGRES} \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install boto3 psycopg2-binary

WORKDIR /app
COPY snapshot.py /app/
