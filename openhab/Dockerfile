FROM openhab/openhab:4.2.2
USER root
COPY import-mqtt-ca.sh /usr/local/bin/import-mqtt-ca
RUN chmod 0755 /usr/local/bin/import-mqtt-ca
ENTRYPOINT ["/usr/local/bin/import-mqtt-ca"]
CMD ["gosu", "openhab", "tini", "-s", "./start.sh"]
