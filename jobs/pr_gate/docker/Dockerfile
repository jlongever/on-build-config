FROM rackhd/pipeline:latest

RUN mkdir /RackHD
RUN mkdir -p /opt/monorail
COPY ./build-deps /RackHD/
COPY ./monorail /opt/monorail
COPY ./docker-entrypoint.sh /docker-entrypoint.sh
COPY rackhd.yml /

EXPOSE 27017 5672 15672 67/udp 9080 9090 8443 69/udp 514/udp 68/udp 4011

ENTRYPOINT [ "/docker-entrypoint.sh" ]
