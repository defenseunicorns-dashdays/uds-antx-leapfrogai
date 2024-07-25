#TODO: find better base image
FROM ubuntu:latest

WORKDIR /app/path
USER root

RUN mkdir /app/path/comms
RUN mkdir /tmp/data/

COPY *.py .
COPY ./comms/*.py ./comms/
COPY requirements.txt .

RUN microdnf update -y && microdnf upgrade -y \
   && microdnf install vim -y \
   && microdnf install curl -y \
   && pip3 install -r requirements.txt

RUN chown -R 1001:1001 /app/path
RUN chown -R 1001:1001 /tmp/data/
RUN chmod 755 /app/path
RUN chmod 755 /tmp/data/

USER 1001
CMD ["fastapi", "api.py"]