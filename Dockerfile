FROM python:3.8

RUN mkdir /app
WORKDIR /app

RUN pip install poetry


COPY pyproject.toml /app/pyproject.toml


RUN poetry config virtualenvs.create false && poetry install

RUN mkdir /init

COPY create.py /app/create.py

CMD ["python", "create.py"]