release: python ./manage.py check --deploy && python ./manage.py migrate
web: gunicorn --no-control-socket --config gunicorn.conf.py jobserver.wsgi
rapstatus: python ./manage.py rap_status_service
