from django.urls import path
from .views import StudentLogin, StaffLogin, Register, Profile, logout_user, home,get_nasa_apod, UpdatePassword, FacultyListView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .import views
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', home, name='home'),
    path('faculty_list/', FacultyListView.as_view(), name='faculty_list'),
    path('get_nasa_apod/', views.get_nasa_apod, name='get_nasa_apod'),
    path('student/login/', StudentLogin.as_view(), name='student-login'),
    path('staff/login/', StaffLogin.as_view(), name='staff-login'),
    path('register/', Register.as_view(), name='register'),
    # New path for password update
    path('update-password/', UpdatePassword.as_view(), name='update-password'),
    path('profile/', Profile.as_view(), name='profile'),
    path('logout/', logout_user, name='logout'),
    # JWT Token obtain route (for login and token generation)
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # JWT Token refresh route (for refreshing access token)
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('get-announcements/', views.get_announcements, name='get_announcements'),
    path('events/', views.event_list, name='event_list'),
    path('events/<int:event_id>/images/', views.event_images, name='event_images'),
   
]



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
