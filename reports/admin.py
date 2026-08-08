from django.contrib import admin
from .models import Branch, Product, Sale, SaleLine, SavedReport, AuditLog


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'city', 'is_active')
    search_fields = ('name', 'code')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'barcode', 'category')
    search_fields = ('name', 'barcode')


class SaleLineInline(admin.TabularInline):
    model = SaleLine
    extra = 0


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('receipt_no', 'branch', 'sold_at', 'payment', 'status', 'total')
    list_filter = ('branch', 'status', 'payment')
    date_hierarchy = 'sold_at'
    inlines = [SaleLineInline]


@admin.register(SavedReport)
class SavedReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'period_from', 'period_to', 'created_at', 'author', 'retention')
    list_filter = ('report_type', 'retention')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'action', 'object_repr', 'actor')
    list_filter = ('action',)
    readonly_fields = ('created_at', 'actor', 'action', 'object_repr', 'detail')

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