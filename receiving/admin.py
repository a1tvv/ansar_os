from django.contrib import admin
from .models import Supplier, ReceivingDocument, ReceivingLine


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'terms')
    search_fields = ('name',)


class ReceivingLineInline(admin.TabularInline):
    model = ReceivingLine
    extra = 0


@admin.register(ReceivingDocument)
class ReceivingDocumentAdmin(admin.ModelAdmin):
    list_display = ('doc_no', 'supplier', 'branch', 'status', 'created_at', 'author')
    list_filter = ('branch', 'status', 'supplier')
    date_hierarchy = 'created_at'
    inlines = [ReceivingLineInline]
