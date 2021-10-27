#!/bin/bash

export NAME=edbw                              # Name of the application
export DIR=/home/ubuntu/webapps/${NAME}
export DJANGODIR=/home/ubuntu/webapps/${NAME} #/webapps/hello_django/hello             # Django project directory
export SOCKFILE=${DIR}/gunicorn.sock  # we will communicte using this unix socket
export USER=ubuntu #${NAME}                                        # the user to run as
export GROUP=ubuntu #webapps                                     # the group to run as
export NUM_WORKERS=4                                     # how many worker processes should Gunicorn spawn
export DJANGO_SETTINGS_MODULE=${NAME}.settings             # which settings file should Django use
export DJANGO_WSGI_MODULE=${NAME}.wsgi                     # WSGI module name

export PATH="/home/ubuntu/miniconda3/bin:$PATH"

echo "Starting $NAME as `whoami`"

# Activate the virtual environment
#workon edbw
cd $DJANGODIR
#source ../bin/activate

export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
exec gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user=$USER --group=$GROUP \
  --bind=unix:$SOCKFILE \
  --log-level=debug
