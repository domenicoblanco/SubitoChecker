FROM python:3.9.4-alpine3.13

# Install depencencies
RUN set -eux && \
    apk --update add --no-cache git && \
    pip install --upgrade pip && \
    git clone https://github.com/domenicoblanco/SubitoChecker && \
    cd SubitoChecker && \
    pip install -r requirements.txt

# run without privileges
USER nobody

# start
CMD ["python3 SubitoChecker.py"]