FROM python:3.11.10-bookworm

WORKDIR /usr/src/app

COPY core/central/ /usr/src/app/
COPY shared/ /usr/src/app/
RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt

ENTRYPOINT [ "python", "./EC_Central.py"]