FROM python:3.9.4-alpine3.13

# Install depencencies
RUN set -eux && \
    apk --update add --no-cache git && \
    pip install --upgrade pip && \
    cd / && \
    git clone https://github.com/domenicoblanco/SubitoChecker && \
    chmod 775 -R SubitoChecker 

USER nobody

RUN cd SubitoChecker && \
    pip install -r requirements.txt

# start
CMD ["python3 /SubitoChecker/SubitoChecker.py"]