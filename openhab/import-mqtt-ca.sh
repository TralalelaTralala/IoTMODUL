#!/bin/sh
set -eu

: "${MQTT_OPENHAB_PASSWORD:?MQTT_OPENHAB_PASSWORD is required}"

mkdir -p /openhab/conf/things
cp /run/openhab-things-source/*.things /openhab/conf/things/

if [ -s /run/mqtt-ca/ca.crt ]; then
    cacerts="$(find /usr/lib/jvm -path '*/lib/security/cacerts' -print -quit)"
    keytool -delete -alias iotmodul-mqtt-ca -keystore "$cacerts" -storepass changeit >/dev/null 2>&1 || true
    keytool -importcert -noprompt -trustcacerts -alias iotmodul-mqtt-ca \
        -file /run/mqtt-ca/ca.crt -keystore "$cacerts" -storepass changeit >/dev/null
fi

umask 077
printf 'Bridge mqtt:broker:iotmodul "Локальний MQTT-брокер" [ host="mosquitto", port=8883, secure=true, hostnameValidated=true, username="openhab", password="%s", clientID="openhab-iotmodul", qos=1, lwtTopic="iotmodul/status/openhab", lwtMessage="OFFLINE", lwtQos=1, lwtRetain=true, birthTopic="iotmodul/status/openhab", birthMessage="ONLINE", birthQos=1, birthRetain=true ]\n' \
    "$MQTT_OPENHAB_PASSWORD" > /openhab/conf/things/mqtt-bridge.generated.things
chmod 0600 /openhab/conf/things/mqtt-bridge.generated.things

exec /entrypoint "$@"
