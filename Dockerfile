FROM python:3.6.4
MAINTAINER furion <_@furion.me>

COPY . /src
WORKDIR /src

RUN pip install git+git://github.com/Netherdrake/steem-python@master
RUN steempy set nodes http://steemd.steemdata.com:8090
RUN pip install -r requirements.txt

ENV PRODUCTION yes
ENV FLASK_HOST 0.0.0.0

EXPOSE 5000

CMD ["python", "src/steemdata-api.py"]
