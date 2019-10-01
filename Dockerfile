FROM python:3.6
LABEL MAINTAINER="ricterzheng@gmail.com"

EXPOSE 8888
ENV LANG=C.UTF-8 TRAVIS_CI=1 BGMI_PATH=/bgmi BGMI_IN_DOCKER=1

VOLUME /bgmi
WORKDIR /opt/bgmi
COPY ./ /opt/bgmi/

#RUN pip install -e '.[mysql]'

RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python && \
    export PATH=$HOME/.poetry/bin:$PATH && \
    poetry config settings.virtualenvs.create false && \
    poetry install --no-dev -E mysql

ENTRYPOINT ["python", "-m", "bgmi"]

CMD ["serve"]
