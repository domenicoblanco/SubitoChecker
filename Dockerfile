FROM python:3.9.4-alpine3.13

WORKDIR /

# Install depencencies
RUN set -eux && \
    apk --update add --no-cache git && \
    pip install --upgrade pip && \
    git clone https://github.com/domenicoblanco/SubitoChecker

RUN cd SubitoChecker && \
    pip install --no-cache-dir -r requirements.txt

# start
CMD ["python3", "/SubitoChecker/subitoChecker.py"]