# Установка на новый VPS (KVM 2, Ubuntu 24.04 + Docker)

Это порядок шагов по официальному пути `frappe_docker` — «свой образ с нашими
приложениями» + compose с MariaDB, Redis и HTTPS. Команды выполняет Джереми.
Ничего из этого не трогает боевой n8n-сервер.

## 0. Перед началом

- DNS: `erp.powerpro.info` и `dev.erp.powerpro.info` → IP этого VPS.
- Снапшот чистой системы в hPanel.
- Репозиторий `powerpro-erp` на GitHub (можно публичный — секретов в коде нет).
  Впиши его URL в `deploy/apps.json` вместо `REPLACE_ME`.
- Ветка ERPNext: `version-15` (если `version-16` уже помечена stable — можно её,
  тогда поменяй ветку в `apps.json` и `FRAPPE_BRANCH` ниже).

## 1. Базовая гигиена сервера

```bash
adduser deploy && usermod -aG sudo,docker deploy   # работать не под root
ufw allow OpenSSH && ufw allow 80 && ufw allow 443 && ufw enable
apt update && apt -y upgrade && apt -y install git fail2ban
```

## 2. Собрать образ с ERPNext + powerpro

```bash
git clone https://github.com/frappe/frappe_docker ~/frappe_docker && cd ~/frappe_docker
export APPS_JSON_BASE64=$(base64 -w 0 ~/powerpro-erp/deploy/apps.json)
docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-15 \
  --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --tag=powerpro/erp:latest \
  --file=images/layered/Containerfile .
```

Сборка занимает 10–20 минут на KVM 2.

## 3. Compose

```bash
mkdir -p ~/gitops && cat > ~/gitops/erp.env <<'ENV'
CUSTOM_IMAGE=powerpro/erp
CUSTOM_TAG=latest
PULL_POLICY=never
DB_PASSWORD=CHANGE_ME_LONG_RANDOM
SITES=`erp.powerpro.info`,`dev.erp.powerpro.info`
LETSENCRYPT_EMAIL=jeremy@powerpro.info
ENV

docker compose --project-name erp \
  --env-file ~/gitops/erp.env \
  -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.https.yaml \
  config > ~/gitops/erp.yaml

docker compose --project-name erp -f ~/gitops/erp.yaml up -d
```

`compose.https.yaml` поднимает Traefik с Let's Encrypt — отдельный Caddy не нужен,
пока на этом сервере только ERPNext.

## 4. Создать сайты и поставить приложения

```bash
docker compose --project-name erp exec backend \
  bench new-site erp.powerpro.info \
    --mariadb-user-host-login-scope='%' \
    --db-root-password "$DB_PASSWORD" \
    --admin-password CHANGE_ME \
    --install-app erpnext --install-app powerpro

docker compose --project-name erp exec backend \
  bench new-site dev.erp.powerpro.info \
    --mariadb-user-host-login-scope='%' \
    --db-root-password "$DB_PASSWORD" \
    --admin-password CHANGE_ME \
    --install-app erpnext --install-app powerpro

docker compose --project-name erp exec backend bench --site dev.erp.powerpro.info set-config developer_mode 1
```

Открыть https://erp.powerpro.info → мастер настройки ERPNext (компания, валюта USD,
финансовый год, **Accounts не активировать как книгу** — см. план).

## 5. Ночной бэкап

```bash
cat > /etc/cron.daily/erp-backup <<'SH'
#!/bin/bash
docker compose --project-name erp -f /root/gitops/erp.yaml exec -T backend \
  bench --site erp.powerpro.info backup --with-files
SH
chmod +x /etc/cron.daily/erp-backup
```

Файлы бэкапа лежат в томе `sites/erp.powerpro.info/private/backups`; вторым
шагом настроим отправку в Dropbox (Frappe умеет это из коробки: Integrations →
Dropbox Settings, либо `rclone` по крону).

## 6. Обновление приложения powerpro

```bash
cd ~/frappe_docker && docker build ... --tag=powerpro/erp:latest .   # как в шаге 2
docker compose --project-name erp -f ~/gitops/erp.yaml up -d --force-recreate
docker compose --project-name erp exec backend bench --site erp.powerpro.info migrate
```

Сначала на `dev.erp.powerpro.info`, потом на боевом.

## Портал для глаз (по желанию)

```bash
docker run -d -p 127.0.0.1:9000:9000 --name portainer --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ce
```

Открывать через SSH-туннель: `ssh -L 9000:127.0.0.1:9000 deploy@IP` → http://localhost:9000.
