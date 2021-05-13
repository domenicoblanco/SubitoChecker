FROM python:3.9.4-alpine3.13

# Install depencencies
RUN set -eux && \
    apk --update add --no-cache git && \
    pip install --upgrade pip && \
    cd / && \
    git clone https://github.com/domenicoblanco/SubitoChecker

RUN cd SubitoChecker && \
    pip install -r requirements.txt

# add to cron
RUN echo '*/5 * * * * python3 /SubitoChecker/SubitoChecker.py' > /etc/crontabs/root

# start
CMD ["crond", "-l 2", "-f"]