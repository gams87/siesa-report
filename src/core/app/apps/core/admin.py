from django import forms
from django.contrib import admin

from .models import Column, Database, Report, ReportColumn, Table


class ReportAdminForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si el formulario tiene una instancia (editando un reporte existente)
        if self.instance.pk and self.instance.table:
            # Filtrar las columnas para mostrar solo las de la tabla seleccionada
            self.fields["table"].widget.can_delete_related = False
            self.fields["table"].widget.can_change_related = False


@admin.register(Database)
class DatabaseAdmin(admin.ModelAdmin):
    list_display = ["name", "alias", "is_active", "created_at", "updated_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "alias", "description"]
    readonly_fields = ["created_at", "updated_at"]


class ColumnInline(admin.TabularInline):
    model = Column
    extra = 0
    fields = [
        "column_name",
        "ordinal_position",
        "data_type",
        "is_nullable",
        "is_primary_key",
        "is_foreign_key",
        "is_active",
    ]
    readonly_fields = ["ordinal_position"]


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ["table_name", "schema_name", "database", "table_type", "row_count", "is_active", "updated_at"]
    list_filter = ["database", "schema_name", "table_type", "is_active"]
    search_fields = ["table_name", "schema_name", "description"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [ColumnInline]


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = [
        "column_name",
        "table",
        "ordinal_position",
        "data_type",
        "is_nullable",
        "is_primary_key",
        "is_foreign_key",
        "is_active",
    ]
    list_filter = ["table__database", "data_type", "is_nullable", "is_primary_key", "is_foreign_key", "is_active"]
    search_fields = ["column_name", "table__table_name", "description"]
    readonly_fields = ["created_at", "updated_at"]

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        # Filtrar por tabla si se proporciona en los parámetros
        table_id = request.GET.get("table__id__exact")
        if table_id:
            queryset = queryset.filter(table_id=table_id)

        return queryset, use_distinct


class ReportColumnInline(admin.TabularInline):
    model = ReportColumn
    extra = 1
    fields = ["column", "order", "display_name", "is_visible"]
    ordering = ["order"]
    autocomplete_fields = ["column"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "column":
            # Obtener el ID del reporte desde la URL
            report_id = request.resolver_match.kwargs.get("object_id")
            if report_id:
                try:
                    report = Report.objects.get(pk=report_id)
                    # Filtrar solo las columnas de la tabla seleccionada en el reporte
                    kwargs["queryset"] = Column.objects.filter(table=report.table, is_active=True)
                except Report.DoesNotExist:
                    pass
            else:
                # Si es un nuevo reporte, no mostrar columnas hasta que se seleccione una tabla
                kwargs["queryset"] = Column.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    form = ReportAdminForm
    list_display = ["name", "table", "orientation", "is_active", "created_at", "updated_at"]
    list_filter = ["orientation", "is_active", "table__database", "created_at"]
    search_fields = ["name", "description", "table__table_name"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [ReportColumnInline]
    autocomplete_fields = ["table"]

    class Media:
        js = ("admin/js/report_admin.js",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("table", "table__database")


@admin.register(ReportColumn)
class ReportColumnAdmin(admin.ModelAdmin):
    list_display = ["report", "column", "order", "display_name", "is_visible"]
    list_filter = ["is_visible", "report__table__database"]
    search_fields = ["report__name", "column__column_name", "display_name"]
    ordering = ["report", "order"]
    autocomplete_fields = ["report", "column"]
