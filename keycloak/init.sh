#!/bin/bash
set -e

KCADM=/opt/keycloak/bin/kcadm.sh
REALM=${KEYCLOAK_REALM:-deepaudiolab}
ADMIN_USERNAME=${DEFAULT_ADMIN_USERNAME:-admin}
ADMIN_PASSWORD=${DEFAULT_ADMIN_PASSWORD:-admin}

echo "==> Authenticating with master realm..."
$KCADM config credentials \
  --server http://keycloak:8080 \
  --realm master \
  --user admin \
  --password admin

echo "==> Creating user '$ADMIN_USERNAME' in realm '$REALM' (if not exists)..."
$KCADM create users -r "$REALM" \
  -s username="$ADMIN_USERNAME" \
  -s email="${ADMIN_USERNAME}@deepaudio.lab" \
  -s firstName="Admin" \
  -s lastName="User" \
  -s enabled=true 2>/dev/null || echo "User '$ADMIN_USERNAME' already exists, skipping..."

echo "==> Setting password..."
$KCADM set-password -r "$REALM" --username "$ADMIN_USERNAME" --new-password "$ADMIN_PASSWORD"

echo "==> Assigning 'admin' realm role..."
$KCADM add-roles -r "$REALM" --uusername "$ADMIN_USERNAME" --rolename admin 2>/dev/null || echo "Role already assigned, skipping..."

echo "==> Done! User '$ADMIN_USERNAME' is ready."
