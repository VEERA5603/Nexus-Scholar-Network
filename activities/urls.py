from django.urls import path
from . import views

urlpatterns = [
    path('ac/', views.activities_by_year, name='activities_list'),
    path('year/<str:year>/', views.year_activities, name='year_activities'),
    path('activity/<int:pk>/', views.activity_detail, name='activity_detail'),
]