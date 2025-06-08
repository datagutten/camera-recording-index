#!/usr/bin/env sh
echo "Waiting for DB..."

python3 manage.py collectstatic --noinput
while ! nc -z $SQL_HOST $SQL_PORT; do
  sleep 0.1
done
echo "DB started"
python3 manage.py makemigrations --noinput
python3 manage.py migrate

gunicorn