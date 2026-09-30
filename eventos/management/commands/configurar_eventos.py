from datetime import datetime

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.utils import timezone

from eventos.models import Atividade, Evento, InscricaoAtividade, InscricaoEvento, Sala


SENHA_DEMO = "Eventos@2026"


def horario(ano, mes, dia, hora, minuto=0):
    return timezone.make_aware(datetime(ano, mes, dia, hora, minuto))


class Command(BaseCommand):
    help = "Cria os cinco usuários e os dados demonstrativos exigidos pela atividade."

    def handle(self, *args, **options):
        grupo_organizadores, _ = Group.objects.get_or_create(name="Organizadores")

        usuarios = {}
        contas = [
            ("admin_eventos", "Administrador", "de Eventos", True),
            ("organizador2", "Olívia", "Organizadora", False),
            ("organizador3", "Otávio", "Organizador", False),
            ("participante4", "Paula", "Participante", False),
            ("participante5", "Pedro", "Participante", False),
        ]
        for username, primeiro_nome, sobrenome, superusuario in contas:
            usuario, _ = User.objects.get_or_create(username=username)
            usuario.first_name = primeiro_nome
            usuario.last_name = sobrenome
            usuario.email = f"{username}@example.com"
            usuario.is_staff = superusuario
            usuario.is_superuser = superusuario
            usuario.set_password(SENHA_DEMO)
            usuario.save()
            usuarios[username] = usuario

        usuarios["organizador2"].groups.add(grupo_organizadores)
        usuarios["organizador3"].groups.add(grupo_organizadores)

        laboratorio, _ = Sala.objects.update_or_create(
            nome="Laboratório 01",
            bloco="B",
            defaults={"capacidade": 2},
        )
        auditorio, _ = Sala.objects.update_or_create(
            nome="Auditório Central",
            bloco="A",
            defaults={"capacidade": 80},
        )
        sala_12, _ = Sala.objects.update_or_create(
            nome="Sala 12",
            bloco="C",
            defaults={"capacidade": 35},
        )

        semana, _ = Evento.objects.update_or_create(
            nome="Semana de Tecnologia 2026",
            defaults={
                "descricao": "Palestras e oficinas sobre desenvolvimento de software.",
                "data_inicio": horario(2026, 10, 20, 8),
                "data_fim": horario(2026, 10, 20, 18),
                "inscricoes_abertas": True,
                "organizador": usuarios["organizador2"],
            },
        )
        jornada, _ = Evento.objects.update_or_create(
            nome="Jornada Científica 2026",
            defaults={
                "descricao": "Apresentações de pesquisa e minicursos do campus.",
                "data_inicio": horario(2026, 10, 20, 8, 30),
                "data_fim": horario(2026, 10, 21, 17),
                "inscricoes_abertas": True,
                "organizador": usuarios["organizador3"],
            },
        )
        Evento.objects.update_or_create(
            nome="Encontro de Egressos 2026",
            defaults={
                "descricao": "Encontro com ex-alunos e profissionais convidados.",
                "data_inicio": horario(2026, 10, 22, 9),
                "data_fim": horario(2026, 10, 22, 17),
                "inscricoes_abertas": False,
                "organizador": usuarios["organizador2"],
            },
        )

        def atividade(evento, titulo, **dados):
            objeto, _ = Atividade.objects.update_or_create(
                evento=evento,
                titulo=titulo,
                defaults=dados,
            )
            objeto.full_clean()
            objeto.save()
            return objeto

        abertura = atividade(
            semana,
            "Abertura da Semana de Tecnologia",
            tipo=Atividade.Tipo.PALESTRA,
            descricao="Tendências e oportunidades na área de tecnologia.",
            responsavel="Profa. Renata Lima",
            sala=auditorio,
            inicio=horario(2026, 10, 20, 9),
            fim=horario(2026, 10, 20, 10, 30),
        )
        oficina = atividade(
            semana,
            "Oficina Django",
            tipo=Atividade.Tipo.TREINAMENTO,
            descricao="Construção de uma aplicação web com Django.",
            responsavel="Prof. Rodrigo Araújo",
            sala=laboratorio,
            inicio=horario(2026, 10, 20, 14),
            fim=horario(2026, 10, 20, 16),
        )
        atividade(
            jornada,
            "Painel de Pesquisa Aplicada",
            tipo=Atividade.Tipo.APRESENTACAO,
            descricao="Projetos de pesquisa desenvolvidos por estudantes.",
            responsavel="Profa. Camila Souza",
            sala=sala_12,
            inicio=horario(2026, 10, 20, 9),
            fim=horario(2026, 10, 20, 10, 30),
        )
        minicurso = atividade(
            jornada,
            "Minicurso de Dados",
            tipo=Atividade.Tipo.TREINAMENTO,
            descricao="Fundamentos de análise e visualização de dados.",
            responsavel="Prof. André Silva",
            sala=laboratorio,
            inicio=horario(2026, 10, 20, 9),
            fim=horario(2026, 10, 20, 10, 30),
        )

        for participante in (usuarios["participante4"], usuarios["participante5"]):
            inscricao_evento, _ = InscricaoEvento.objects.get_or_create(
                evento=semana,
                participante=participante,
            )
            InscricaoAtividade.objects.get_or_create(
                inscricao_evento=inscricao_evento,
                atividade=oficina,
            )

        inscricao_jornada, _ = InscricaoEvento.objects.get_or_create(
            evento=jornada,
            participante=usuarios["participante4"],
        )
        InscricaoAtividade.objects.get_or_create(
            inscricao_evento=inscricao_jornada,
            atividade=minicurso,
        )

        self.stdout.write(self.style.SUCCESS("Dados demonstrativos configurados."))
        self.stdout.write(f"Senha das cinco contas: {SENHA_DEMO}")
        self.stdout.write(
            f"Atividades simultâneas: {abertura.titulo}, Painel de Pesquisa Aplicada e {minicurso.titulo}."
        )
