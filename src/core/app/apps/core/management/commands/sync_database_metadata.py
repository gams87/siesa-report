"""
Comando de Django para sincronizar metadatos de la base de datos.
Lee todas las tablas y columnas de la base de datos y las almacena en los modelos.
"""

from django.core.management.base import BaseCommand
from django.db import connections

from apps.core.models import Column, Database, Table


class Command(BaseCommand):
    help = "Sincroniza todas las tablas y columnas de la base de datos con los modelos"

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            type=str,
            default="report",
            help='Nombre del alias de la base de datos en settings.py (default: "default")',
        )
        parser.add_argument(
            "--clear",
            default=False,
            action="store_true",
            help="Eliminar todos los datos existentes antes de sincronizar",
        )

    def handle(self, *args, **options):
        db_alias = options["database"]
        clear_data = options["clear"]

        self.stdout.write(
            self.style.SUCCESS(f"🔄 Iniciando sincronización de metadatos para la base de datos: {db_alias}")
        )

        # Si se solicita, limpiar datos existentes
        if clear_data:
            self.stdout.write(self.style.WARNING("⚠️  Eliminando datos existentes..."))
            Column.objects.all().delete()
            Table.objects.all().delete()
            Database.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("✅ Datos eliminados"))

        # Obtener o crear el registro de la base de datos
        db_config = connections.databases[db_alias]
        database, created = Database.objects.get_or_create(
            alias=db_alias,
            defaults={
                "name": db_config.get("NAME", db_alias),
                "description": f"Base de datos {db_alias}",
                "is_active": True,
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"✅ Base de datos creada: {database.name}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"ℹ️  Base de datos encontrada: {database.name}"))

        # Obtener conexión a la base de datos
        conn = connections[db_alias]

        # Detectar el tipo de base de datos
        db_vendor = conn.vendor
        self.stdout.write(f"🔍 Tipo de base de datos: {db_vendor}")

        if db_vendor == "postgresql":
            self._sync_postgresql(database, conn)
        elif db_vendor == "mysql":
            self._sync_mysql(database, conn)
        elif db_vendor == "sqlite":
            self._sync_sqlite(database, conn)
        else:
            self.stdout.write(self.style.ERROR(f"❌ Base de datos no soportada: {db_vendor}"))
            return

        self.stdout.write(self.style.SUCCESS("✅ Sincronización completada exitosamente"))

    def _sync_postgresql(self, database, conn):
        """Sincroniza metadatos para PostgreSQL"""
        self.stdout.write("📊 Sincronizando tablas y columnas de PostgreSQL...")

        with conn.cursor() as cursor:
            # Obtener todas las tablas
            cursor.execute("""
                SELECT 
                    table_schema,
                    table_name,
                    table_type
                FROM information_schema.tables
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                ORDER BY table_schema, table_name
            """)

            tables_data = cursor.fetchall()
            self.stdout.write(f"📋 Encontradas {len(tables_data)} tablas")

            for schema_name, table_name, table_type in tables_data:
                # Crear o actualizar la tabla
                table, created = Table.objects.update_or_create(
                    database=database,
                    schema_name=schema_name,
                    table_name=table_name,
                    defaults={"table_type": table_type, "is_active": True},
                )

                if created:
                    self.stdout.write(f"  ✅ Tabla creada: {schema_name}.{table_name}")
                else:
                    self.stdout.write(f"  🔄 Tabla actualizada: {schema_name}.{table_name}")

                # Obtener columnas de la tabla
                cursor.execute(
                    """
                    SELECT 
                        column_name,
                        ordinal_position,
                        data_type,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """,
                    [schema_name, table_name],
                )

                columns_data = cursor.fetchall()

                # Obtener llaves primarias
                cursor.execute(
                    """
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name 
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                        AND tc.table_schema = %s
                        AND tc.table_name = %s
                """,
                    [schema_name, table_name],
                )

                primary_keys = {row[0] for row in cursor.fetchall()}

                # Obtener llaves foráneas
                cursor.execute(
                    """
                    SELECT 
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name
                    FROM information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_schema = %s
                        AND tc.table_name = %s
                """,
                    [schema_name, table_name],
                )

                foreign_keys = {row[0]: row[1] for row in cursor.fetchall()}

                # Crear o actualizar columnas
                for col_data in columns_data:
                    (
                        column_name,
                        ordinal_position,
                        data_type,
                        char_max_length,
                        num_precision,
                        num_scale,
                        is_nullable,
                        column_default,
                    ) = col_data

                    Column.objects.update_or_create(
                        table=table,
                        column_name=column_name,
                        defaults={
                            "ordinal_position": ordinal_position,
                            "data_type": data_type,
                            "character_maximum_length": char_max_length,
                            "numeric_precision": num_precision,
                            "numeric_scale": num_scale,
                            "is_nullable": is_nullable == "YES",
                            "column_default": column_default,
                            "is_primary_key": column_name in primary_keys,
                            "is_foreign_key": column_name in foreign_keys,
                            "foreign_table": foreign_keys.get(column_name),
                            "is_active": True,
                        },
                    )

                self.stdout.write(f"    💾 {len(columns_data)} columnas sincronizadas")

    def _sync_mysql(self, database, conn):
        """Sincroniza metadatos para MySQL"""
        self.stdout.write("📊 Sincronizando tablas y columnas de MySQL...")

        with conn.cursor() as cursor:
            # Obtener el nombre de la base de datos
            cursor.execute("SELECT DATABASE()")
            db_name = cursor.fetchone()[0]

            # Obtener todas las tablas
            cursor.execute(
                """
                SELECT 
                    TABLE_SCHEMA,
                    TABLE_NAME,
                    TABLE_TYPE
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME
            """,
                [db_name],
            )

            tables_data = cursor.fetchall()
            self.stdout.write(f"📋 Encontradas {len(tables_data)} tablas")

            for schema_name, table_name, table_type in tables_data:
                table, created = Table.objects.update_or_create(
                    database=database,
                    schema_name=schema_name,
                    table_name=table_name,
                    defaults={"table_type": table_type, "is_active": True},
                )

                if created:
                    self.stdout.write(f"  ✅ Tabla creada: {table_name}")
                else:
                    self.stdout.write(f"  🔄 Tabla actualizada: {table_name}")

                # Obtener columnas de la tabla
                cursor.execute(
                    """
                    SELECT 
                        COLUMN_NAME,
                        ORDINAL_POSITION,
                        DATA_TYPE,
                        CHARACTER_MAXIMUM_LENGTH,
                        NUMERIC_PRECISION,
                        NUMERIC_SCALE,
                        IS_NULLABLE,
                        COLUMN_DEFAULT,
                        COLUMN_KEY
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                """,
                    [db_name, table_name],
                )

                columns_data = cursor.fetchall()

                for col_data in columns_data:
                    (
                        column_name,
                        ordinal_position,
                        data_type,
                        char_max_length,
                        num_precision,
                        num_scale,
                        is_nullable,
                        column_default,
                        column_key,
                    ) = col_data

                    Column.objects.update_or_create(
                        table=table,
                        column_name=column_name,
                        defaults={
                            "ordinal_position": ordinal_position,
                            "data_type": data_type,
                            "character_maximum_length": char_max_length,
                            "numeric_precision": num_precision,
                            "numeric_scale": num_scale,
                            "is_nullable": is_nullable == "YES",
                            "column_default": column_default,
                            "is_primary_key": column_key == "PRI",
                            "is_foreign_key": column_key == "MUL",
                            "is_active": True,
                        },
                    )

                self.stdout.write(f"    💾 {len(columns_data)} columnas sincronizadas")

    def _sync_sqlite(self, database, conn):
        """Sincroniza metadatos para SQLite"""
        self.stdout.write("📊 Sincronizando tablas y columnas de SQLite...")

        with conn.cursor() as cursor:
            # Obtener todas las tablas
            cursor.execute("""
                SELECT name 
                FROM sqlite_master 
                WHERE type='table' 
                    AND name NOT LIKE 'sqlite_%'
                    AND name NOT LIKE 'django_%'
                ORDER BY name
            """)

            tables_data = cursor.fetchall()
            self.stdout.write(f"📋 Encontradas {len(tables_data)} tablas")

            for (table_name,) in tables_data:
                table, created = Table.objects.update_or_create(
                    database=database,
                    schema_name="main",
                    table_name=table_name,
                    defaults={"table_type": "BASE TABLE", "is_active": True},
                )

                if created:
                    self.stdout.write(f"  ✅ Tabla creada: {table_name}")
                else:
                    self.stdout.write(f"  🔄 Tabla actualizada: {table_name}")

                # Obtener información de columnas
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns_data = cursor.fetchall()

                for col_data in columns_data:
                    (cid, column_name, data_type, not_null, column_default, is_pk) = col_data

                    Column.objects.update_or_create(
                        table=table,
                        column_name=column_name,
                        defaults={
                            "ordinal_position": cid + 1,
                            "data_type": data_type,
                            "is_nullable": not not_null,
                            "column_default": column_default,
                            "is_primary_key": bool(is_pk),
                            "is_active": True,
                        },
                    )

                self.stdout.write(f"    💾 {len(columns_data)} columnas sincronizadas")
