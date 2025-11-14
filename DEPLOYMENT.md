# Deployment Guide - SIESA Report Production

## Pre-requisitos

- Docker y Docker Compose instalados
- Dominio configurado (opcional para SSL)
- Servidor con al menos 2GB RAM

## Pasos para Desplegar

### 1. Configurar Variables de Entorno

```bash
cp .env.prod.example .env.prod
nano .env.prod
```

Configura las siguientes variables:
- `SECRET_KEY`: Genera una nueva con `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `ALLOWED_HOSTS`: Tu dominio (ej: `app.tuempresa.com`)
- Todas las contraseñas de bases de datos
- `REDIS_PASSWORD`
- `CORS_ALLOWED_ORIGINS`

### 2. Ejecutar Script de Despliegue

```bash
chmod +x deploy.sh
./deploy.sh
```

### 3. Verificar Servicios

```bash
docker compose -f docker-compose.prod.yaml ps
```

Todos los servicios deben estar en estado "Up".

### 4. Acceder a la Aplicación

- Aplicación: `http://tu-servidor`
- Admin: `http://tu-servidor/admin`
- Usuario por defecto: `admin` / `admin123`

## Configurar SSL (Opcional)

### 1. Obtener Certificado Let's Encrypt

```bash
# Instalar certbot
docker compose -f docker-compose.prod.yaml run --rm certbot certonly \
  --webroot --webroot-path=/var/www/certbot \
  -d tu-dominio.com -d www.tu-dominio.com
```

### 2. Habilitar HTTPS en Nginx

Edita `nginx/conf.d/default.conf`:
- Descomenta el bloque server HTTPS
- Cambia `your-domain.com` por tu dominio
- Descomenta el redirect HTTP → HTTPS

```bash
docker compose -f docker-compose.prod.yaml restart nginx
```

### 3. Auto-renovación de Certificado

Agrega a crontab:
```bash
0 0 * * * docker compose -f /ruta/a/docker-compose.prod.yaml run --rm certbot renew
```

## Comandos Útiles

### Ver Logs
```bash
# Todos los servicios
docker compose -f docker-compose.prod.yaml logs -f

# Solo Django
docker compose -f docker-compose.prod.yaml logs -f core

# Solo Nginx
docker compose -f docker-compose.prod.yaml logs -f nginx
```

### Ejecutar Comandos Django
```bash
# Migraciones
docker compose -f docker-compose.prod.yaml exec core python manage.py migrate

# Crear superusuario
docker compose -f docker-compose.prod.yaml exec core python manage.py createsuperuser

# Shell Django
docker compose -f docker-compose.prod.yaml exec core python manage.py shell

# Sincronizar metadata
docker compose -f docker-compose.prod.yaml exec core python manage.py sync_database_metadata
```

### Backup de Base de Datos
```bash
# Backup
docker compose -f docker-compose.prod.yaml exec db pg_dump -U siesa_user siesa_report_prod > backup.sql

# Restore
docker compose -f docker-compose.prod.yaml exec -T db psql -U siesa_user siesa_report_prod < backup.sql
```

### Actualizar Aplicación
```bash
# Pull cambios
git pull origin main

# Rebuild y restart
docker compose -f docker-compose.prod.yaml build core
docker compose -f docker-compose.prod.yaml up -d
docker compose -f docker-compose.prod.yaml exec core python manage.py migrate
docker compose -f docker-compose.prod.yaml exec core python manage.py collectstatic --noinput
```

### Monitoreo
```bash
# Ver uso de recursos
docker stats

# Ver estado de servicios
docker compose -f docker-compose.prod.yaml ps

# Health checks
curl http://localhost/health
```

## Troubleshooting

### Servicio no inicia
```bash
docker compose -f docker-compose.prod.yaml logs nombre_servicio
```

### Error de permisos en static/media
```bash
docker compose -f docker-compose.prod.yaml exec core chown -R www-data:www-data /app/static /app/media
```

### Redis connection error
Verifica que `REDIS_PASSWORD` en `.env.prod` coincida en todos los servicios.

### Database connection error
1. Verifica que las credenciales en `.env.prod` sean correctas
2. Asegúrate que el servicio `db` esté healthy: `docker compose -f docker-compose.prod.yaml ps db`

## Seguridad

1. **Cambiar contraseñas por defecto** inmediatamente
2. **Habilitar firewall** - solo puertos 80, 443, 22
3. **Configurar SSL** - Always use HTTPS en producción
4. **Backups regulares** - Automatizar backups diarios
5. **Monitoreo** - Configurar alertas para servicios caídos
6. **Updates** - Mantener Docker images actualizadas

## Performance

### Escalar Workers
```bash
# Más Celery workers
docker compose -f docker-compose.prod.yaml up -d --scale celery_worker=4
```

### Aumentar Gunicorn Workers
Edita `docker-compose.prod.yaml`, cambia `--workers 4` por el número deseado (regla: 2-4 x CPU cores).

## Mantenimiento

### Limpiar logs
```bash
docker compose -f docker-compose.prod.yaml exec core find /var/log -name "*.log" -type f -delete
```

### Limpiar volúmenes no usados
```bash
docker volume prune
```

### Reiniciar todos los servicios
```bash
docker compose -f docker-compose.prod.yaml restart
```
