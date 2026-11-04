from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from eventos.views import CadastroView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("eventos.api_urls")),
    path("contas/entrar/", auth_views.LoginView.as_view(), name="login"),
    path("contas/sair/", auth_views.LogoutView.as_view(), name="logout"),
    path("contas/cadastro/", CadastroView.as_view(), name="cadastro"),
    path("", include("eventos.urls")),
]
