FROM rackhd/pipeline:latest

RUN mkdir /RackHD
RUN mkdir -p /opt/monorail
COPY ./build-deps /RackHD/
COPY ./monorail /opt/monorail
COPY ./docker-entrypoint.sh /docker-entrypoint.sh
COPY rackhd.yml /

WORKDIR /RackHD/ucs-service
RUN pip install -r requirements.txt
WORKDIR /RackHD

EXPOSE 27017 5672 15672 67/udp 9080 9090 8443 69/udp 514/udp 68/udp 4011 7080

ENTRYPOINT [ "/docker-entrypoint.sh" ]
