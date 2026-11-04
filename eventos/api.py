from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Atividade, Evento, InscricaoAtividade, InscricaoEvento, Sala
from .permissions import EhOrganizador, EhOrganizadorDoObjeto
from .serializers import (
    AtividadeIdSerializer,
    AtividadeSerializer,
    EventoIdSerializer,
    EventoProgramacaoSerializer,
    EventoSerializer,
    InscricaoAtividadeSerializer,
    InscricaoEventoSerializer,
    SalaSerializer,
)
from .services import (
    cancelar_atividade,
    cancelar_evento,
    inscrever_na_atividade,
    inscrever_no_evento,
)


def _resposta_erro(erro):
    mensagens = erro.message_dict if hasattr(erro, "message_dict") else erro.messages
    return Response({"erros": mensagens}, status=status.HTTP_400_BAD_REQUEST)


class SalaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Sala.objects.all()
    serializer_class = SalaSerializer
    permission_classes = [AllowAny]


class EventoViewSet(viewsets.ModelViewSet):
    serializer_class = EventoSerializer
    queryset = Evento.objects.select_related("organizador")
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nome", "descricao"]
    ordering_fields = ["data_inicio", "nome"]
    ordering = ["data_inicio"]

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            classes = [AllowAny]
        elif self.action == "create":
            classes = [IsAuthenticated, EhOrganizador]
        else:
            classes = [IsAuthenticated, EhOrganizador, EhOrganizadorDoObjeto]
        return [classe() for classe in classes]

class AtividadeViewSet(viewsets.ModelViewSet):
    serializer_class = AtividadeSerializer
    queryset = Atividade.objects.select_related("evento", "sala").prefetch_related("inscricoes")
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["titulo", "descricao"]
    ordering_fields = ["inicio"]
    ordering = ["inicio"]

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            classes = [AllowAny]
        elif self.action == "create":
            classes = [IsAuthenticated, EhOrganizador]
        else:
            classes = [IsAuthenticated, EhOrganizador, EhOrganizadorDoObjeto]
        return [classe() for classe in classes]

    def perform_create(self, serializer):
        evento = serializer.validated_data["evento"]
        if evento.organizador_id != self.request.user.id:
            raise PermissionDenied("Você não pode criar atividade em evento de outro organizador.")
        serializer.save()


@extend_schema(responses={200: EventoProgramacaoSerializer})
@api_view(["GET"])
@permission_classes([AllowAny])
def programacao_evento_api(request, pk):
    evento = get_object_or_404(
        Evento.objects.select_related("organizador").prefetch_related(
            "atividades__sala",
            "atividades__inscricoes",
        ),
        pk=pk,
    )
    serializer = EventoProgramacaoSerializer(evento, context={"request": request})
    return Response(serializer.data)


@extend_schema(request=EventoIdSerializer, responses={201: InscricaoEventoSerializer})
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def inscrever_evento_api(request):
    entrada = EventoIdSerializer(data=request.data)
    entrada.is_valid(raise_exception=True)
    try:
        inscricao = inscrever_no_evento(request.user, entrada.validated_data["evento"].pk)
    except DjangoValidationError as erro:
        return _resposta_erro(erro)
    return Response(InscricaoEventoSerializer(inscricao).data, status=status.HTTP_201_CREATED)


@extend_schema(request=None, responses={204: None})
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def cancelar_evento_api(request, pk):
    get_object_or_404(InscricaoEvento, pk=pk)
    try:
        cancelar_evento(request.user, pk)
    except DjangoPermissionDenied as erro:
        raise PermissionDenied(str(erro)) from erro
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(request=AtividadeIdSerializer, responses={201: InscricaoAtividadeSerializer})
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def inscrever_atividade_api(request):
    entrada = AtividadeIdSerializer(data=request.data)
    entrada.is_valid(raise_exception=True)
    try:
        inscricao = inscrever_na_atividade(request.user, entrada.validated_data["atividade"].pk)
    except DjangoValidationError as erro:
        return _resposta_erro(erro)
    return Response(InscricaoAtividadeSerializer(inscricao).data, status=status.HTTP_201_CREATED)


@extend_schema(request=None, responses={204: None})
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def cancelar_atividade_api(request, pk):
    get_object_or_404(InscricaoAtividade, pk=pk)
    try:
        cancelar_atividade(request.user, pk)
    except DjangoPermissionDenied as erro:
        raise PermissionDenied(str(erro)) from erro
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(responses={200: InscricaoAtividadeSerializer(many=True)})
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def minha_agenda_api(request):
    inscricoes = InscricaoAtividade.objects.filter(
        inscricao_evento__participante=request.user
    ).select_related("atividade__evento", "atividade__sala").order_by("atividade__inicio")
    return Response(InscricaoAtividadeSerializer(inscricoes, many=True).data)
