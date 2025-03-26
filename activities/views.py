from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404
from .models import AcademicYear, DepartmentActivity

def activities_by_year(request):
    academic_years = AcademicYear.objects.all().order_by('-year')
    current_year = AcademicYear.objects.filter(is_current=True).first()
    
    context = {
        'academic_years': academic_years,
        'current_year': current_year,
    }
    return render(request, 'activities/activities_list.html', context)

def year_activities(request, year):
    academic_year = get_object_or_404(AcademicYear, year=year)
    activities = DepartmentActivity.objects.filter(academic_year=academic_year).order_by('-date')
    
    context = {
        'academic_year': academic_year,
        'activities': activities,
    }
    return render(request, 'activities/year_activities.html', context)

def activity_detail(request, pk):
    activity = get_object_or_404(DepartmentActivity, pk=pk)
    
    context = {
        'activity': activity,
    }
    return render(request, 'activities/activity_detail.html', context)