FROM python:alpine3.17

WORKDIR /app/

COPY ["medicover_session.py" ,"medihunter*.py", "setup.py", "/app/"]

# Workaround for "use_2to3 is invalid" error
RUN pip install "setuptools<58.0.0"

RUN pip install .

ENTRYPOINT ["python", "./medihunter.py"]
