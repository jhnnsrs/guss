FROM python:3.8

RUN mkdir /app
WORKDIR /app

RUN pip install poetry


COPY pyproject.toml /app/pyproject.toml


RUN poetry config virtualenvs.create false && poetry install

RUN mkdir /init

COPY main.py /app/main.py
COPY ser /app/ser

CMD ["python", "main.py"]