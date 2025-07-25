import json
import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from testing_dashboard.models import TestSuite, TestRun, TestCase
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Importa resultados de Playwright desde archivo JSON'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='pw_tests/test-results/results.json',
            help='Ruta al archivo JSON de resultados de Playwright'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Username del usuario que ejecutó las pruebas'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        username = options.get('user')
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            raise CommandError(f'El archivo {file_path} no existe')
        
        # Obtener usuario si se especificó
        user = None
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Usuario {username} no encontrado, continuando sin usuario')
                )
        
        # Leer el archivo JSON
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise CommandError(f'Error al parsear JSON: {e}')
        
        self.stdout.write('🚀 Iniciando importación de resultados de Playwright...')
        
        # Crear TestRun
        test_run = self.create_test_run(data, user)
        self.stdout.write(f'✅ TestRun creado: {test_run}')
        
        # Procesar suites y tests
        total_imported = 0
        for suite_data in data.get('suites', []):
            suite = self.get_or_create_suite(suite_data)
            imported_count = self.process_suite_tests(suite, suite_data, test_run)
            total_imported += imported_count
        
        # Actualizar estadísticas del run
        self.update_run_stats(test_run, data)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'🎉 Importación completada: {total_imported} tests importados para el run {test_run.id}'
            )
        )

    def create_test_run(self, data, user):
        """Crea un nuevo TestRun basado en los datos JSON"""
        stats = data.get('stats', {})
        config = data.get('config', {})
        
        # Parsear fecha de inicio
        start_time_str = stats.get('startTime')
        if start_time_str:
            # Formato: "2025-07-25T01:27:10.160Z"
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        else:
            start_time = timezone.now()
        
        # Determinar status basado en estadísticas
        unexpected = stats.get('unexpected', 0)
        expected = stats.get('expected', 0)
        
        if unexpected > 0:
            status = 'failed'
        elif expected > 0:
            status = 'passed'
        else:
            status = 'error'
        
        test_run = TestRun.objects.create(
            executed_by=user,
            status=status,
            started_at=start_time,
            finished_at=start_time,  # Se actualizará después
            duration_ms=int(stats.get('duration', 0)),
            total_tests=expected + unexpected + stats.get('skipped', 0),
            passed_tests=expected,
            failed_tests=unexpected,
            skipped_tests=stats.get('skipped', 0),
            playwright_config=config
        )
        
        return test_run

    def get_or_create_suite(self, suite_data):
        """Obtiene o crea un TestSuite"""
        suite_name = suite_data.get('title', 'Unknown Suite')
        file_path = suite_data.get('file', 'unknown.spec.ts')
        
        suite, created = TestSuite.objects.get_or_create(
            name=suite_name,
            file_path=file_path,
            defaults={
                'description': f'Suite de pruebas para {suite_name}'
            }
        )
        
        if created:
            self.stdout.write(f'📁 Suite creado: {suite_name}')
        
        return suite

    def process_suite_tests(self, suite, suite_data, test_run):
        """Procesa todos los tests de una suite"""
        imported_count = 0
        
        for spec in suite_data.get('specs', []):
            for test_data in spec.get('tests', []):
                self.create_test_case(suite, test_data, test_run)
                imported_count += 1
        
        return imported_count

    def create_test_case(self, suite, test_data, test_run):
        """Crea un TestCase individual"""
        # Obtener el primer resultado (pueden haber múltiples por reintentos)
        results = test_data.get('results', [])
        if not results:
            return
        
        result = results[0]  # Primer resultado
        
        # Parsear fecha de inicio
        start_time_str = result.get('startTime')
        if start_time_str:
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        else:
            start_time = timezone.now()
        
        # Determinar browser del projectName
        project_name = test_data.get('projectName', 'chromium').lower()
        browser = project_name if project_name in ['chromium', 'firefox', 'webkit'] else 'chromium'
        
        # Obtener errores si los hay
        errors = result.get('errors', [])
        error_message = ''
        error_stack = ''
        if errors:
            error_message = errors[0].get('message', '')
            error_stack = errors[0].get('stack', '')
        
        test_case = TestCase.objects.create(
            run=test_run,
            suite=suite,
            title=test_data.get('title', 'Unknown Test'),
            status=result.get('status', 'unknown'),
            browser=browser,
            duration_ms=result.get('duration', 0),
            retry_count=result.get('retry', 0),
            error_message=error_message,
            error_stack=error_stack,
            attachments=result.get('attachments', []),
            annotations=result.get('annotations', []),
            worker_index=result.get('workerIndex'),
            started_at=start_time
        )
        
        return test_case

    def update_run_stats(self, test_run, data):
        """Actualiza las estadísticas finales del run"""
        stats = data.get('stats', {})
        
        # Calcular tiempo de finalización
        start_time_str = stats.get('startTime')
        duration_ms = stats.get('duration', 0)
        
        if start_time_str:
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            finish_time = start_time
            if duration_ms:
                from datetime import timedelta
                finish_time = start_time + timedelta(milliseconds=duration_ms)
            test_run.finished_at = finish_time
        
        # Actualizar duración
        test_run.duration_ms = int(duration_ms)
        test_run.save()
        
        self.stdout.write(f'📊 Estadísticas actualizadas: {test_run.success_rate}% de éxito')
