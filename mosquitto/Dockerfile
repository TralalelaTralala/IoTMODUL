FROM eclipse-mosquitto:2
USER root
RUN apk add --no-cache openssl
COPY entrypoint.sh /usr/local/bin/iotmodul-mosquitto-entrypoint
RUN chmod 0755 /usr/local/bin/iotmodul-mosquitto-entrypoint
ENTRYPOINT ["/usr/local/bin/iotmodul-mosquitto-entrypoint"]
