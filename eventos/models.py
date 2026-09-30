from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Sala(models.Model):
    nome = models.CharField(max_length=120)
    bloco = models.CharField(max_length=80)
    capacidade = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["bloco", "nome"]
        constraints = [
            models.UniqueConstraint(fields=["nome", "bloco"], name="sala_nome_bloco_unicos")
        ]

    def __str__(self):
        return f"{self.nome} - Bloco {self.bloco}"


class Evento(models.Model):
    nome = models.CharField(max_length=180)
    descricao = models.TextField()
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    inscricoes_abertas = models.BooleanField(default=True)
    organizador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="eventos_organizados",
    )

    class Meta:
        ordering = ["data_inicio", "nome"]

    def clean(self):
        super().clean()
        if self.data_inicio and self.data_fim and self.data_fim <= self.data_inicio:
            raise ValidationError({"data_fim": "O fim do evento deve ser posterior ao início."})
        if self.pk and self.data_inicio and self.data_fim:
            atividade_fora = self.atividades.filter(
                models.Q(inicio__lt=self.data_inicio) | models.Q(fim__gt=self.data_fim)
            ).exists()
            if atividade_fora:
                raise ValidationError(
                    {"data_fim": "O novo período deixaria atividades cadastradas fora do evento."}
                )

    def __str__(self):
        return self.nome


class Atividade(models.Model):
    class Tipo(models.TextChoices):
        PALESTRA = "PALESTRA", "Palestra"
        TREINAMENTO = "TREINAMENTO", "Treinamento"
        APRESENTACAO = "APRESENTACAO", "Apresentação"

    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="atividades")
    titulo = models.CharField(max_length=180)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    descricao = models.TextField()
    responsavel = models.CharField(max_length=150)
    sala = models.ForeignKey(Sala, on_delete=models.PROTECT, related_name="atividades")
    inicio = models.DateTimeField()
    fim = models.DateTimeField()

    class Meta:
        ordering = ["inicio", "titulo"]

    def clean(self):
        super().clean()
        erros = {}

        if self.inicio and self.fim and self.fim <= self.inicio:
            erros["fim"] = "O fim da atividade deve ser posterior ao início."

        if self.evento_id and self.inicio and self.fim:
            if self.inicio < self.evento.data_inicio or self.fim > self.evento.data_fim:
                erros["inicio"] = "A atividade precisa acontecer dentro do período do evento."

        if self.sala_id and self.inicio and self.fim and self.fim > self.inicio:
            conflito = Atividade.objects.filter(
                sala_id=self.sala_id,
                inicio__lt=self.fim,
                fim__gt=self.inicio,
            ).exclude(pk=self.pk)
            if conflito.exists():
                erros["sala"] = "A sala já está ocupada nesse intervalo de horário."

        if erros:
            raise ValidationError(erros)

    @property
    def vagas_ocupadas(self):
        return self.inscricoes.count()

    @property
    def vagas_restantes(self):
        return max(self.sala.capacidade - self.vagas_ocupadas, 0)

    @property
    def lotada(self):
        return self.vagas_restantes == 0

    def __str__(self):
        return f"{self.titulo} ({self.evento})"


class InscricaoEvento(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="inscricoes")
    participante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inscricoes_eventos",
    )
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["data"]
        constraints = [
            models.UniqueConstraint(
                fields=["evento", "participante"],
                name="evento_participante_unicos",
            )
        ]

    def __str__(self):
        return f"{self.participante} em {self.evento}"


class InscricaoAtividade(models.Model):
    inscricao_evento = models.ForeignKey(
        InscricaoEvento,
        on_delete=models.CASCADE,
        related_name="inscricoes_atividades",
    )
    atividade = models.ForeignKey(Atividade, on_delete=models.CASCADE, related_name="inscricoes")
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["data"]
        constraints = [
            models.UniqueConstraint(
                fields=["inscricao_evento", "atividade"],
                name="inscricao_evento_atividade_unicos",
            )
        ]

    def clean(self):
        super().clean()
        if (
            self.inscricao_evento_id
            and self.atividade_id
            and self.inscricao_evento.evento_id != self.atividade.evento_id
        ):
            raise ValidationError("A atividade não pertence ao evento desta inscrição.")

    def __str__(self):
        return f"{self.inscricao_evento.participante} em {self.atividade}"


class ListaEspera(models.Model):
    inscricao_evento = models.ForeignKey(
        InscricaoEvento,
        on_delete=models.CASCADE,
        related_name="esperas",
    )
    atividade = models.ForeignKey(Atividade, on_delete=models.CASCADE, related_name="lista_espera")
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["data", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["inscricao_evento", "atividade"],
                name="espera_inscricao_atividade_unicos",
            )
        ]

    @property
    def posicao(self):
        return (
            ListaEspera.objects.filter(atividade=self.atividade, data__lt=self.data).count() + 1
        )

    def clean(self):
        super().clean()
        if (
            self.inscricao_evento_id
            and self.atividade_id
            and self.inscricao_evento.evento_id != self.atividade.evento_id
        ):
            raise ValidationError("A atividade não pertence ao evento desta inscrição.")

    def __str__(self):
        return f"{self.inscricao_evento.participante} aguardando {self.atividade}"
