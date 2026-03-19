#!/bin/bash
# Deploy Polymarket Broker to Tencent Cloud
# Usage: ./deploy/deploy.sh <server_ip> [ssh_key_path]

set -e

SERVER=${1:?Usage: deploy.sh <server_ip> [ssh_key_path]}
SSH_KEY=${2:-~/.ssh/id_rsa}
SSH_CMD="ssh -i $SSH_KEY root@$SERVER"
REMOTE_DIR="/opt/polymarket-broker"

echo "=== Deploying to $SERVER ==="

# 1. Install Docker if not present
echo "[1/6] Checking Docker..."
$SSH_CMD "docker --version 2>/dev/null || (curl -fsSL https://get.docker.com | sh && systemctl enable docker)"

# 2. Install Docker Compose
echo "[2/6] Checking Docker Compose..."
$SSH_CMD "docker compose version 2>/dev/null || (apt-get update && apt-get install -y docker-compose-plugin)"

# 3. Clone/update repo
echo "[3/6] Syncing code..."
$SSH_CMD "if [ -d $REMOTE_DIR ]; then cd $REMOTE_DIR && git pull; else git clone https://github.com/Oceanjackson1/Polymarket-Broker.git $REMOTE_DIR; fi"

# 4. Copy .env (you must create .env on server first)
echo "[4/6] Checking .env..."
$SSH_CMD "test -f $REMOTE_DIR/.env || echo 'WARNING: No .env file! Create $REMOTE_DIR/.env before starting.'"

# 5. SSL certificate setup
echo "[5/6] Setting up SSL..."
$SSH_CMD "mkdir -p $REMOTE_DIR/deploy/ssl"
$SSH_CMD "if ! test -f $REMOTE_DIR/deploy/ssl/fullchain.pem; then
    apt-get install -y certbot 2>/dev/null
    certbot certonly --standalone -d polydesk.eu.cc --non-interactive --agree-tos -m admin@polydesk.eu.cc || echo 'SSL setup failed - configure manually'
    if test -f /etc/letsencrypt/live/polydesk.eu.cc/fullchain.pem; then
        ln -sf /etc/letsencrypt/live/polydesk.eu.cc/fullchain.pem $REMOTE_DIR/deploy/ssl/fullchain.pem
        ln -sf /etc/letsencrypt/live/polydesk.eu.cc/privkey.pem $REMOTE_DIR/deploy/ssl/privkey.pem
    fi
fi"

# 6. Build and start
echo "[6/6] Building and starting..."
$SSH_CMD "cd $REMOTE_DIR && docker compose up -d --build"

echo ""
echo "=== Deployment complete ==="
echo "API: https://polydesk.eu.cc/api/v1/"
echo "Docs: https://polydesk.eu.cc/docs"
echo ""
echo "Next steps:"
echo "  1. Create .env on server: ssh root@$SERVER 'vi $REMOTE_DIR/.env'"
echo "  2. Point DNS: polydesk.eu.cc → $SERVER (A record)"
echo "  3. Restart: ssh root@$SERVER 'cd $REMOTE_DIR && docker compose restart'"
