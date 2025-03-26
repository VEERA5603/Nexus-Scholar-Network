from django.urls import path
from .views.views import Studentdashboard,VisualDetails
from .views.views1 import PersonalInformationView,AddressView,CopyAddressView,GetPersonalInfoView
from .views.views2 import AcademicsView,RejoinView,ScholarView
from .views.views3 import PersonalDocumentsView,PersonalDDView
from .views.views4 import ExaminationView,MarksheetDetails,DiplomaMarksheetDetails
from .views.views5 import SchoolDetails,DiplomaDetails
from .views.views6 import BreifView,HostellarView,BankView
from.views.views7 import ReportDetails
from .views.views8 import DocumentDashboardView
urlpatterns = [
    path('student/dash/', Studentdashboard.as_view(), name='student-dashboard'),
    path('student/dashboard/news/', Studentdashboard.as_view(), name='dashboard-news-partial'),
    path('visual-details/', VisualDetails.as_view(), name='visual-details'),
    path('personal-information/', PersonalInformationView.as_view(), name='personal_information'),
    path('breif-details/', BreifView.as_view(), name='breif'),
    path('bank-details/', BankView.as_view(), name='bank'),
    path('host-details/', HostellarView.as_view(), name='host'),
    path('rejoin-details/', RejoinView.as_view(), name='rejoin'),
    path('address/', AddressView.as_view(), name='address'),
    path('copy-address/', CopyAddressView.as_view(), name='copy_address'),
    path('get-personal-info/<int:roll_number>/', GetPersonalInfoView.as_view(), name='get_personal_info'),
    path('academics/', AcademicsView.as_view(), name='academics'),
    path('scholarship/', ScholarView.as_view(), name='scholar'),
    path('documents/', PersonalDocumentsView.as_view(), name='personal-documents'),
    path('download/', PersonalDDView.as_view(), name='download'),
    path('examination/', ExaminationView.as_view(), name='examination'),
    path('marksheets/', MarksheetDetails.as_view(), name='marksheet-details'),
    path('marksheets/<int:marksheet_id>/', MarksheetDetails.as_view(), name='marksheet-details'),
    path('dmarksheets/', DiplomaMarksheetDetails.as_view(), name='dmarksheet-details'),
    path('dmarksheets/<int:marksheet_id>/', DiplomaMarksheetDetails.as_view(), name='dmarksheet-details'),
    path('school-details/', SchoolDetails.as_view(), name='school-details'),
    path('diploma-details/', DiplomaDetails.as_view(), name='diploma-details'),
    path('report-details/', ReportDetails.as_view(), name='report-details'),
    path('document-dashboard/', DocumentDashboardView.as_view(), name='document-dashboard'),
]
