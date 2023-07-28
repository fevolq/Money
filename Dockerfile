FROM python:3.7-slim-buster

WORKDIR /data/money

COPY requirements.txt /data/money/

RUN pip install -r requirements.txt

COPY . /data/money

ARG PORT=8888

ENV PORT=${PORT}

EXPOSE ${PORT}

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port $PORT"]
