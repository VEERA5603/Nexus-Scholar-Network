from django.urls import path
from .views.views import StaffDashboard, Visualization, VisualizationData
from .views.views1 import FacultyView, ResearchGuidanceview,AcademicEventView, ResearchProjectView, PublicationView, AwardView, PublicationCategoryView
from .views.views2 import StaffAttendanceManagement


urlpatterns = [
    path('staff/dash/', StaffDashboard.as_view(), name='staff-dashboard'),
    path('faculty/', FacultyView.as_view(), name='faculty'),
    path('publication-category/', PublicationCategoryView.as_view(), name='publication-category'),
    path('RG/', ResearchGuidanceview.as_view(), name='RG'),
    path('AE/', AcademicEventView.as_view(), name='AE'),
    path('RP/', ResearchProjectView.as_view(), name='RP'),
    path('publication/', PublicationView.as_view(), name='publication'),
    path('awards/', AwardView.as_view(), name='awards'),
    path('visualization/', Visualization.as_view(), name='visualization'),
    path('visualization/data/<str:data_type>/', VisualizationData.as_view(), name='visualization-data'),
   # path('attendance/', AttendanceView.as_view(), name='attendance'),
   # path('get-students/', StudentListView.as_view(), name='get_students'),
   # path('save-attendance/', SaveAttendanceView.as_view(), name='save_attendance'),
    
    path('staff/attendance/', StaffAttendanceManagement.as_view(), name='staff-attendance'),
    
   
]

