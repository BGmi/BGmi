FROM ubuntu:latest
MAINTAINER ricterzheng@gmail.com

ADD ./ /opt/bgmi

WORKDIR /opt/bgmi
RUN apt-get -y update \
    && apt-get -y install aria2 nginx python-pip
RUN pip install -r requirements.txt \
    && python setup.py install

COPY others/aria2c.conf /root
COPY others/bgmi.conf /etc/nginx/site-enabled

RUN aria2c --conf-path=/root/aria2c.conf
RUN nginx -s reload
RUN bgmi_http

EXPOSE 80

