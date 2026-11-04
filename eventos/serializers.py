from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Atividade, Evento, InscricaoAtividade, InscricaoEvento, Sala


def _erros_django(erro):
    if hasattr(erro, "message_dict"):
        return erro.message_dict
    return {"non_field_errors": erro.messages}


class SalaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sala
        fields = ["id", "nome", "bloco", "capacidade"]


class AtividadeSerializer(serializers.ModelSerializer):
    sala_nome = serializers.CharField(source="sala.nome", read_only=True)
    vagas_restantes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Atividade
        fields = [
            "id",
            "evento",
            "titulo",
            "tipo",
            "descricao",
            "responsavel",
            "sala",
            "sala_nome",
            "inicio",
            "fim",
            "vagas_restantes",
        ]

    def create(self, validated_data):
        atividade = Atividade(**validated_data)
        try:
            atividade.full_clean()
        except DjangoValidationError as erro:
            raise serializers.ValidationError(_erros_django(erro)) from erro
        atividade.save()
        return atividade

    def update(self, instance, validated_data):
        for campo, valor in validated_data.items():
            setattr(instance, campo, valor)
        try:
            instance.full_clean()
        except DjangoValidationError as erro:
            raise serializers.ValidationError(_erros_django(erro)) from erro
        instance.save()
        return instance


class EventoSerializer(serializers.ModelSerializer):
    organizador = serializers.CharField(source="organizador.username", read_only=True)

    class Meta:
        model = Evento
        fields = [
            "id",
            "nome",
            "descricao",
            "data_inicio",
            "data_fim",
            "inscricoes_abertas",
            "organizador",
        ]

    def create(self, validated_data):
        evento = Evento(
            organizador=self.context["request"].user,
            **validated_data,
        )
        try:
            evento.full_clean()
        except DjangoValidationError as erro:
            raise serializers.ValidationError(_erros_django(erro)) from erro
        evento.save()
        return evento

    def update(self, instance, validated_data):
        for campo, valor in validated_data.items():
            setattr(instance, campo, valor)
        try:
            instance.full_clean()
        except DjangoValidationError as erro:
            raise serializers.ValidationError(_erros_django(erro)) from erro
        instance.save()
        return instance


class EventoProgramacaoSerializer(EventoSerializer):
    atividades = AtividadeSerializer(many=True, read_only=True)

    class Meta(EventoSerializer.Meta):
        fields = EventoSerializer.Meta.fields + ["atividades"]


class InscricaoEventoSerializer(serializers.ModelSerializer):
    evento_nome = serializers.CharField(source="evento.nome", read_only=True)
    participante = serializers.CharField(source="participante.username", read_only=True)

    class Meta:
        model = InscricaoEvento
        fields = ["id", "evento", "evento_nome", "participante", "data"]
        read_only_fields = fields


class InscricaoAtividadeSerializer(serializers.ModelSerializer):
    atividade_titulo = serializers.CharField(source="atividade.titulo", read_only=True)
    evento_nome = serializers.CharField(source="atividade.evento.nome", read_only=True)
    sala_nome = serializers.CharField(source="atividade.sala.nome", read_only=True)
    inicio = serializers.DateTimeField(source="atividade.inicio", read_only=True)
    fim = serializers.DateTimeField(source="atividade.fim", read_only=True)

    class Meta:
        model = InscricaoAtividade
        fields = [
            "id",
            "atividade",
            "atividade_titulo",
            "evento_nome",
            "sala_nome",
            "inicio",
            "fim",
            "data",
        ]
        read_only_fields = fields


class EventoIdSerializer(serializers.Serializer):
    evento = serializers.PrimaryKeyRelatedField(queryset=Evento.objects.all())


class AtividadeIdSerializer(serializers.Serializer):
    atividade = serializers.PrimaryKeyRelatedField(queryset=Atividade.objects.all())
