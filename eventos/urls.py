from django.urls import path

from . import views


app_name = "eventos"

urlpatterns = [
    path("", views.EventoListView.as_view(), name="lista"),
    path("eventos/novo/", views.EventoCreateView.as_view(), name="evento_criar"),
    path("eventos/<int:pk>/", views.EventoDetailView.as_view(), name="detalhe"),
    path("eventos/<int:pk>/editar/", views.EventoUpdateView.as_view(), name="evento_editar"),
    path("eventos/<int:pk>/excluir/", views.EventoDeleteView.as_view(), name="evento_excluir"),
    path("eventos/<int:pk>/inscrever/", views.inscrever_evento_view, name="evento_inscrever"),
    path("eventos/<int:pk>/cancelar/", views.cancelar_evento_view, name="evento_cancelar"),
    path(
        "eventos/<int:evento_pk>/atividades/nova/",
        views.AtividadeCreateView.as_view(),
        name="atividade_criar",
    ),
    path(
        "atividades/<int:pk>/editar/",
        views.AtividadeUpdateView.as_view(),
        name="atividade_editar",
    ),
    path(
        "atividades/<int:pk>/excluir/",
        views.AtividadeDeleteView.as_view(),
        name="atividade_excluir",
    ),
    path(
        "atividades/<int:pk>/inscrever/",
        views.inscrever_atividade_view,
        name="atividade_inscrever",
    ),
    path(
        "atividades/<int:pk>/cancelar/",
        views.cancelar_atividade_view,
        name="atividade_cancelar",
    ),
    path(
        "atividades/<int:pk>/espera/",
        views.entrar_espera_view,
        name="espera_entrar",
    ),
    path("espera/<int:pk>/sair/", views.sair_espera_view, name="espera_sair"),
    path("minha-agenda/", views.MinhaAgendaView.as_view(), name="agenda"),
    path(
        "eventos/<int:pk>/painel/",
        views.PainelOrganizadorView.as_view(),
        name="painel",
    ),
]
