FROM python:latest
RUN apt update && \
    apt upgrade -y && \
    pip install awscli boto3 detect-secrets && \
    apt install -y python3-pip && \
    apt install -y jq
RUN git clone https://github.com/toniblyx/prowler
ADD script.sh /
RUN chmod +x /script.sh
WORKDIR /prowler
ENTRYPOINT ["/script.sh"]
