from django.shortcuts import render
from django.views.generic import ListView, DetailView, TemplateView
from django.http import JsonResponse
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from .models import TestSuite, TestRun, TestCase


class DashboardView(TemplateView):
    """Vista principal del dashboard con estadísticas generales"""
    template_name = 'testing_dashboard/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas generales
        context['total_runs'] = TestRun.objects.count()
        context['total_suites'] = TestSuite.objects.count()
        context['total_tests'] = TestCase.objects.count()
        
        # Estadísticas de los últimos 7 días
        last_week = timezone.now() - timedelta(days=7)
        recent_runs = TestRun.objects.filter(started_at__gte=last_week)
        
        context['recent_runs_count'] = recent_runs.count()
        context['recent_success_rate'] = self.calculate_success_rate(recent_runs)
        
        # Últimos runs
        context['latest_runs'] = TestRun.objects.select_related('executed_by').order_by('-started_at')[:5]
        
        # Distribución por browser
        context['browser_stats'] = self.get_browser_stats()
        
        # Suites más activas
        context['active_suites'] = self.get_active_suites()
        
        return context
    
    def calculate_success_rate(self, runs):
        if not runs.exists():
            return 0
        total_tests = sum(run.total_tests for run in runs)
        passed_tests = sum(run.passed_tests for run in runs)
        return round((passed_tests / total_tests * 100), 2) if total_tests > 0 else 0
    
    def get_browser_stats(self):
        return TestCase.objects.values('browser').annotate(
            count=Count('id'),
            avg_duration=Avg('duration_ms')
        ).order_by('-count')
    
    def get_active_suites(self):
        return TestSuite.objects.annotate(
            test_count=Count('testcase'),
            recent_runs=Count('testcase__run', filter=Q(testcase__run__started_at__gte=timezone.now() - timedelta(days=7)))
        ).order_by('-recent_runs')[:5]


class TestRunListView(ListView):
    """Lista de todas las ejecuciones de pruebas"""
    model = TestRun
    template_name = 'testing_dashboard/run_list.html'
    context_object_name = 'runs'
    paginate_by = 20
    ordering = ['-started_at']
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('executed_by')
        
        # Filtros
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(started_at__date__gte=date_from)
        
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(started_at__date__lte=date_to)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = TestRun.STATUS_CHOICES
        context['current_filters'] = {
            'status': self.request.GET.get('status', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
        }
        return context


class TestRunDetailView(DetailView):
    """Detalle de una ejecución específica"""
    model = TestRun
    template_name = 'testing_dashboard/run_detail.html'
    context_object_name = 'run'
    
    def get_queryset(self):
        return super().get_queryset().select_related('executed_by').prefetch_related(
            'test_cases__suite'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        run = self.object
        
        # Agrupar tests por suite
        tests_by_suite = {}
        for test in run.test_cases.all():
            suite_name = test.suite.name
            if suite_name not in tests_by_suite:
                tests_by_suite[suite_name] = []
            tests_by_suite[suite_name].append(test)
        
        context['tests_by_suite'] = tests_by_suite
        
        # Estadísticas por browser
        context['browser_stats'] = run.test_cases.values('browser').annotate(
            count=Count('id'),
            passed=Count('id', filter=Q(status='passed')),
            failed=Count('id', filter=Q(status='failed')),
            avg_duration=Avg('duration_ms')
        ).order_by('browser')
        
        return context


class TestSuiteListView(ListView):
    """Lista de todas las suites de pruebas"""
    model = TestSuite
    template_name = 'testing_dashboard/suite_list.html'
    context_object_name = 'suites'
    ordering = ['name']
    
    def get_queryset(self):
        return super().get_queryset().annotate(
            total_tests=Count('testcase'),
            recent_tests=Count('testcase', filter=Q(testcase__run__started_at__gte=timezone.now() - timedelta(days=7)))
        )


def dashboard_stats_api(request):
    """API endpoint para estadísticas dinámicas"""
    days = int(request.GET.get('days', 7))
    start_date = timezone.now() - timedelta(days=days)
    
    # Runs por día
    daily_runs = TestRun.objects.filter(
        started_at__gte=start_date
    ).extra({
        'day': 'date(started_at)'
    }).values('day').annotate(
        count=Count('id'),
        success_rate=Avg('passed_tests') * 100 / Avg('total_tests')
    ).order_by('day')
    
    # Convertir a formato para Chart.js
    labels = []
    run_counts = []
    success_rates = []
    
    for item in daily_runs:
        labels.append(item['day'].strftime('%d/%m'))
        run_counts.append(item['count'])
        success_rates.append(round(item['success_rate'] or 0, 2))
    
    return JsonResponse({
        'labels': labels,
        'run_counts': run_counts,
        'success_rates': success_rates
    })
