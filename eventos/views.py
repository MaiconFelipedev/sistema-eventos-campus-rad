from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Prefetch
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    UpdateView,
)

from .forms import AtividadeForm, CadastroForm, EventoForm
from .models import Atividade, Evento, InscricaoAtividade, InscricaoEvento, ListaEspera
from .permissions import OrganizadorRequiredMixin
from .services import (
    cancelar_atividade,
    cancelar_evento,
    entrar_na_lista_espera,
    existe_conflito_agenda,
    inscrever_na_atividade,
    inscrever_no_evento,
    sair_da_lista_espera,
)


def _mostrar_erro(request, erro):
    texto = "; ".join(erro.messages) if hasattr(erro, "messages") else str(erro)
    messages.error(request, texto)


class CadastroView(FormView):
    template_name = "registration/cadastro.html"
    form_class = CadastroForm
    success_url = reverse_lazy("eventos:lista")

    def form_valid(self, form):
        usuario = form.save()
        login(self.request, usuario)
        messages.success(self.request, "Cadastro realizado. Você entrou como participante.")
        return super().form_valid(form)


class EventoListView(ListView):
    model = Evento
    template_name = "eventos/evento_list.html"
    context_object_name = "eventos"
    queryset = Evento.objects.select_related("organizador").prefetch_related("atividades__sala")


class EventoDetailView(DetailView):
    model = Evento
    template_name = "eventos/evento_detail.html"
    context_object_name = "evento"
    queryset = Evento.objects.select_related("organizador").prefetch_related("atividades__sala")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        usuario = self.request.user
        inscricao_evento = None
        if usuario.is_authenticated:
            inscricao_evento = InscricaoEvento.objects.filter(
                evento=self.object,
                participante=usuario,
            ).first()

        programacao = []
        for atividade in self.object.atividades.all():
            inscricao = None
            espera = None
            conflito = False
            if inscricao_evento:
                inscricao = InscricaoAtividade.objects.filter(
                    inscricao_evento=inscricao_evento,
                    atividade=atividade,
                ).first()
                espera = ListaEspera.objects.filter(
                    inscricao_evento=inscricao_evento,
                    atividade=atividade,
                ).first()
                if not inscricao:
                    conflito = existe_conflito_agenda(usuario, atividade)
            programacao.append(
                {
                    "atividade": atividade,
                    "vagas": atividade.vagas_restantes,
                    "lotada": atividade.lotada,
                    "inscricao": inscricao,
                    "espera": espera,
                    "conflito": conflito,
                    "pode_inscrever": bool(
                        inscricao_evento and not inscricao and not espera and not atividade.lotada and not conflito
                    ),
                    "pode_esperar": bool(
                        inscricao_evento and not inscricao and not espera and atividade.lotada
                    ),
                }
            )

        contexto.update(
            {
                "inscricao_evento": inscricao_evento,
                "programacao": programacao,
                "evento_do_usuario": usuario.is_authenticated
                and self.object.organizador_id == usuario.id,
            }
        )
        return contexto


class EventoOwnerQuerysetMixin:
    def get_queryset(self):
        return Evento.objects.filter(organizador=self.request.user)


class EventoCreateView(OrganizadorRequiredMixin, CreateView):
    model = Evento
    form_class = EventoForm
    template_name = "eventos/form.html"

    def form_valid(self, form):
        form.instance.organizador = self.request.user
        messages.success(self.request, "Evento criado com sucesso.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("eventos:detalhe", args=[self.object.pk])


class EventoUpdateView(OrganizadorRequiredMixin, EventoOwnerQuerysetMixin, UpdateView):
    model = Evento
    form_class = EventoForm
    template_name = "eventos/form.html"

    def form_valid(self, form):
        messages.success(self.request, "Evento atualizado com sucesso.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("eventos:detalhe", args=[self.object.pk])


class EventoDeleteView(OrganizadorRequiredMixin, EventoOwnerQuerysetMixin, DeleteView):
    model = Evento
    template_name = "eventos/confirm_delete.html"
    success_url = reverse_lazy("eventos:lista")


class AtividadeOwnerQuerysetMixin:
    def get_queryset(self):
        return Atividade.objects.filter(evento__organizador=self.request.user).select_related("evento")


class AtividadeCreateView(OrganizadorRequiredMixin, CreateView):
    model = Atividade
    form_class = AtividadeForm
    template_name = "eventos/form.html"

    def dispatch(self, request, *args, **kwargs):
        self.evento = get_object_or_404(Evento, pk=kwargs["evento_pk"])
        if self.evento.organizador_id != request.user.id:
            return HttpResponseForbidden("Você não pode alterar um evento de outro organizador.")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["evento"] = self.evento
        return kwargs

    def form_valid(self, form):
        form.instance.evento = self.evento
        messages.success(self.request, "Atividade criada com sucesso.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("eventos:detalhe", args=[self.evento.pk])


class AtividadeUpdateView(OrganizadorRequiredMixin, AtividadeOwnerQuerysetMixin, UpdateView):
    model = Atividade
    form_class = AtividadeForm
    template_name = "eventos/form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["evento"] = self.object.evento
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Atividade atualizada com sucesso.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("eventos:detalhe", args=[self.object.evento_id])


class AtividadeDeleteView(OrganizadorRequiredMixin, AtividadeOwnerQuerysetMixin, DeleteView):
    model = Atividade
    template_name = "eventos/confirm_delete.html"

    def get_success_url(self):
        return reverse("eventos:detalhe", args=[self.object.evento_id])


@login_required
@require_POST
def inscrever_evento_view(request, pk):
    try:
        inscrever_no_evento(request.user, pk)
        messages.success(request, "Inscrição no evento realizada.")
    except ValidationError as erro:
        _mostrar_erro(request, erro)
    return redirect("eventos:detalhe", pk=pk)


@login_required
@require_POST
def inscrever_atividade_view(request, pk):
    atividade = get_object_or_404(Atividade, pk=pk)
    try:
        inscrever_na_atividade(request.user, pk)
        messages.success(request, "Atividade adicionada à sua agenda.")
    except ValidationError as erro:
        _mostrar_erro(request, erro)
    return redirect("eventos:detalhe", pk=atividade.evento_id)


@login_required
@require_POST
def entrar_espera_view(request, pk):
    atividade = get_object_or_404(Atividade, pk=pk)
    try:
        espera = entrar_na_lista_espera(request.user, pk)
        messages.success(request, f"Você entrou na lista de espera, posição {espera.posicao}.")
    except ValidationError as erro:
        _mostrar_erro(request, erro)
    return redirect("eventos:detalhe", pk=atividade.evento_id)


@login_required
@require_POST
def cancelar_atividade_view(request, pk):
    inscricao = get_object_or_404(InscricaoAtividade, pk=pk)
    evento_id = inscricao.atividade.evento_id
    cancelar_atividade(request.user, pk)
    messages.success(request, "Inscrição na atividade cancelada.")
    return redirect(request.POST.get("next") or reverse("eventos:detalhe", args=[evento_id]))


@login_required
@require_POST
def cancelar_evento_view(request, pk):
    inscricao = get_object_or_404(InscricaoEvento, pk=pk)
    evento_id = inscricao.evento_id
    cancelar_evento(request.user, pk)
    messages.success(request, "Inscrição no evento e nas atividades cancelada.")
    return redirect("eventos:detalhe", pk=evento_id)


@login_required
@require_POST
def sair_espera_view(request, pk):
    espera = get_object_or_404(ListaEspera, pk=pk)
    evento_id = espera.atividade.evento_id
    sair_da_lista_espera(request.user, pk)
    messages.success(request, "Você saiu da lista de espera.")
    return redirect(request.POST.get("next") or reverse("eventos:detalhe", args=[evento_id]))


class MinhaAgendaView(LoginRequiredMixin, ListView):
    model = InscricaoAtividade
    template_name = "eventos/minha_agenda.html"
    context_object_name = "inscricoes"

    def get_queryset(self):
        return InscricaoAtividade.objects.filter(
            inscricao_evento__participante=self.request.user
        ).select_related("atividade__evento", "atividade__sala").order_by("atividade__inicio")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["esperas"] = ListaEspera.objects.filter(
            inscricao_evento__participante=self.request.user
        ).select_related("atividade__evento", "atividade__sala").order_by("atividade__inicio")
        return contexto


class PainelOrganizadorView(OrganizadorRequiredMixin, EventoOwnerQuerysetMixin, DetailView):
    model = Evento
    template_name = "eventos/painel_organizador.html"
    context_object_name = "evento"

    def get_queryset(self):
        participantes = InscricaoAtividade.objects.select_related(
            "inscricao_evento__participante"
        ).order_by("inscricao_evento__participante__username")
        return super().get_queryset().prefetch_related(
            Prefetch("atividades__inscricoes", queryset=participantes),
            "atividades__sala",
        )
