FROM python:3.5.2
MAINTAINER furion <_@furion.me>

RUN pip install -U steemtools
RUN pip install --upgrade --no-deps --force-reinstall  git+git://github.com/xeroc/piston@develop
RUN pip install --upgrade --no-deps --force-reinstall  git+git://github.com/xeroc/python-steemlib@develop
RUN pip install --upgrade --no-deps --force-reinstall  git+git://github.com/xeroc/python-graphenelib@develop

#RUN pip install git+git://github.com/xeroc/python-graphenelib@develop
#RUN pip install git+git://github.com/xeroc/python-steemlib@develop
#RUN pip install git+git://github.com/xeroc/piston@develop

COPY . /src
WORKDIR /src

RUN pip install -r requirements.txt

EXPOSE 5000

RUN chmod +x wait-for-it.sh
CMD ["./wait-for-it.sh", "ipfs:5001", "--timeout=60", "--strict", "--", "python", "server.py"]
