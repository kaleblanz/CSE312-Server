FROM python:3.8

ENV HOME /root
WORKDIR /root

COPY ./requirements.txt ./requirements.txt
COPY ./server.py ./server.py
COPY ./public ./public
COPY ./util ./util
COPY ./path_functions.py ./path_functions.py

RUN pip3 install -r requirements.txt
#this installs ffmpeg during the building process of this docker file
RUN apt-get update && apt-get install -y ffmpeg

EXPOSE 8000

ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.2.1/wait /wait
RUN chmod +x /wait

CMD /wait && python3 -u server.py
