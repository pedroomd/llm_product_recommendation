#!/usr/bin/env bash
# initial_script.sh
# Usage: ./initial_script.sh host:port -- command args

set -e

hostport=$1
shift 1

IFS=':' read -r host port <<< "$hostport"

echo "Waiting for $host:$port..."

while ! nc -z "$host" "$port"; do
  sleep 1
done

echo "$host:$port is available - executing command"
exec "$@"