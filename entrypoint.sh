#!/bin/bash

set -e -o pipefail

./manage.py migrate

cat <<EOF | ./manage.py shell
from django.contrib.auth import get_user_model

User = get_user_model()  # get the currently active user model,

User.objects.filter(username='$QUEUE_USER').exists() or \
    User.objects.create_superuser('$QUEUE_USER', 'doesntmatter@example.com', '$QUEUE_PASS')
EOF

./manage.py runserver 0.0.0.0:8000
