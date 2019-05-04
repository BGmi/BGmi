FROM alpine:edge
LABEL MAINTAINER=trim21<trim21me@gmail.com>

EXPOSE 6800

ENV PACKAGE "aria2"

ARG CURRENT_UID='1000'
ARG CURRENT_GID='1000'

ENV USER=aria2

# Install package using --no-cache to update index and remove unwanted files

RUN addgroup --gid "$CURRENT_GID" "$USER" &&\
    adduser --uid $CURRENT_UID --disabled-password --ingroup "$USER" --no-create-home "$USER" &&\
    apk add --update --no-cache $PACKAGE
#    sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories && \

USER $USER

COPY ./entrypoint.sh /entrypoint.sh

CMD sh /entrypoint.sh
