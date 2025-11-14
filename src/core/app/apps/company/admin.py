from django.contrib import admin

from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "phone", "is_default", "created_at", "updated_at"]
    list_filter = ["is_default", "created_at"]
    search_fields = ["name", "email", "phone"]
    readonly_fields = ["created_at", "updated_at"]
