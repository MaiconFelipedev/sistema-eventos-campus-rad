from django.contrib import admin

from .models import Atividade, Evento, InscricaoAtividade, InscricaoEvento, ListaEspera, Sala


@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ("nome", "bloco", "capacidade")
    list_filter = ("bloco",)
    search_fields = ("nome", "bloco")


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ("nome", "data_inicio", "data_fim", "inscricoes_abertas", "organizador")
    list_filter = ("inscricoes_abertas", "data_inicio")
    search_fields = ("nome", "descricao", "organizador__username")
    autocomplete_fields = ("organizador",)


@admin.register(Atividade)
class AtividadeAdmin(admin.ModelAdmin):
    list_display = ("titulo", "evento", "tipo", "sala", "inicio", "fim", "vagas_restantes")
    list_filter = ("tipo", "evento", "sala")
    search_fields = ("titulo", "descricao", "responsavel", "evento__nome")
    autocomplete_fields = ("evento", "sala")


@admin.register(InscricaoEvento)
class InscricaoEventoAdmin(admin.ModelAdmin):
    list_display = ("participante", "evento", "data")
    list_filter = ("evento", "data")
    search_fields = ("participante__username", "evento__nome")
    autocomplete_fields = ("participante", "evento")


@admin.register(InscricaoAtividade)
class InscricaoAtividadeAdmin(admin.ModelAdmin):
    list_display = ("participante", "atividade", "data")
    list_filter = ("atividade__evento", "atividade")
    search_fields = ("inscricao_evento__participante__username", "atividade__titulo")

    @admin.display(description="Participante")
    def participante(self, obj):
        return obj.inscricao_evento.participante


@admin.register(ListaEspera)
class ListaEsperaAdmin(admin.ModelAdmin):
    list_display = ("participante", "atividade", "data", "posicao")
    list_filter = ("atividade__evento", "atividade")
    search_fields = ("inscricao_evento__participante__username", "atividade__titulo")

    @admin.display(description="Participante")
    def participante(self, obj):
        return obj.inscricao_evento.participante
