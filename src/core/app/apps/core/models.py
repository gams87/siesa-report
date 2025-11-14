import logging

from django.db import models
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class BaseModelManager(models.Manager):
    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)


class BaseModel(models.Model):
    """Abstract base model with common fields and behaviors"""

    is_active = models.BooleanField(verbose_name=_("Activo"), default=True)
    created_at = models.DateTimeField(editable=False, auto_now_add=True, verbose_name=_("Creado el"))
    updated_at = models.DateTimeField(editable=False, auto_now=True, verbose_name=_("Actualizado el"))

    class Meta:
        abstract = True
        ordering = ["updated_at", "created_at"]


class Database(BaseModel):
    """Represents a database configured in the system"""

    name = models.CharField(max_length=255, unique=True, verbose_name=_("Nombre de la base de datos"))
    alias = models.CharField(max_length=100, unique=True, verbose_name=_("Alias de conexión"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Descripción"))

    class Meta:
        verbose_name = _("Base de datos")
        verbose_name_plural = _("Bases de datos")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Table(BaseModel):
    """Represents a table in the database"""

    database = models.ForeignKey(
        Database, on_delete=models.CASCADE, related_name="tables", verbose_name=_("Base de datos")
    )
    schema_name = models.CharField(max_length=255, verbose_name=_("Esquema"), default="public")
    table_name = models.CharField(max_length=255, verbose_name=_("Nombre de la tabla"))
    table_type = models.CharField(max_length=50, verbose_name=_("Tipo de tabla"), default="BASE TABLE")
    description = models.TextField(blank=True, null=True, verbose_name=_("Descripción"))
    row_count = models.BigIntegerField(null=True, blank=True, verbose_name=_("Número de filas"))

    class Meta:
        verbose_name = _("Tabla")
        verbose_name_plural = _("Tablas")
        ordering = ["schema_name", "table_name"]
        unique_together = [["database", "schema_name", "table_name"]]

    def __str__(self):
        return self.table_name


class Column(BaseModel):
    """Represents a column in a table"""

    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name="columns", verbose_name=_("Tabla"))
    column_name = models.CharField(max_length=255, verbose_name=_("Nombre de la columna"))
    ordinal_position = models.IntegerField(verbose_name=_("Posición ordinal"))
    data_type = models.CharField(max_length=100, verbose_name=_("Tipo de dato"))
    character_maximum_length = models.IntegerField(
        null=True, blank=True, verbose_name=_("Longitud máxima de caracteres")
    )
    numeric_precision = models.IntegerField(null=True, blank=True, verbose_name=_("Precisión numérica"))
    numeric_scale = models.IntegerField(null=True, blank=True, verbose_name=_("Escala numérica"))
    is_nullable = models.BooleanField(default=True, verbose_name=_("Permite NULL"))
    column_default = models.TextField(null=True, blank=True, verbose_name=_("Valor por defecto"))
    is_primary_key = models.BooleanField(default=False, verbose_name=_("Es llave primaria"))
    is_foreign_key = models.BooleanField(default=False, verbose_name=_("Es llave foránea"))
    foreign_table = models.CharField(max_length=255, null=True, blank=True, verbose_name=_("Tabla referenciada"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Descripción"))

    class Meta:
        verbose_name = _("Columna")
        verbose_name_plural = _("Columnas")
        ordering = ["table", "ordinal_position"]
        unique_together = [["table", "column_name"]]

    def __str__(self):
        return f"{self.table}.{self.column_name}"

    @property
    def slug(self):
        return f"{self.table.schema_name}_{self.table.table_name}_{self.column_name}".lower()


class Report(BaseModel):
    """Represents a report configuration"""

    class Orientation(models.TextChoices):
        VERTICAL = "vertical", _("Vertical")
        HORIZONTAL = "horizontal", _("Horizontal")

    class Order(models.TextChoices):
        ASC = "asc", _("Ascendente")
        DESC = "desc", _("Descendente")

    class Interval(models.TextChoices):
        ALL = "all", _("Todos")
        FIVE = "5", _("5 minutos")
        TEN = "10", _("10 minutos")
        FIFTEEN = "15", _("15 minutos")
        THIRTY = "30", _("30 minutos")
        SIXTY = "60", _("60 minutos")

    name = models.CharField(max_length=255, verbose_name=_("Nombre del reporte"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Descripción"))
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name="reports", verbose_name=_("Tabla"))
    orientation = models.CharField(
        max_length=20, choices=Orientation.choices, default=Orientation.VERTICAL, verbose_name=_("Orientación")
    )
    order = models.CharField(
        max_length=10, choices=Order.choices, default=Order.ASC, blank=True, verbose_name=_("Tipo de orden")
    )
    interval = models.CharField(
        max_length=10, choices=Interval.choices, default=Interval.ALL, verbose_name=_("Intervalo")
    )

    class Meta:
        verbose_name = _("Reporte")
        verbose_name_plural = _("Reportes")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_columns(self):
        """Returns ordered columns for this report"""
        return self.report_columns.filter(is_visible=True).select_related("column").order_by("order")

    def get_query(self):
        """Generates the SQL SELECT query for this report"""
        columns = self.get_columns()
        if not columns.exists():
            return None

        # Build column list with aliases
        column_list = []
        for rc in columns:
            col_name = rc.column.column_name
            display_name = rc.get_display_name()
            if col_name != display_name:
                column_list.append(f'"{col_name}" AS "{display_name}"')
            else:
                column_list.append(f'"{col_name}"')

        columns_str = ", ".join(column_list)
        schema_table = f'"{self.table.schema_name}"."{self.table.table_name}"'

        return f"SELECT {columns_str} FROM {schema_table}"

    def execute_query(self, limit=None, offset=None, start_date=None, end_date=None):
        """
        Executes the report query and returns results

        Args:
            limit: Number of rows to return
            offset: Number of rows to skip
            start_date: Start date filter (string YYYY-MM-DD)
            end_date: End date filter (string YYYY-MM-DD)

        Returns:
            tuple: (columns, rows, total_count)
        """
        from django.db import connections

        # Get database connection
        db_alias = self.table.database.alias
        connection = connections[db_alias]

        # Find interval and order_by columns
        order_by_column = self.report_columns.filter(order_by=True).first()
        interval_column = self.report_columns.filter(column__data_type__istartswith="timestamp").first()
        date_column = self.report_columns.filter(column__data_type__istartswith="timestamp").first()

        # Build WHERE clause for date filters
        where_conditions = []
        if date_column:
            if start_date:
                where_conditions.append(f"\"{date_column.column.column_name}\" >= '{start_date}'")
            if end_date:
                where_conditions.append(f"\"{date_column.column.column_name}\" < '{end_date}'::date + INTERVAL '1 day'")

        # Check if we need interval grouping
        use_interval = interval_column and self.interval != self.Interval.ALL

        if use_interval:
            # Build query with interval grouping
            interval_minutes = int(self.interval)
            date_col = interval_column.column.column_name

            # PostgreSQL interval grouping
            interval_select = f'''DATE_TRUNC('hour', "{date_col}") + 
                INTERVAL '{interval_minutes} min' * 
                FLOOR(EXTRACT(MINUTE FROM "{date_col}")::int / {interval_minutes})'''

            columns = self.get_columns()
            select_parts = [f'{interval_select} AS "{interval_column.get_display_name()}"']
            group_by_parts = ["1"]  # GROUP BY position 1 (Intervalo)
            current_position = 2

            for rc in columns:
                col_name = rc.column.column_name
                display_name = rc.get_display_name()

                if rc == interval_column:
                    # Skip the interval column, already added
                    continue
                elif rc.aggregate != ReportColumn.AggregateFunction.NONE:
                    # Apply aggregate function
                    agg_func = rc.aggregate.upper()
                    select_parts.append(f'{agg_func}("{col_name}") AS "{display_name}"')
                    current_position += 1
                else:
                    # Group by other columns (first value)
                    select_parts.append(f'"{col_name}" AS "{display_name}"')
                    group_by_parts.append(str(current_position))
                    current_position += 1

            columns_str = ", ".join(select_parts)
            schema_table = f'"{self.table.schema_name}"."{self.table.table_name}"'
            query = f"SELECT {columns_str} FROM {schema_table}"

            # Add WHERE clause
            if where_conditions:
                query += f" WHERE {' AND '.join(where_conditions)}"

            # Add GROUP BY
            query += f" GROUP BY {', '.join(group_by_parts)}"

            # Add ORDER BY
            if self.order:
                query += f' ORDER BY "{interval_column.get_display_name()}" {self.order.upper()}'

            # For interval queries, we need to count grouped results
            with connection.cursor() as cursor:
                # Build count query - count distinct groups
                count_query = f"SELECT COUNT(*) FROM ({query}) AS grouped_results"
                cursor.execute(count_query)
                total_count = cursor.fetchone()[0]

                # Add pagination to main query
                if limit is not None:
                    query += f" LIMIT {limit}"
                if offset is not None:
                    query += f" OFFSET {offset}"

                logger.debug("Query generated with interval: %s", query)
                cursor.execute(query)

                # Get column names
                columns = [col[0] for col in cursor.description]

                # Fetch all rows
                rows = cursor.fetchall()

            return columns, rows, total_count
        else:
            # Regular query without grouping
            query = self.get_query()
            if not query:
                return [], [], 0

            # Add WHERE clause
            if where_conditions:
                query += f" WHERE {' AND '.join(where_conditions)}"

            # Add ORDER BY
            if order_by_column and self.order:
                query += f' ORDER BY "{order_by_column.column.column_name}" {self.order.upper()}'

        with connection.cursor() as cursor:
            # Build count query
            count_query = f'SELECT COUNT(*) FROM "{self.table.schema_name}"."{self.table.table_name}"'
            if where_conditions:
                count_query += f" WHERE {' AND '.join(where_conditions)}"

            cursor.execute(count_query)
            total_count = cursor.fetchone()[0]

            # Execute main query with pagination
            if limit is not None:
                query += f" LIMIT {limit}"
            if offset is not None:
                query += f" OFFSET {offset}"

            logger.debug("Query generated without interval: %s", query)
            cursor.execute(query)

            # Get column names
            columns = [col[0] for col in cursor.description]

            # Fetch all rows
            rows = cursor.fetchall()

        return columns, rows, total_count


class ReportColumn(models.Model):
    """Represents a column included in a report"""

    class FormatColumn(models.TextChoices):
        TEXT = "text", _("Texto")
        NUMBER = "number", _("Número")
        DATE = "date", _("Fecha")
        DATETIME = "datetime", _("Fecha y hora")
        BOOLEAN = "boolean", _("Booleano")
        CURRENCY = "currency", _("Moneda")

    class AggregateFunction(models.TextChoices):
        NONE = "none", _("Ninguna (Primer valor)")
        SUM = "sum", _("Suma")
        AVG = "avg", _("Promedio")
        MIN = "min", _("Mínimo")
        MAX = "max", _("Máximo")
        COUNT = "count", _("Contar")

    report = models.ForeignKey(
        Report, on_delete=models.CASCADE, related_name="report_columns", verbose_name=_("Reporte")
    )
    column = models.ForeignKey(
        Column, on_delete=models.CASCADE, related_name="report_columns", verbose_name=_("Columna")
    )
    order = models.PositiveIntegerField(verbose_name=_("Orden"), default=0)
    format = models.CharField(
        max_length=20, choices=FormatColumn.choices, default=FormatColumn.TEXT, verbose_name=_("Formato")
    )
    display_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Nombre a mostrar"),
        help_text=_(
            "Nombre personalizado para la columna en el reporte. Si se deja vacío, se usa el nombre de la columna."
        ),
    )
    is_visible = models.BooleanField(default=True, verbose_name=_("Visible"))
    order_by = models.BooleanField(default=False, verbose_name=_("Ordenar por"))
    aggregate = models.CharField(
        max_length=10,
        choices=AggregateFunction.choices,
        default=AggregateFunction.NONE,
        verbose_name=_("Función de agregación"),
        help_text=_("Función a aplicar cuando se agrupa por intervalos"),
    )

    class Meta:
        verbose_name = _("Columna del reporte")
        verbose_name_plural = _("Columnas del reporte")
        ordering = ["report", "order"]
        unique_together = [["report", "column"]]

    def __str__(self):
        return f"{self.report.name} - {self.column.column_name}"

    def get_display_name(self):
        """Returns the display name or the column name if not set"""
        return self.display_name or self.column.column_name
