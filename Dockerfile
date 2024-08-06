FROM alpine:latest

# Install packages
RUN apk add --no-cache nut python3 py3-paho-mqtt

# Copy configuration files
COPY config /etc/nut

# Copy scripts
COPY scripts /opt/scripts

# Create directories
RUN mkdir /var/run/nut

# Set ownersihp and permissions for the directories
RUN chmod -R 755 /opt/scripts
RUN chmod 640 /etc/nut/*
RUN chown -R nut:nut /etc/nut
RUN chmod -R 750 /var/run/nut
RUN chown -R nut:nut /var/run/nut