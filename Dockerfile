FROM python:3.6.3
MAINTAINER furion <_@furion.me>

COPY . /src
WORKDIR /src

RUN pip install -r requirements.txt
RUN pip install git+git://github.com/Netherdrake/steem-python@master
RUN steempy set nodes http://136.243.77.24:8090

ENV PRODUCTION yes
ENV FLASK_HOST 0.0.0.0

EXPOSE 5000

CMD ["python", "src/steemdata-api.py"]
