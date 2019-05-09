FROM python:3.6-alpine3.9
LABEL MAINTAINER="ricterzheng@gmail.com"

EXPOSE 8888
ENV LANG=C.UTF-8 TRAVIS_CI=1 BGMI_PATH=/bgmi BGMI_IN_DOCKER=1

VOLUME /bgmi

COPY ./requirements /opt/bgmi/requirements

WORKDIR /opt/bgmi

#RUN apk add docker --no-cache --repository http://mirrors.ustc.edu.cn/alpine/v3.9/main/ && \
RUN pip install "setuptools==41.0.1" -r requirements/prod.txt


COPY ./ /opt/bgmi/

RUN pip install -e ".[mysql]"

ENTRYPOINT ["/usr/local/bin/bgmi"]

CMD serve
