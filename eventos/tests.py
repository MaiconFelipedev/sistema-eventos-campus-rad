from datetime import datetime

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import EventoForm
from .models import Atividade, Evento, InscricaoAtividade, InscricaoEvento, ListaEspera, Sala
from .services import entrar_na_lista_espera, inscrever_na_atividade


def momento(dia, hora, minuto=0):
    return timezone.make_aware(datetime(2026, 11, dia, hora, minuto))


class BaseEventosTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        grupo = Group.objects.create(name="Organizadores")
        cls.organizador2 = User.objects.create_user("organizador2", password="teste12345")
        cls.organizador3 = User.objects.create_user("organizador3", password="teste12345")
        cls.organizador2.groups.add(grupo)
        cls.organizador3.groups.add(grupo)
        cls.participante4 = User.objects.create_user("participante4", password="teste12345")
        cls.participante5 = User.objects.create_user("participante5", password="teste12345")
        cls.participante6 = User.objects.create_user("participante6", password="teste12345")
        cls.participante7 = User.objects.create_user("participante7", password="teste12345")

        cls.sala_pequena = Sala.objects.create(nome="Laboratório", bloco="B", capacidade=2)
        cls.sala_grande = Sala.objects.create(nome="Auditório", bloco="A", capacidade=50)

        cls.evento = Evento.objects.create(
            nome="Semana de Tecnologia",
            descricao="Evento principal",
            data_inicio=momento(10, 8),
            data_fim=momento(10, 18),
            inscricoes_abertas=True,
            organizador=cls.organizador2,
        )
        cls.outro_evento = Evento.objects.create(
            nome="Jornada Científica",
            descricao="Evento simultâneo",
            data_inicio=momento(10, 8),
            data_fim=momento(11, 18),
            inscricoes_abertas=True,
            organizador=cls.organizador3,
        )
        cls.evento_fechado = Evento.objects.create(
            nome="Evento fechado",
            descricao="Sem novas inscrições",
            data_inicio=momento(12, 8),
            data_fim=momento(12, 18),
            inscricoes_abertas=False,
            organizador=cls.organizador2,
        )
        cls.atividade = Atividade.objects.create(
            evento=cls.evento,
            titulo="Oficina Django",
            tipo=Atividade.Tipo.TREINAMENTO,
            descricao="Oficina principal",
            responsavel="Docente",
            sala=cls.sala_pequena,
            inicio=momento(10, 10),
            fim=momento(10, 12),
        )
        cls.atividade_posterior = Atividade.objects.create(
            evento=cls.evento,
            titulo="Palestra da tarde",
            tipo=Atividade.Tipo.PALESTRA,
            descricao="Palestra",
            responsavel="Palestrante",
            sala=cls.sala_pequena,
            inicio=momento(10, 14),
            fim=momento(10, 15),
        )
        cls.atividade_simultanea = Atividade.objects.create(
            evento=cls.evento,
            titulo="Painel simultâneo",
            tipo=Atividade.Tipo.APRESENTACAO,
            descricao="Painel",
            responsavel="Equipe",
            sala=cls.sala_grande,
            inicio=momento(10, 10, 30),
            fim=momento(10, 11, 30),
        )
        cls.atividade_outro_evento = Atividade.objects.create(
            evento=cls.outro_evento,
            titulo="Minicurso simultâneo",
            tipo=Atividade.Tipo.TREINAMENTO,
            descricao="Minicurso",
            responsavel="Docente 2",
            sala=cls.sala_grande,
            inicio=momento(10, 10, 30),
            fim=momento(10, 11, 30),
        )

    def inscricao_evento(self, usuario, evento=None):
        return InscricaoEvento.objects.create(
            participante=usuario,
            evento=evento or self.evento,
        )

    def inscricao_atividade(self, usuario, atividade=None, evento=None):
        atividade = atividade or self.atividade
        inscricao_evento = self.inscricao_evento(usuario, evento or atividade.evento)
        return InscricaoAtividade.objects.create(
            inscricao_evento=inscricao_evento,
            atividade=atividade,
        )


class CriteriosAceitacaoTests(BaseEventosTestCase):
    def test_01_anonimo_ve_lista_eventos(self):
        resposta = self.client.get(reverse("eventos:lista"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, self.evento.nome)

    def test_02_anonimo_ve_programacao_e_vagas(self):
        resposta = self.client.get(reverse("eventos:detalhe", args=[self.evento.pk]))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, self.atividade.titulo)
        self.assertContains(resposta, "2 vagas")

    def test_03_anonimo_tenta_inscrever_e_vai_ao_login(self):
        resposta = self.client.post(reverse("eventos:evento_inscrever", args=[self.evento.pk]))
        self.assertRedirects(
            resposta,
            f"{reverse('login')}?next={reverse('eventos:evento_inscrever', args=[self.evento.pk])}",
        )

    def test_04_conta_recem_cadastrada_e_participante_comum(self):
        resposta = self.client.post(
            reverse("cadastro"),
            {
                "username": "contanova",
                "email": "nova@example.com",
                "password1": "SenhaForte@2026",
                "password2": "SenhaForte@2026",
            },
        )
        usuario = User.objects.get(username="contanova")
        self.assertRedirects(resposta, reverse("eventos:lista"))
        self.assertFalse(usuario.groups.filter(name="Organizadores").exists())
        self.assertTrue(self.client.session.get("_auth_user_id"))

    def test_05_organizador_e_preenchido_pelo_sistema(self):
        self.client.force_login(self.organizador2)
        resposta = self.client.post(
            reverse("eventos:evento_criar"),
            {
                "nome": "Novo evento",
                "descricao": "Descrição",
                "data_inicio": "2026-11-15T08:00",
                "data_fim": "2026-11-15T18:00",
                "inscricoes_abertas": "on",
            },
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(Evento.objects.get(nome="Novo evento").organizador, self.organizador2)

    def test_06_outro_organizador_nao_edita_evento_alheio(self):
        self.client.force_login(self.organizador3)
        resposta = self.client.get(reverse("eventos:evento_editar", args=[self.evento.pk]))
        self.assertEqual(resposta.status_code, 404)

    def test_07_atividade_fora_do_periodo_e_recusada(self):
        self.client.force_login(self.organizador2)
        resposta = self.client.post(
            reverse("eventos:atividade_criar", args=[self.evento.pk]),
            self._dados_atividade("2026-11-09T09:00", "2026-11-09T10:00"),
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "dentro do período do evento")

    def test_08_fim_antes_do_inicio_e_recusado(self):
        self.client.force_login(self.organizador2)
        resposta = self.client.post(
            reverse("eventos:atividade_criar", args=[self.evento.pk]),
            self._dados_atividade("2026-11-10T16:00", "2026-11-10T15:00"),
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "posterior ao início")

    def test_09_sala_ocupada_e_recusada(self):
        self.client.force_login(self.organizador2)
        resposta = self.client.post(
            reverse("eventos:atividade_criar", args=[self.evento.pk]),
            self._dados_atividade("2026-11-10T11:00", "2026-11-10T12:30"),
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "sala já está ocupada")

    def test_10_mesma_sala_em_outro_horario_e_aceita(self):
        self.client.force_login(self.organizador2)
        resposta = self.client.post(
            reverse("eventos:atividade_criar", args=[self.evento.pk]),
            self._dados_atividade("2026-11-10T16:00", "2026-11-10T17:00"),
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(Atividade.objects.filter(titulo="Nova atividade").exists())

    def test_11_participante_se_inscreve_no_evento(self):
        self.client.force_login(self.participante4)
        self.client.post(reverse("eventos:evento_inscrever", args=[self.evento.pk]))
        self.assertTrue(
            InscricaoEvento.objects.filter(evento=self.evento, participante=self.participante4).exists()
        )

    def test_12_inscricao_duplicada_no_evento_e_recusada(self):
        self.inscricao_evento(self.participante4)
        self.client.force_login(self.participante4)
        self.client.post(reverse("eventos:evento_inscrever", args=[self.evento.pk]))
        self.assertEqual(
            InscricaoEvento.objects.filter(evento=self.evento, participante=self.participante4).count(),
            1,
        )

    def test_13_evento_fechado_recusa_inscricao(self):
        self.client.force_login(self.participante4)
        self.client.post(reverse("eventos:evento_inscrever", args=[self.evento_fechado.pk]))
        self.assertFalse(
            InscricaoEvento.objects.filter(
                evento=self.evento_fechado,
                participante=self.participante4,
            ).exists()
        )

    def test_14_atividade_exige_inscricao_no_evento(self):
        self.client.force_login(self.participante4)
        self.client.post(reverse("eventos:atividade_inscrever", args=[self.atividade.pk]))
        self.assertFalse(
            InscricaoAtividade.objects.filter(
                atividade=self.atividade,
                inscricao_evento__participante=self.participante4,
            ).exists()
        )

    def test_15_inscricao_em_atividade_reduz_vaga(self):
        self.inscricao_evento(self.participante4)
        self.client.force_login(self.participante4)
        self.client.post(reverse("eventos:atividade_inscrever", args=[self.atividade.pk]))
        self.assertEqual(self.atividade.vagas_restantes, 1)

    def test_16_terceira_inscricao_e_recusada_na_sala_de_capacidade_dois(self):
        self.inscricao_atividade(self.participante4)
        self.inscricao_atividade(self.participante5)
        self.inscricao_evento(self.participante6)
        self.client.force_login(self.participante6)
        self.client.post(reverse("eventos:atividade_inscrever", args=[self.atividade.pk]))
        self.assertEqual(self.atividade.inscricoes.count(), 2)

    def test_17_botao_de_inscricao_some_quando_lotada(self):
        self.inscricao_atividade(self.participante4)
        self.inscricao_atividade(self.participante5)
        self.inscricao_evento(self.participante6)
        self.client.force_login(self.participante6)
        resposta = self.client.get(reverse("eventos:detalhe", args=[self.evento.pk]))
        self.assertNotContains(
            resposta,
            f'action="{reverse("eventos:atividade_inscrever", args=[self.atividade.pk])}"',
        )
        self.assertContains(resposta, "Entrar na lista de espera")

    def test_18_conflito_no_mesmo_evento_e_recusado(self):
        inscricao = self.inscricao_evento(self.participante4)
        InscricaoAtividade.objects.create(inscricao_evento=inscricao, atividade=self.atividade)
        self.client.force_login(self.participante4)
        self.client.post(
            reverse("eventos:atividade_inscrever", args=[self.atividade_simultanea.pk])
        )
        self.assertFalse(
            InscricaoAtividade.objects.filter(
                inscricao_evento=inscricao,
                atividade=self.atividade_simultanea,
            ).exists()
        )

    def test_19_conflito_entre_eventos_diferentes_e_recusado(self):
        self.inscricao_atividade(self.participante4)
        outra_inscricao = self.inscricao_evento(self.participante4, self.outro_evento)
        self.client.force_login(self.participante4)
        self.client.post(
            reverse("eventos:atividade_inscrever", args=[self.atividade_outro_evento.pk])
        )
        self.assertFalse(
            InscricaoAtividade.objects.filter(
                inscricao_evento=outra_inscricao,
                atividade=self.atividade_outro_evento,
            ).exists()
        )

    def test_20_cancelar_atividade_mantem_inscricao_no_evento(self):
        inscricao = self.inscricao_atividade(self.participante4)
        self.client.force_login(self.participante4)
        self.client.post(reverse("eventos:atividade_cancelar", args=[inscricao.pk]))
        self.assertFalse(InscricaoAtividade.objects.filter(pk=inscricao.pk).exists())
        self.assertTrue(
            InscricaoEvento.objects.filter(evento=self.evento, participante=self.participante4).exists()
        )

    def test_21_cancelar_atividade_libera_vaga(self):
        inscricao = self.inscricao_atividade(self.participante4)
        self.client.force_login(self.participante4)
        self.client.post(reverse("eventos:atividade_cancelar", args=[inscricao.pk]))
        self.assertEqual(self.atividade.vagas_restantes, 2)

    def test_22_cancelar_evento_remove_atividades_em_cascata(self):
        inscricao_atividade = self.inscricao_atividade(self.participante4)
        inscricao_evento = inscricao_atividade.inscricao_evento
        self.client.force_login(self.participante4)
        self.client.post(reverse("eventos:evento_cancelar", args=[inscricao_evento.pk]))
        self.assertFalse(InscricaoEvento.objects.filter(pk=inscricao_evento.pk).exists())
        self.assertFalse(InscricaoAtividade.objects.filter(pk=inscricao_atividade.pk).exists())

    def test_23_participante_nao_cancela_inscricao_alheia(self):
        inscricao = self.inscricao_atividade(self.participante4)
        self.client.force_login(self.participante5)
        resposta = self.client.post(reverse("eventos:atividade_cancelar", args=[inscricao.pk]))
        self.assertEqual(resposta.status_code, 403)
        self.assertTrue(InscricaoAtividade.objects.filter(pk=inscricao.pk).exists())

    def test_24_agenda_mostra_atividades_de_todos_os_eventos(self):
        self.inscricao_atividade(self.participante4, self.atividade_posterior)
        self.inscricao_atividade(
            self.participante4,
            self.atividade_outro_evento,
            self.outro_evento,
        )
        self.client.force_login(self.participante4)
        resposta = self.client.get(reverse("eventos:agenda"))
        self.assertContains(resposta, self.atividade_posterior.titulo)
        self.assertContains(resposta, self.atividade_outro_evento.titulo)

    def test_25_agenda_e_ordenada_por_data_e_hora(self):
        posterior = self.inscricao_atividade(self.participante4, self.atividade_posterior)
        outra = self.inscricao_atividade(
            self.participante4,
            self.atividade_outro_evento,
            self.outro_evento,
        )
        self.client.force_login(self.participante4)
        resposta = self.client.get(reverse("eventos:agenda"))
        self.assertEqual(list(resposta.context["inscricoes"]), [outra, posterior])

    def test_26_organizador_ve_inscritos_de_evento_proprio(self):
        self.inscricao_atividade(self.participante4)
        self.client.force_login(self.organizador2)
        resposta = self.client.get(reverse("eventos:painel", args=[self.evento.pk]))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, self.participante4.username)

    def test_27_organizador_nao_ve_painel_alheio(self):
        self.client.force_login(self.organizador3)
        resposta = self.client.get(reverse("eventos:painel", args=[self.evento.pk]))
        self.assertEqual(resposta.status_code, 404)

    def _dados_atividade(self, inicio, fim):
        return {
            "titulo": "Nova atividade",
            "tipo": Atividade.Tipo.PALESTRA,
            "descricao": "Descrição",
            "responsavel": "Responsável",
            "sala": self.sala_pequena.pk,
            "inicio": inicio,
            "fim": fim,
        }


class RestricoesTecnicasTests(BaseEventosTestCase):
    def test_organizador_nao_esta_no_formulario_de_evento(self):
        self.assertNotIn("organizador", EventoForm().fields)

    def test_acoes_de_estado_recusam_get(self):
        self.client.force_login(self.participante4)
        resposta = self.client.get(reverse("eventos:evento_inscrever", args=[self.evento.pk]))
        self.assertEqual(resposta.status_code, 405)

    def test_participante_ve_apenas_a_propria_agenda(self):
        self.inscricao_atividade(self.participante4)
        self.inscricao_atividade(self.participante5, self.atividade_posterior)
        self.client.force_login(self.participante4)
        resposta = self.client.get(reverse("eventos:agenda"))
        self.assertContains(resposta, self.atividade.titulo)
        self.assertNotContains(resposta, self.atividade_posterior.titulo)

    def test_intervalos_que_apenas_encostam_nao_conflitam(self):
        atividade = Atividade(
            evento=self.evento,
            titulo="Atividade seguinte",
            tipo=Atividade.Tipo.PALESTRA,
            descricao="Teste",
            responsavel="Docente",
            sala=self.sala_pequena,
            inicio=momento(10, 12),
            fim=momento(10, 13),
        )
        atividade.full_clean()

    def test_intervalo_que_contem_outro_e_detectado(self):
        atividade = Atividade(
            evento=self.evento,
            titulo="Atividade abrangente",
            tipo=Atividade.Tipo.PALESTRA,
            descricao="Teste",
            responsavel="Docente",
            sala=self.sala_pequena,
            inicio=momento(10, 9),
            fim=momento(10, 13),
        )
        with self.assertRaisesMessage(Exception, "sala já está ocupada"):
            atividade.full_clean()

    def test_evento_nao_pode_ser_encurtado_deixando_atividade_fora(self):
        self.evento.data_fim = momento(10, 11)
        with self.assertRaisesMessage(Exception, "deixaria atividades cadastradas fora"):
            self.evento.full_clean()


class ListaEsperaTests(BaseEventosTestCase):
    def setUp(self):
        self.inscricao_atividade(self.participante4)
        self.inscricao_atividade(self.participante5)
        self.inscricao_evento(self.participante6)
        self.inscricao_evento(self.participante7)

    def test_fila_e_ordenada_por_chegada_e_exibe_posicao(self):
        primeira = entrar_na_lista_espera(self.participante6, self.atividade.pk)
        segunda = entrar_na_lista_espera(self.participante7, self.atividade.pk)
        self.assertEqual(primeira.posicao, 1)
        self.assertEqual(segunda.posicao, 2)

    def test_cancelamento_promove_primeiro_da_fila(self):
        espera = entrar_na_lista_espera(self.participante6, self.atividade.pk)
        inscricao = InscricaoAtividade.objects.get(
            atividade=self.atividade,
            inscricao_evento__participante=self.participante4,
        )
        self.client.force_login(self.participante4)
        self.client.post(reverse("eventos:atividade_cancelar", args=[inscricao.pk]))
        self.assertTrue(
            InscricaoAtividade.objects.filter(
                atividade=self.atividade,
                inscricao_evento__participante=self.participante6,
            ).exists()
        )
        self.assertFalse(ListaEspera.objects.filter(pk=espera.pk).exists())

    def test_promocao_pula_participante_com_conflito_atual(self):
        primeira = entrar_na_lista_espera(self.participante6, self.atividade.pk)
        segunda = entrar_na_lista_espera(self.participante7, self.atividade.pk)
        inscricao_outro_evento = self.inscricao_evento(self.participante6, self.outro_evento)
        InscricaoAtividade.objects.create(
            inscricao_evento=inscricao_outro_evento,
            atividade=self.atividade_outro_evento,
        )
        inscricao = InscricaoAtividade.objects.get(
            atividade=self.atividade,
            inscricao_evento__participante=self.participante4,
        )
        self.client.force_login(self.participante4)
        self.client.post(reverse("eventos:atividade_cancelar", args=[inscricao.pk]))
        self.assertTrue(ListaEspera.objects.filter(pk=primeira.pk).exists())
        self.assertFalse(ListaEspera.objects.filter(pk=segunda.pk).exists())
        self.assertTrue(
            InscricaoAtividade.objects.filter(
                atividade=self.atividade,
                inscricao_evento__participante=self.participante7,
            ).exists()
        )

    def test_lista_exige_inscricao_no_evento(self):
        usuario = User.objects.create_user("foraevento", password="teste12345")
        with self.assertRaisesMessage(Exception, "Inscreva-se no evento"):
            entrar_na_lista_espera(usuario, self.atividade.pk)
