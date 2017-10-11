FROM ubuntu:latest
MAINTAINER ricterzheng@gmail.com

ENV LANG C.UTF-8

ADD ./ /opt/bgmi
WORKDIR /opt/bgmi

RUN apt-get update \
    && apt-get -y install aria2 nginx supervisor cron wget unzip python3 \
    && wget -O- https://bootstrap.pypa.io/get-pip.py | python3 \
    && pip install -r requirements.txt \
    && python3 setup.py install \
    && cp others/aria2c.conf /root \
    && cp others/bgmi.conf /etc/nginx/sites-enabled/default \
    && cp others/supervisord.conf /etc/supervisor/conf.d/supervisord.conf \
    && wget https://github.com/binux/yaaw/archive/master.zip \
    && unzip master.zip \
    && mv yaaw-master /yaaw \
    && rm master.zip \
    && ln -s /bgmi /root/.bgmi


CMD /usr/sbin/nginx; /usr/bin/supervisord

EXPOSE 80
EXPOSE 6800
