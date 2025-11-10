Deployment Guide (Examples)

This project ships without server-specific deploy configs. Below are examples you can copy/paste and adapt per server.

Nginx reverse proxy (HTTPS + WebSocket)
- Point your domain (e.g., chat.example.com) to the server IP (A record)
- Issue a certificate via certbot (webroot) or your preferred method
- Example vhost (replace server_name and cert paths):

```
map $http_upgrade $connection_upgrade { default upgrade; '' close; }

server {
  listen 80; listen [::]:80;
  server_name chat.example.com;
  location ^~ /.well-known/acme-challenge/ { root /var/www/letsencrypt; default_type text/plain; }
  location / { return 301 https://$host$request_uri; }
}

server {
  listen 443 ssl http2; listen [::]:443 ssl http2;
  server_name chat.example.com;
  ssl_certificate     /etc/letsencrypt/live/chat.example.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/chat.example.com/privkey.pem;

  # UI → container HTTP
  location / {
    proxy_pass http://127.0.0.1:9000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }

  # WebSocket at /ws → container WS (8765)
  location /ws {
    proxy_pass http://127.0.0.1:8765;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
    proxy_set_header Host $host;
    proxy_read_timeout 3600s;
  }
}
```

Compose and .env
- Copy `docker-compose.yml.example` → `docker-compose.yml`
- Pick an `.env` sample from `examples/env/` and adjust paths/UID/GID as needed
- Run: `docker compose up -d --build`

