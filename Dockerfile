FROM ubuntu:latest
MAINTAINER ricterzheng@gmail.com

ENV LANG C.UTF-8

ADD ./ /opt/bgmi
WORKDIR /opt/bgmi

RUN apt-get update \
    && apt-get -y install aria2 nginx supervisor cron curl \
    && curl https://bootstrap.pypa.io/get-pip.py | python \
    && pip install -r requirements.txt \
    && python setup.py install \
    && cp others/aria2c.conf /root \
    && cp others/bgmi.conf /etc/nginx/sites-enabled/default \
    && cp others/supervisord.conf /etc/supervisor/conf.d/supervisord.conf


CMD /usr/sbin/nginx; /usr/bin/supervisord

EXPOSE 80

