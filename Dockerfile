FROM python:3.7-slim-buster

WORKDIR /app/money

COPY requirements.txt /app/money/

ARG LIBRARY="-i https://pypi.tuna.tsinghua.edu.cn/simple"

RUN pip install -r requirements.txt ${LIBRARY}

COPY . /app/money

ARG PORT=8888

ENV PORT=${PORT} WorthUseCache=true

EXPOSE ${PORT}

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port $PORT"]
