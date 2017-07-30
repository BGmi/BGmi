FROM ubuntu:latest
MAINTAINER ricterzheng@gmail.com

ENV LANG C.UTF-8
ADD ./ /opt/bgmi

WORKDIR /opt/bgmi
RUN apt-get -y update \
    && apt-get -y install aria2 nginx python3 python3-pip supervisor cron
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt \
    && python3 setup.py install

COPY others/aria2c.conf /root
COPY others/bgmi.conf /etc/nginx/sites-enabled/default
COPY others/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD /usr/sbin/nginx; /usr/bin/supervisord

EXPOSE 80

