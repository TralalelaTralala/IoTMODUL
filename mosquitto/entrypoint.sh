#!/bin/sh
set -eu

: "${MQTT_OPENHAB_PASSWORD:?MQTT_OPENHAB_PASSWORD is required}"
: "${MQTT_SIMULATOR_PASSWORD:?MQTT_SIMULATOR_PASSWORD is required}"

mkdir -p /mosquitto/data /mosquitto/certs /mosquitto/ca
if [ ! -s /mosquitto/certs/ca.crt ] || [ ! -s /mosquitto/certs/server.crt ] || [ ! -s /mosquitto/certs/server.key ]; then
    openssl req -x509 -newkey rsa:3072 -sha256 -nodes -days 1825 \
        -keyout /mosquitto/certs/ca.key -out /mosquitto/certs/ca.crt \
        -subj "/CN=IoTModul MQTT Local CA"
    openssl req -newkey rsa:2048 -sha256 -nodes \
        -keyout /mosquitto/certs/server.key -out /mosquitto/certs/server.csr \
        -subj "/CN=mosquitto"
    printf 'subjectAltName=DNS:mosquitto,DNS:localhost,IP:127.0.0.1\nextendedKeyUsage=serverAuth\n' > /mosquitto/certs/server.ext
    openssl x509 -req -sha256 -days 825 \
        -in /mosquitto/certs/server.csr \
        -CA /mosquitto/certs/ca.crt -CAkey /mosquitto/certs/ca.key \
        -CAcreateserial -out /mosquitto/certs/server.crt \
        -extfile /mosquitto/certs/server.ext
    cp /mosquitto/certs/ca.crt /mosquitto/ca/ca.crt
    chmod 0600 /mosquitto/certs/ca.key /mosquitto/certs/server.key
    chmod 0644 /mosquitto/certs/ca.crt /mosquitto/certs/server.crt /mosquitto/ca/ca.crt
    rm -f /mosquitto/certs/server.csr /mosquitto/certs/server.ext
fi

rm -f /mosquitto/data/passwordfile
cp /mosquitto/config/aclfile /mosquitto/data/aclfile
chmod 0600 /mosquitto/data/aclfile
mosquitto_passwd -b -c /mosquitto/data/passwordfile openhab "$MQTT_OPENHAB_PASSWORD"
mosquitto_passwd -b /mosquitto/data/passwordfile simulator "$MQTT_SIMULATOR_PASSWORD"
chmod 0640 /mosquitto/data/passwordfile
chown -R mosquitto:mosquitto /mosquitto/data /mosquitto/certs
exec su -s /bin/sh mosquitto -c 'exec /usr/sbin/mosquitto -c /mosquitto/config/mosquitto.conf'
