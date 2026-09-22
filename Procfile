release: python ./manage.py check --deploy && python ./manage.py migrate
web: gunicorn --config gunicorn.conf.py jobserver.wsgi
rapstatus: python ./manage.py rap_status_service
