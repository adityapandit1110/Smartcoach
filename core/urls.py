from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomLoginView

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('report-defect/', views.report_defect, name='report_defect'),
    path('get-coaches/<int:train_id>/', views.get_coaches, name='get_coaches'),
    path('my-defects/', views.my_defects, name='my_defects'),
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('add-train/', views.add_train, name='add_train'),
    path('delete-train/<int:train_id>/', views.delete_train, name='delete_train'),
    path('add-coach/<int:train_id>/', views.add_coach, name='add_coach'),
    path('delete-coach/<int:coach_id>/', views.delete_coach, name='delete_coach'),
    path('register/', views.register_passenger, name='register'),
    path('passenger-dashboard/', views.passenger_dashboard, name='passenger_dashboard'),
    path('add-staff/', views.add_maintenance_staff, name='add_maintenance_staff'),
    


]
