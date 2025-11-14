#!/bin/bash

# Script para inicializar la base de datos de reportes

echo "🚀 Iniciando configuración de base de datos de reportes..."

# Ejecutar el script SQL en el contenedor de PostgreSQL
docker compose exec -T db psql -U postgres -f /backups/init_report_db.sql

if [ $? -eq 0 ]; then
    echo "✅ Base de datos configurada exitosamente!"
    echo ""
    echo "📊 Información de la base de datos:"
    echo "   - Nombre: siesa_report_db"
    echo "   - Usuario: siesa_report_user"
    echo "   - Password: 123456"
    echo ""
    echo "📋 Tablas creadas:"
    echo "   - clientes (5 registros de ejemplo)"
    echo "   - productos (10 registros de ejemplo)"
    echo "   - ventas (12 registros de ejemplo)"
    echo "   - detalle_ventas (múltiples registros)"
    echo "   - vista_ventas_detalladas (vista para reportes)"
    echo ""
    echo "🔐 Permisos otorgados al usuario siesa_report_user"
else
    echo "❌ Error al configurar la base de datos"
    exit 1
fi
