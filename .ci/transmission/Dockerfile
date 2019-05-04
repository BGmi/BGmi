FROM alpine:3.7

VOLUME ["/bgmi"]


RUN apk add --update --no-cache transmission-daemon

COPY transmission_settings.json /config/transmission_settings.json

EXPOSE 9091

CMD transmission-daemon -g /config/
