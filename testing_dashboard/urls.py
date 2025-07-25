from django.urls import path
from . import views

app_name = 'testing_dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('runs/', views.TestRunListView.as_view(), name='run_list'),
    path('runs/<int:pk>/', views.TestRunDetailView.as_view(), name='run_detail'),
    path('suites/', views.TestSuiteListView.as_view(), name='suite_list'),
    path('api/stats/', views.dashboard_stats_api, name='stats_api'),
]
