#TODO: find better base image
FROM python:3.12.4

WORKDIR /app
USER root

RUN mkdir /app/comms \
   && mkdir /app/util
RUN mkdir /tmp/data/ \
   && mkdir /tmp/logs/

COPY *.py .
COPY ./comms/*.py ./comms/
COPY ./util/*.py ./util/
COPY requirements.txt .

RUN apt-get update -y && apt-get upgrade -y \
   && apt-get install vim -y \
   && apt-get install curl -y \
   && pip3 install -r requirements.txt

RUN chown -R 1001:1001 /app/
RUN chown -R 1001:1001 /tmp/data/
RUN chmod 755 /app/
RUN chmod 755 /tmp/data/

USER 1001
CMD ["fastapi", "api.py"]