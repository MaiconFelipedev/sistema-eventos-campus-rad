from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from . import api


app_name = "api"

router = DefaultRouter()
router.register("salas", api.SalaViewSet, basename="sala")
router.register("eventos", api.EventoViewSet, basename="evento")
router.register("atividades", api.AtividadeViewSet, basename="atividade")

urlpatterns = [
    path(
        "eventos/<int:pk>/programacao/",
        api.programacao_evento_api,
        name="evento-programacao",
    ),
    path("", include(router.urls)),
    path("token/", obtain_auth_token, name="token"),
    path("inscricoes/eventos/", api.inscrever_evento_api, name="inscrever-evento"),
    path(
        "inscricoes/eventos/<int:pk>/",
        api.cancelar_evento_api,
        name="cancelar-evento",
    ),
    path(
        "inscricoes/atividades/",
        api.inscrever_atividade_api,
        name="inscrever-atividade",
    ),
    path(
        "inscricoes/atividades/<int:pk>/",
        api.cancelar_atividade_api,
        name="cancelar-atividade",
    ),
    path("minha-agenda/", api.minha_agenda_api, name="minha-agenda"),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(url_name="api:schema"),
        name="docs",
    ),
]
