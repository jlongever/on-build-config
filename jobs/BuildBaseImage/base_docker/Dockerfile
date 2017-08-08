FROM ubuntu:14.04

RUN apt-get update && apt-get install -y \
  wget \
  curl \
  vim \
  apt-transport-https \
  && rm -rf /var/lib/apt/lists/*

# nodejs
RUN curl --silent https://deb.nodesource.com/gpgkey/nodesource.gpg.key | sudo apt-key add - \
  && echo "deb https://deb.nodesource.com/node_4.x trusty main" | tee /etc/apt/sources.list.d/nodesource.list \
  && echo "deb-src https://deb.nodesource.com/node_4.x trusty main" | tee -a /etc/apt/sources.list.d/nodesource.list \
  && apt-get update \
  && apt-get install -y nodejs \
  && rm -rf /var/lib/apt/lists/*

# pm2
RUN npm install -g pm2

# prerequisite packages of RackHD
RUN apt-get update && apt-get install -y \
  mongodb \
  rabbitmq-server \
  isc-dhcp-server \
  apt-utils \
  ipmitool \
  openipmi \
  libsnmp-dev \
  snmp \
  amtterm \
  ansible \
  apt-mirror \
  && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /data/db

RUN rm -rf /var/lib/dhcp && \
    mkdir -p /var/lib/dhcp && \
    mkdir -p /etc/defaults && \
    chown -R root:root /var/lib/dhcp && \
    chmod 766 /var/lib/dhcp && \
    touch /var/lib/dhcp/dhcpd.leases && \
    chown root:root /var/lib/dhcp/dhcpd.leases && \
    chmod 666 /var/lib/dhcp/dhcpd.leases

COPY ./dhcp/config /etc/dhcp
COPY ./dhcp/defaults /etc/defaults
