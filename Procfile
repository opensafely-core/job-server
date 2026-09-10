release: /usr/bin/env bash /app/deployment/release_phase.sh
web: gunicorn --config gunicorn.conf.py jobserver.wsgi
rapstatus: python ./manage.py rap_status_service
