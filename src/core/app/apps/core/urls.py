from django.urls import path

from apps.core import views

urlpatterns = [
    path("", views.dashboard_view, name="index"),
    path("favicon.ico", views.favicon, name="favicon"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("config-report/", views.config_report_view, name="config-report"),
    path("config-report-sync/", views.config_report_sync_view, name="config-report-sync"),
    path("config-report-detail/", views.config_report_detail_view, name="config-report-detail"),
    path("config-report-delete/<int:report_id>/", views.config_report_delete_view, name="config-report-delete"),
    path("config-report/columns/", views.config_report_column_view, name="config-report-columns"),
    path("reports/", views.report_view, name="report"),
    path("reports-execute/", views.report_execute_view, name="report-execute"),
    path("reports-generate-pdf/", views.report_gen_pdf_view, name="report-generate-pdf"),
]
