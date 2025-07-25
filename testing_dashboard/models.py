from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class TestSuite(models.Model):
    """Representa un conjunto de pruebas (archivo .spec.ts)"""
    name = models.CharField(max_length=200, help_text="Nombre del archivo de prueba")
    file_path = models.CharField(max_length=500, help_text="Ruta del archivo")
    description = models.TextField(blank=True, help_text="Descripción opcional")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['name', 'file_path']
        ordering = ['name']
    
    def __str__(self):
        return self.name


class TestRun(models.Model):
    """Representa una ejecución completa de pruebas"""
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('passed', 'All Passed'),
        ('failed', 'Some Failed'),
        ('error', 'Error'),
    ]
    
    executed_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running')
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.IntegerField(null=True, blank=True, help_text="Duración en milisegundos")
    
    # Estadísticas
    total_tests = models.IntegerField(default=0)
    passed_tests = models.IntegerField(default=0)
    failed_tests = models.IntegerField(default=0)
    skipped_tests = models.IntegerField(default=0)
    
    # Configuración de Playwright
    playwright_config = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Run {self.id} - {self.started_at.strftime('%Y-%m-%d %H:%M')} ({self.status})"
    
    @property
    def success_rate(self):
        if self.total_tests == 0:
            return 0
        return round((self.passed_tests / self.total_tests) * 100, 2)


class TestCase(models.Model):
    """Representa un caso de prueba individual"""
    STATUS_CHOICES = [
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
        ('flaky', 'Flaky'),
    ]
    
    BROWSER_CHOICES = [
        ('chromium', 'Chromium'),
        ('firefox', 'Firefox'),
        ('webkit', 'WebKit'),
        ('msedge', 'Microsoft Edge'),
    ]
    
    run = models.ForeignKey(TestRun, on_delete=models.CASCADE, related_name='test_cases')
    suite = models.ForeignKey(TestSuite, on_delete=models.CASCADE)
    
    title = models.CharField(max_length=500, help_text="Título del test")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    browser = models.CharField(max_length=20, choices=BROWSER_CHOICES)
    
    duration_ms = models.IntegerField(help_text="Duración en milisegundos")
    retry_count = models.IntegerField(default=0)
    
    # Detalles de error si falló
    error_message = models.TextField(blank=True)
    error_stack = models.TextField(blank=True)
    
    # Attachments (screenshots, videos, traces)
    attachments = models.JSONField(default=list, blank=True)
    
    # Metadata adicional
    annotations = models.JSONField(default=list, blank=True)
    worker_index = models.IntegerField(null=True, blank=True)
    
    started_at = models.DateTimeField()
    
    class Meta:
        ordering = ['started_at']
    
    def __str__(self):
        return f"{self.title} ({self.browser}) - {self.status}"
