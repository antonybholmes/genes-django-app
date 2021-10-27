FROM python:3.9-alpine

COPY requirements.txt /app/

WORKDIR /app

RUN apk add --no-cache --virtual build-deps postgresql-dev build-base
RUN python -m venv /env
RUN /env/bin/pip install --upgrade pip
RUN /env/bin/pip install --upgrade setuptools
RUN /env/bin/pip install --upgrade wheel
RUN /env/bin/pip install --no-cache-dir -r requirements.txt
RUN runDeps="$(scanelf --needed --nobanner --recursive /env \
        | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
        | sort -u \
        | xargs -r apk info --installed \
        | sort -u)" \
    && apk add --virtual rundeps $runDeps
RUN apk del build-deps

ADD . .


ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

EXPOSE 8300

CMD ["gunicorn", "--bind", ":8300", "--workers", "4", "genes.wsgi:application"]
