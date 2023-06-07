FROM python:3.8

RUN mkdir /app

RUN pip install poetry


COPY pyproject.toml /app/pyproject.toml
WORKDIR /app

RUN poetry config virtualenvs.create false && poetry install


COPY README.md /app/README.md

COPY main.py /app/main.py
COPY mysecrets.py /app/mysecrets.py
COPY setup.py /app/setup.py
COPY utils.py /app/utils.py



CMD ["python", "main.py"]