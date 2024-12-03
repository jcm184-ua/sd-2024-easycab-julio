FROM python:3.11.10-bookworm

WORKDIR /usr/src/app

COPY taxis/sensors/ /usr/src/app/
COPY shared/ /usr/src/app/
RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt

CMD [ "python", "./EC_S.py"]