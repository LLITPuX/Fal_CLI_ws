#!/bin/sh
set -e

# Replace environment variables in nginx config
envsubst '${API_PORT}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

# Start nginx
exec nginx -g 'daemon off;'

