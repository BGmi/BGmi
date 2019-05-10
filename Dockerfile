FROM python:3.6-alpine3.9
LABEL MAINTAINER="ricterzheng@gmail.com"

EXPOSE 8888
ENV LANG=C.UTF-8 TRAVIS_CI=1 BGMI_PATH=/bgmi BGMI_IN_DOCKER=1

VOLUME /bgmi

COPY ./requirements/build.txt /opt/bgmi/requirements/build.txt

WORKDIR /opt/bgmi

RUN pip install -r requirements/build.txt

COPY ./ /opt/bgmi/

RUN pip install -e ".[mysql]"

ENTRYPOINT ["/usr/local/bin/bgmi"]

CMD serve
