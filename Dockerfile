FROM python:latest AS builder
WORKDIR /home/app
COPY pyproject.toml .
COPY poetry.lock .

RUN pip install -U pip poetry
RUN poetry self add poetry-plugin-export
RUN poetry export -f requirements.txt --output requirements.txt --with gunicorn && \
     pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt


FROM python:latest
RUN apt-get update && apt-get -y install ffmpeg netcat-traditional


COPY recording_index /home/app
WORKDIR /home/app

COPY --from=builder /wheels /wheels
RUN pip install --upgrade pip
RUN pip install --no-cache /wheels/*

# Start gunicorn
RUN chmod +x launcher.sh
CMD ["./launcher.sh"]

EXPOSE 8000