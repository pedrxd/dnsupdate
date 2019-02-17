FROM alpine

RUN apk add --update python3

COPY updater.py /usr/bin/dnsupdater
RUN mkdir /etc/dnsupdater
COPY domain.json /etc/dnsupdater/

RUN chmod +x /usr/bin/dnsupdater
ENTRYPOINT ["dnsupdater"]
