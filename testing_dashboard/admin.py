from django.contrib import admin
from .models import TestSuite, TestRun, TestCase


@admin.register(TestSuite)
class TestSuiteAdmin(admin.ModelAdmin):
    list_display = ['name', 'file_path', 'created_at']
    search_fields = ['name', 'file_path']
    list_filter = ['created_at']


@admin.register(TestRun)
class TestRunAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'started_at', 'total_tests', 'passed_tests', 'failed_tests', 'success_rate']
    list_filter = ['status', 'started_at']
    search_fields = ['executed_by__username']
    readonly_fields = ['success_rate']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('executed_by')


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'browser', 'duration_ms', 'suite', 'run']
    list_filter = ['status', 'browser', 'run__started_at']
    search_fields = ['title', 'suite__name']
    readonly_fields = ['started_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('suite', 'run')
