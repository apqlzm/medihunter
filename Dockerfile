FROM python:3.9-alpine
RUN apk add --no-cache libxml2 libxslt libxml2-dev libxslt-dev gcc musl-dev

WORKDIR /app/

COPY ids ids

COPY ["medicover_session.py" ,"medihunter*.py", "setup.py", "/app/"]

# Workaround for "use_2to3 is invalid" error
RUN pip install "setuptools<58.0.0"
RUN pip install rpds-py
RUN python setup.py install

ENTRYPOINT ["python", "./medihunter.py"]
