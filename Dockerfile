FROM python:3.7-slim-buster

WORKDIR /data/money

COPY requirements.txt /data/money/

ARG LIBRARY="-i https://pypi.tuna.tsinghua.edu.cn/simple"

RUN pip install -r requirements.txt ${LIBRARY}

COPY . /data/money

ARG PORT=8888

ENV PORT=${PORT} WorthUseCache=true

EXPOSE ${PORT}

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port $PORT"]
