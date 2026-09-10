# Установка PowerPro + ERPNext на новый VPS

Проверено по официальной документации frappe_docker (сентябрь 2026):
образ собирается с `--secret=id=apps_json`, HTTPS даёт Traefik по переменной
`SITES_RULE`. Команды выполняет Джереми на своём сервере.

Ничего из этого не трогает боевой n8n-сервер.

## 0. Перед началом

- Куплен Hostinger **KVM 2**, локация **Phoenix**, шаблон **Ubuntu 24.04 with Docker**.
- DNS: `erp.powerprofessor.co` и `dev.erp.powerprofessor.co` → IP этого VPS.
  **Проверить до запуска** (`nslookup erp.powerprofessor.co`) — Let's Encrypt
  ограничивает число неудачных попыток.
- Репозиторий `powerpro-erp` на GitHub, содержимое этой папки залито в его корень.
- Снапшот чистой системы в hPanel.

## 1. Базовая гигиена сервера

```bash
adduser deploy && usermod -aG sudo,docker deploy
ufw allow OpenSSH && ufw allow 80 && ufw allow 443 && ufw enable
apt update && apt -y upgrade && apt -y install git dnsutils fail2ban
fallocate -l 4G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

Дальше всё под пользователем `deploy`.

## 2. Забрать репозитории

```bash
git clone https://github.com/frappe/frappe_docker ~/frappe_docker
```

## 3. Список приложений

```bash
cat > ~/apps.json <<'JSON'
[
  {"url": "https://github.com/frappe/erpnext", "branch": "version-16"},
  {"url": "https://github.com/ЛОГИН/powerpro-erp", "branch": "main"}
]
JSON
```

Ветка `version-16` — текущая стабильная в примерах официальной документации.
Если сборка упадёт на несовместимости, поменять здесь и в шаге 4 на `version-15`.

## 4. Собрать образ

```bash
cd ~/frappe_docker
docker build \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-16 \
  --secret=id=apps_json,src=/home/deploy/apps.json \
  --tag=powerpro/erp:latest \
  --file=images/layered/Containerfile .
```

15–30 минут на KVM 2. Список приложений передаётся секретом, а не build-arg —
так он не остаётся в метаданных слоёв образа.

## 5. Переменные окружения

```bash
mkdir -p ~/gitops
cat > ~/frappe_docker/.env <<'ENV'
CUSTOM_IMAGE=powerpro/erp
CUSTOM_TAG=latest
PULL_POLICY=never
DB_PASSWORD=ПРИДУМАТЬ_ДЛИННЫЙ
LETSENCRYPT_EMAIL=jeremy@powerpro.info
SITES_RULE=Host(`erp.powerprofessor.co`) || Host(`dev.erp.powerprofessor.co`)
ENV
```

Обратные кавычки в `SITES_RULE` обязательны — это синтаксис правил Traefik v3.

## 6. Запуск

```bash
cd ~/frappe_docker
docker compose --env-file .env \
  -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.https.yaml \
  config > ~/gitops/erp.yaml

docker compose --project-name erp -f ~/gitops/erp.yaml up -d
docker compose --project-name erp -f ~/gitops/erp.yaml ps
```

Все контейнеры `running`, кроме `configurator` — он отрабатывает один раз и
завершается, это нормально. Подождать минуту перед следующим шагом.

## 7. Два сайта

```bash
C="docker compose --project-name erp -f /home/deploy/gitops/erp.yaml"

$C exec backend bench new-site erp.powerprofessor.co \
  --mariadb-user-host-login-scope='%' \
  --db-root-password 'ТОТ_ЖЕ_DB_PASSWORD' \
  --admin-password 'ПАРОЛЬ_АДМИНА' \
  --install-app erpnext --install-app powerpro

$C exec backend bench new-site dev.erp.powerprofessor.co \
  --mariadb-user-host-login-scope='%' \
  --db-root-password 'ТОТ_ЖЕ_DB_PASSWORD' \
  --admin-password 'ПАРОЛЬ_АДМИНА' \
  --install-app erpnext --install-app powerpro

$C exec backend bench --site dev.erp.powerprofessor.co set-config developer_mode 1
```

Если `install-app powerpro` упадёт — скопировать ошибку целиком в чат.
Первый подозреваемый: `powerpro/powerpro/workspace/powerpro/powerpro.json`
(формат Workspace самый капризный). Его можно удалить из репозитория,
пересобрать образ и собрать рабочее пространство руками в интерфейсе.

## 8. Ночной бэкап

```bash
sudo tee /etc/cron.daily/erp-backup >/dev/null <<'SH'
#!/bin/bash
docker compose --project-name erp -f /home/deploy/gitops/erp.yaml exec -T backend \
  bench --site erp.powerprofessor.co backup --with-files
SH
sudo chmod +x /etc/cron.daily/erp-backup
```

Бэкапы лежат в `sites/erp.powerprofessor.co/private/backups`. Отправку в Dropbox
настроим отдельно (Integrations → Dropbox Settings внутри ERPNext либо rclone).

## 9. Обновление приложения

```bash
cd ~/frappe_docker
docker build --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-16 \
  --secret=id=apps_json,src=/home/deploy/apps.json \
  --tag=powerpro/erp:latest --file=images/layered/Containerfile .

docker compose --project-name erp -f ~/gitops/erp.yaml up -d --force-recreate
docker compose --project-name erp -f ~/gitops/erp.yaml exec backend \
  bench --site dev.erp.powerprofessor.co migrate
# убедиться, что всё в порядке, и только потом:
docker compose --project-name erp -f ~/gitops/erp.yaml exec backend \
  bench --site erp.powerprofessor.co migrate
```

**Всегда сначала dev, потом прод.**

## 10. Портейнер для глаз (по желанию)

```bash
docker run -d -p 127.0.0.1:9000:9000 --name portainer --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ce
```

Открывать через туннель: `ssh -L 9000:127.0.0.1:9000 deploy@IP` → http://localhost:9000
