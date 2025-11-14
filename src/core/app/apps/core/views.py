import base64
import json
import logging
from datetime import date, datetime
from io import StringIO

import pandas as pd
from django.contrib import messages
from django.core.management import call_command
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods
from django_htmx.middleware import HtmxDetails

from apps.company.models import Company
from apps.core.models import Database
from apps.utils.pdf_utils import PDFUtils

from .models import Column, Report, ReportColumn, Table

logger = logging.getLogger(__name__)


class HtmxHttpRequest(HttpRequest):
    htmx: HtmxDetails


@require_GET
def favicon(request: HtmxHttpRequest) -> HttpResponse:
    """Serve a simple SVG favicon"""

    return HttpResponse(
        (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            + '<text y=".9em" font-size="90">📚</text>'
            + "</svg>"
        ),
        content_type="image/svg+xml",
    )


def index_view(request: HtmxHttpRequest) -> HttpResponse:
    """View for the index page"""

    if request.htmx:
        base_template = "partials/base.html"
    else:
        base_template = "base.html"

    ctx = {"base_template": base_template}
    return render(request, "dashboard.html", context=ctx)


def dashboard_view(request: HtmxHttpRequest) -> HttpResponse:
    """View for the dashboard page"""
    if request.htmx:
        base_template = "partials/base.html"
    else:
        base_template = "base.html"

    # Obtener estadísticas de reportes
    total_reports = Report.objects.filter(is_active=True).count()
    reports_with_interval = Report.objects.filter(is_active=True).exclude(interval=Report.Interval.ALL).count()

    # Obtener estadísticas de base de datos
    total_databases = Database.objects.filter(is_active=True).count()
    total_tables = Table.objects.filter(is_active=True).count()
    total_columns = Column.objects.filter(is_active=True).count()

    # Reportes recientes (últimos 5)
    recent_reports = Report.objects.filter(is_active=True).select_related("table__database").order_by("-updated_at")[:5]

    # Tablas más usadas en reportes
    top_tables = (
        Table.objects.filter(is_active=True)
        .annotate(num_reports=Count("reports"))
        .filter(num_reports__gt=0)
        .order_by("-num_reports")[:5]
    )

    # Estadísticas por base de datos
    databases_stats = []
    for db in Database.objects.filter(is_active=True):
        tables_count = db.tables.filter(is_active=True).count()
        columns_count = Column.objects.filter(table__database=db, is_active=True).count()
        reports_count = Report.objects.filter(table__database=db, is_active=True).count()
        databases_stats.append(
            {
                "name": db.name,
                "tables": tables_count,
                "columns": columns_count,
                "reports": reports_count,
            }
        )

    ctx = {
        "base_template": base_template,
        "total_reports": total_reports,
        "reports_with_interval": reports_with_interval,
        "total_databases": total_databases,
        "total_tables": total_tables,
        "total_columns": total_columns,
        "recent_reports": recent_reports,
        "top_tables": top_tables,
        "databases_stats": databases_stats,
    }
    return render(request, "dashboard.html", context=ctx)


def config_report_sync_view(request: HtmxHttpRequest) -> HttpResponse:
    """Sync database metadata by calling the management command"""
    try:
        # Capture command output
        out = StringIO()
        call_command("sync_database_metadata", stdout=out, stderr=out)

        # Get the output
        output = out.getvalue()
        logger.info(f"Sync command output: {output}")
        logger.info("Sync database metadata output:")
        logger.info(output)

        response = HttpResponse(status=204)
        response["HX-Trigger"] = "toast:synced"
        return response
    except Exception as e:
        logger.error(f"Error syncing database metadata: {e}")
        response = HttpResponse(status=500)
        response["HX-Trigger"] = json.dumps({"toasts:error": {"message": str(e)}})
        return response


def config_report_view(request: HtmxHttpRequest) -> HttpResponse:
    """View to list and paginate reports configuration"""

    reports = Report.objects.filter(is_active=True).select_related("table", "table__database").order_by("-updated_at")

    page_num = request.GET.get("page")
    page_size = int(request.GET.get("page_size", 10))
    page = Paginator(object_list=reports, per_page=page_size).get_page(page_num)

    template_name = "config_report.html"
    if request.htmx:
        base_template = "partials/base.html"
        if request.htmx.target == "table-data":
            template_name += "#table-section"
    else:
        base_template = "base.html"

    ctx = {"base_template": base_template, "page": page}
    return render(request, template_name, context=ctx)


@require_http_methods(["DELETE"])
def config_report_delete_view(request: HtmxHttpRequest, report_id: int) -> HttpResponse:
    """Delete a report by ID"""
    report = get_object_or_404(Report, pk=report_id)
    report.delete()
    response = HttpResponse(status=204)
    response["HX-Trigger"] = "updateTable, toast:deleted"
    return response


def config_report_detail_view(request: HtmxHttpRequest) -> HttpResponse:
    """View to create or edit a report configuration"""

    if request.method == "POST":
        data = request.POST
        report_id = data.get("report_id")
        table = get_object_or_404(Table, pk=data.get("table_id"))
        name = data.get("name").strip().capitalize()
        orientation = data.get("orientation")
        order = data.get("order")
        interval = data.get("interval")

        config = {}
        columns = Column.objects.filter(id__in=data.getlist("columns"), table=table)
        for column in columns:
            config[column.slug] = {
                "format": data.get(f"format_{column.id}", ReportColumn.FormatColumn.TEXT),
                "display_name": data.get(f"display_name_{column.id}", column.column_name),
                "order": data.get(f"order_{column.id}", 0),
                "order_by": data.get(f"order_by_{column.id}", "off") == "on",
                "aggregate": data.get(f"aggregate_{column.id}", ReportColumn.AggregateFunction.NONE),
            }

        if report_id:
            report = get_object_or_404(Report, pk=report_id)
            report.name = name
            report.table = table
            report.orientation = orientation
            report.order = order
            report.interval = interval
            report.save()
            report.report_columns.all().delete()
        else:
            report = Report.objects.create(
                name=name,
                table=table,
                orientation=orientation,
                order=order,
                interval=interval,
            )

        for column in columns:
            report.report_columns.create(
                column=column,
                format=config[column.slug]["format"],
                order=int(config[column.slug]["order"]),
                display_name=config[column.slug]["display_name"].strip().capitalize(),
                order_by=config[column.slug]["order_by"],
                aggregate=config[column.slug]["aggregate"],
                is_visible=True,
            )

        if not report_id:
            messages.success(request, "Reporte guardado exitosamente.")
        else:
            messages.success(request, "Reporte actualizado exitosamente.")

        return redirect("config-report")

    report_id = request.GET.get("report_id")
    report = None
    if report_id:
        report = get_object_or_404(Report, pk=report_id)

    template_name = "partials/config_report_detail.html"
    if request.htmx:
        base_template = "partials/base.html"
    else:
        base_template = "base.html"

    tables = Table.objects.all()
    ctx = {"base_template": base_template, "tables": tables, "report": report}
    return render(request, template_name, context=ctx)


def config_report_column_view(request: HtmxHttpRequest) -> HttpResponse:
    report_id = request.GET.get("report_id")
    if report_id:
        report = get_object_or_404(Report, pk=report_id)
        report_columns = report.report_columns.select_related("column").order_by("order")
        table_id = report.table.id
    else:
        report_columns = None
        table_id = request.GET.get("table_id")

    columns = []
    if table_id:
        columns = Column.objects.filter(table_id=table_id, is_active=True).order_by("ordinal_position")

    ctx = {"columns": columns, "report_columns": report_columns}
    return render(request, "partials/config_report_columns.html", context=ctx)


def report_view(request: HtmxHttpRequest) -> HttpResponse:
    if request.htmx:
        base_template = "partials/base.html"
    else:
        base_template = "base.html"

    reports = Report.objects.filter(is_active=True).order_by("name")

    ctx = {"base_template": base_template, "reports": reports}
    return render(request, "report.html", context=ctx)


def report_execute_view(request):
    """Execute a report and display results with pagination"""

    if request.htmx:
        base_template = "partials/base.html"
    else:
        base_template = "base.html"

    report_id = request.GET.get("report_id")
    report = Report.objects.prefetch_related("report_columns").get(pk=report_id)

    # Get pagination parameters
    page_number = request.GET.get("page", 1)
    page_size = int(request.GET.get("page_size", 10))

    # Get date filters with today as default
    today = date.today().isoformat()
    start_date = request.GET.get("start_date") or today
    end_date = request.GET.get("end_date") or today

    # Calculate limit and offset
    try:
        page_number = int(page_number)
    except (ValueError, TypeError):
        page_number = 1

    offset = (page_number - 1) * page_size

    # Execute query
    try:
        columns, rows, total_count = report.execute_query(
            limit=page_size,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
        )

        # Convert dates to date objects for template formatting
        start_date_obj = datetime.fromisoformat(start_date).date()
        end_date_obj = datetime.fromisoformat(end_date).date()

        # Create paginator
        paginator = Paginator(range(total_count), page_size)
        page_obj = paginator.get_page(page_number)

        ctx = {
            "base_template": base_template,
            "report": report,
            "columns": columns,
            "rows": rows,
            "page_obj": page_obj,
            "total_count": total_count,
            "page_size": page_size,
            "start_date": start_date_obj,
            "end_date": end_date_obj,
        }
    except Exception as e:
        logger.info("Error executing report: %s", e)
        ctx = {
            "base_template": base_template,
            "report": report,
            "error": str(e),
        }

    return render(request, "partials/report_execute.html", context=ctx)


def report_gen_pdf_view(request):
    """Generate a PDF for the report"""

    # Get report parameters
    report_id = request.GET.get("report_id")
    if not report_id:
        return HttpResponse("Report ID is required", status=400)

    report = Report.objects.prefetch_related("report_columns").get(pk=report_id)

    # Get date filters with today as default
    today = date.today().isoformat()
    start_date = request.GET.get("start_date") or today
    end_date = request.GET.get("end_date") or today

    # Execute query to get all data (no pagination for PDF)
    try:
        columns, rows, total_count = report.execute_query(
            limit=None,  # No limit for PDF - get all data
            offset=None,
            start_date=start_date,
            end_date=end_date,
        )

        # Convert to pandas DataFrame
        df = pd.DataFrame(rows, columns=columns)

        # Determine which columns are numeric for formatting
        numeric_columns = []
        for rc in report.report_columns.all():
            if rc.format in [ReportColumn.FormatColumn.NUMBER, ReportColumn.FormatColumn.CURRENCY]:
                numeric_columns.append(rc.get_display_name())

        # Company info (you can customize this)
        if not Company.objects.filter(is_default=True).exists():
            raise Exception("Debe crear una compañía predeterminada.")

        company = Company.objects.filter(is_default=True).order_by("-updated_at").first()
        company_data = company.to_dict_for_pdf()

        # Convert dates for display
        start_date_obj = datetime.fromisoformat(start_date).date()
        end_date_obj = datetime.fromisoformat(end_date).date()

        # Generate PDF
        report_base64 = PDFUtils(
            company=company_data,
            template="report_generic.html",
            is_landscape=report.orientation == Report.Orientation.HORIZONTAL,
            context={
                "title": report.name,
                "start_date": start_date_obj.strftime("%d/%m/%Y"),
                "end_date": end_date_obj.strftime("%d/%m/%Y"),
                "total_regs": total_count,
            },
        ).gen_with_df(
            filename=f"{report.name.lower().replace(' ', '_')}.pdf",
            df=df,
            columns_number=numeric_columns,
        )

        response = HttpResponse(
            json.dumps(
                {"base64_report": base64.b64encode(report_base64.read()).decode("utf-8"), "filename": report_base64.name}
            ),
            content_type="application/json",
        )
        return response

    except Exception as e:
        logger.info("Error generating PDF: %s", e)
        return HttpResponse(json.dumps({"error": str(e)}), content_type="application/json", status=400)
