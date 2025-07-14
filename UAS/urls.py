from django.contrib import admin
from django.urls import path, include
from frontend import views as frontend_views

urlpatterns = [
    path('super-admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', frontend_views.home_page, name='home'),  # ⬅️ Halaman Company Profile
    path('login/', frontend_views.login_page, name='login'),
    path('logout/', frontend_views.logout_view, name='logout'),
    path('', include('frontend.urls')),  # ini tetap, tapi pastikan tidak override atasnya
]
