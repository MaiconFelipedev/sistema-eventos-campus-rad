from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction

from .models import Atividade, Evento, InscricaoAtividade, InscricaoEvento, ListaEspera


def existe_conflito_agenda(participante, atividade, excluir_inscricao=None):
    conflitos = InscricaoAtividade.objects.filter(
        inscricao_evento__participante=participante,
        atividade__inicio__lt=atividade.fim,
        atividade__fim__gt=atividade.inicio,
    )
    if excluir_inscricao:
        conflitos = conflitos.exclude(pk=excluir_inscricao.pk)
    return conflitos.exists()


@transaction.atomic
def inscrever_no_evento(participante, evento_id):
    evento = Evento.objects.select_for_update().get(pk=evento_id)
    if not evento.inscricoes_abertas:
        raise ValidationError("As inscrições deste evento estão fechadas.")
    try:
        inscricao = InscricaoEvento.objects.create(evento=evento, participante=participante)
    except IntegrityError as erro:
        raise ValidationError("Você já está inscrito neste evento.") from erro
    return inscricao


@transaction.atomic
def inscrever_na_atividade(participante, atividade_id):
    atividade = Atividade.objects.select_for_update().select_related("evento", "sala").get(
        pk=atividade_id
    )
    try:
        inscricao_evento = InscricaoEvento.objects.select_for_update().get(
            evento=atividade.evento,
            participante=participante,
        )
    except InscricaoEvento.DoesNotExist as erro:
        raise ValidationError("Inscreva-se no evento antes de escolher uma atividade.") from erro

    if InscricaoAtividade.objects.filter(
        inscricao_evento=inscricao_evento,
        atividade=atividade,
    ).exists():
        raise ValidationError("Você já está inscrito nesta atividade.")

    if atividade.inscricoes.count() >= atividade.sala.capacidade:
        raise ValidationError("A atividade está lotada. Use a lista de espera.")

    if existe_conflito_agenda(participante, atividade):
        raise ValidationError("Esta atividade conflita com outra atividade da sua agenda.")

    espera = ListaEspera.objects.filter(
        inscricao_evento=inscricao_evento,
        atividade=atividade,
    ).first()
    if espera:
        espera.delete()

    return InscricaoAtividade.objects.create(
        inscricao_evento=inscricao_evento,
        atividade=atividade,
    )


@transaction.atomic
def entrar_na_lista_espera(participante, atividade_id):
    atividade = Atividade.objects.select_for_update().select_related("evento", "sala").get(
        pk=atividade_id
    )
    try:
        inscricao_evento = InscricaoEvento.objects.get(
            evento=atividade.evento,
            participante=participante,
        )
    except InscricaoEvento.DoesNotExist as erro:
        raise ValidationError("Inscreva-se no evento antes de entrar na lista de espera.") from erro

    if atividade.inscricoes.count() < atividade.sala.capacidade:
        raise ValidationError("Ainda existem vagas; faça a inscrição normalmente.")
    if InscricaoAtividade.objects.filter(
        inscricao_evento=inscricao_evento,
        atividade=atividade,
    ).exists():
        raise ValidationError("Você já está inscrito nesta atividade.")
    try:
        return ListaEspera.objects.create(
            inscricao_evento=inscricao_evento,
            atividade=atividade,
        )
    except IntegrityError as erro:
        raise ValidationError("Você já está na lista de espera desta atividade.") from erro


def promover_primeiro_elegivel(atividade):
    if atividade.inscricoes.count() >= atividade.sala.capacidade:
        return None
    for espera in atividade.lista_espera.select_related("inscricao_evento__participante"):
        participante = espera.inscricao_evento.participante
        if existe_conflito_agenda(participante, atividade):
            continue
        inscricao = InscricaoAtividade.objects.create(
            inscricao_evento=espera.inscricao_evento,
            atividade=atividade,
        )
        espera.delete()
        return inscricao
    return None


@transaction.atomic
def cancelar_atividade(participante, inscricao_id):
    try:
        inscricao = InscricaoAtividade.objects.select_for_update().select_related(
            "atividade__sala",
            "inscricao_evento",
        ).get(pk=inscricao_id)
    except InscricaoAtividade.DoesNotExist as erro:
        raise PermissionDenied("Inscrição não encontrada para este participante.") from erro
    if inscricao.inscricao_evento.participante_id != participante.id:
        raise PermissionDenied("Você não pode cancelar a inscrição de outra pessoa.")
    atividade = inscricao.atividade
    inscricao.delete()
    promover_primeiro_elegivel(atividade)


@transaction.atomic
def cancelar_evento(participante, inscricao_id):
    try:
        inscricao = InscricaoEvento.objects.select_for_update().get(pk=inscricao_id)
    except InscricaoEvento.DoesNotExist as erro:
        raise PermissionDenied("Inscrição não encontrada para este participante.") from erro
    if inscricao.participante_id != participante.id:
        raise PermissionDenied("Você não pode cancelar a inscrição de outra pessoa.")
    atividades = list(
        Atividade.objects.filter(inscricoes__inscricao_evento=inscricao).select_related("sala")
    )
    inscricao.delete()
    for atividade in atividades:
        promover_primeiro_elegivel(atividade)


@transaction.atomic
def sair_da_lista_espera(participante, espera_id):
    try:
        espera = ListaEspera.objects.select_for_update().select_related("inscricao_evento").get(
            pk=espera_id
        )
    except ListaEspera.DoesNotExist as erro:
        raise PermissionDenied("Entrada na fila não encontrada.") from erro
    if espera.inscricao_evento.participante_id != participante.id:
        raise PermissionDenied("Você não pode alterar a lista de espera de outra pessoa.")
    espera.delete()
