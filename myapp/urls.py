from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
 path('donor_statistics/', views.donor_statistics, name='donor_statistics'), 
    # Authentication
    path('register/donor/', views.donor_register, name='donor_register'),
    path('register/orphanage/', views.orphanage_register, name='orphanage_register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
     path('donor/profile/', views.donor_profile, name='donor_profile'),
    path('orphanage/profile/', views.orphanage_profile, name='orphanage_profile'),
    # Dashboards
    path('view_proofs/<int:need_id>/', views.view_proofs, name='view_proofs'),
        path('need/<int:need_id>/', views.need_details, name='need_details'),
    path('donor/dashboard/', views.donor_dashboard, name='donor_dashboard'),
    path('orphanage/dashboard/', views.orphanage_dashboard, name='orphanage_dashboard'),
    path('donate/<int:need_id>/', views.donate, name='donate'),
    # Orphanage functions
    path('orphanage/post_need/', views.post_need, name='post_need'),
    path('orphanage/upload_proof/<int:need_id>/', views.upload_proof, name='upload_proof'),
    path('donor/edit-profile/', views.edit_profile, name='edit_profile'),

]
