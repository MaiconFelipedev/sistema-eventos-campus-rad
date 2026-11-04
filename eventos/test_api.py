from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from django.urls import reverse

from .models import Atividade, InscricaoAtividade, InscricaoEvento, Sala
from .tests import BaseEventosTestCase, momento


class ApiRestCriteriosAceitacaoTests(BaseEventosTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.tokens = {
            usuario.username: Token.objects.create(user=usuario)
            for usuario in (
                cls.organizador2,
                cls.organizador3,
                cls.participante4,
                cls.participante5,
                cls.participante6,
                cls.participante7,
            )
        }

    def setUp(self):
        self.api = APIClient()

    def autenticar(self, usuario):
        self.api.credentials(HTTP_AUTHORIZATION=f"Token {self.tokens[usuario.username].key}")

    def dados_atividade(self, evento=None, sala=None, inicio=None, fim=None, titulo="API Django"):
        return {
            "evento": (evento or self.evento).pk,
            "titulo": titulo,
            "tipo": Atividade.Tipo.TREINAMENTO,
            "descricao": "Atividade criada pela API REST.",
            "responsavel": "Docente da API",
            "sala": (sala or self.sala_grande).pk,
            "inicio": (inicio or momento(10, 16)).isoformat(),
            "fim": (fim or momento(10, 17)).isoformat(),
        }

    def test_01_lista_eventos_e_publica(self):
        resposta = self.api.get(reverse("api:evento-list"))
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(self.evento.nome, [item["nome"] for item in resposta.data["results"]])

    def test_02_programacao_do_evento_e_publica(self):
        resposta = self.api.get(reverse("api:evento-programacao", args=[self.evento.pk]))
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(self.atividade.titulo, [item["titulo"] for item in resposta.data["atividades"]])

    def test_03_programacao_traz_sala_e_vagas_restantes(self):
        resposta = self.api.get(reverse("api:evento-programacao", args=[self.evento.pk]))
        atividade = next(item for item in resposta.data["atividades"] if item["id"] == self.atividade.pk)
        self.assertEqual(atividade["sala_nome"], self.sala_pequena.nome)
        self.assertEqual(atividade["vagas_restantes"], 2)

    def test_04_criar_atividade_sem_token_retorna_401(self):
        resposta = self.api.post(reverse("api:atividade-list"), self.dados_atividade(), format="json")
        self.assertEqual(resposta.status_code, 401)

    def test_05_participante_com_token_nao_cria_atividade(self):
        self.autenticar(self.participante4)
        resposta = self.api.post(reverse("api:atividade-list"), self.dados_atividade(), format="json")
        self.assertEqual(resposta.status_code, 403)

    def test_06_organizador_cria_atividade_no_proprio_evento(self):
        self.autenticar(self.organizador2)
        resposta = self.api.post(reverse("api:atividade-list"), self.dados_atividade(), format="json")
        self.assertEqual(resposta.status_code, 201)
        self.assertTrue(Atividade.objects.filter(titulo="API Django").exists())

    def test_07_organizador_nao_altera_evento_de_outro(self):
        self.autenticar(self.organizador2)
        resposta = self.api.patch(
            reverse("api:evento-detail", args=[self.outro_evento.pk]),
            {"nome": "Tentativa indevida"},
            format="json",
        )
        self.assertEqual(resposta.status_code, 403)
        self.outro_evento.refresh_from_db()
        self.assertNotEqual(self.outro_evento.nome, "Tentativa indevida")

    def test_08_atividade_com_fim_antes_do_inicio_retorna_400(self):
        self.autenticar(self.organizador2)
        resposta = self.api.post(
            reverse("api:atividade-list"),
            self.dados_atividade(inicio=momento(10, 17), fim=momento(10, 16)),
            format="json",
        )
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("fim", resposta.data)

    def test_09_atividade_em_sala_ocupada_retorna_400(self):
        self.autenticar(self.organizador2)
        resposta = self.api.post(
            reverse("api:atividade-list"),
            self.dados_atividade(
                sala=self.sala_pequena,
                inicio=momento(10, 11),
                fim=momento(10, 12, 30),
            ),
            format="json",
        )
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("sala", resposta.data)

    def test_10_participante_se_inscreve_em_evento(self):
        self.autenticar(self.participante4)
        resposta = self.api.post(
            reverse("api:inscrever-evento"),
            {"evento": self.evento.pk},
            format="json",
        )
        self.assertEqual(resposta.status_code, 201)
        self.assertTrue(
            InscricaoEvento.objects.filter(evento=self.evento, participante=self.participante4).exists()
        )

    def test_11_inscricao_duplicada_no_evento_retorna_400(self):
        self.inscricao_evento(self.participante4)
        self.autenticar(self.participante4)
        resposta = self.api.post(
            reverse("api:inscrever-evento"),
            {"evento": self.evento.pk},
            format="json",
        )
        self.assertEqual(resposta.status_code, 400)

    def test_12_atividade_exige_inscricao_previa_no_evento(self):
        self.autenticar(self.participante4)
        resposta = self.api.post(
            reverse("api:inscrever-atividade"),
            {"atividade": self.atividade.pk},
            format="json",
        )
        self.assertEqual(resposta.status_code, 400)

    def test_13_inscricao_em_atividade_reduz_vagas(self):
        self.inscricao_evento(self.participante4)
        self.autenticar(self.participante4)
        resposta = self.api.post(
            reverse("api:inscrever-atividade"),
            {"atividade": self.atividade.pk},
            format="json",
        )
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(self.atividade.vagas_restantes, 1)

    def test_14_atividade_lotada_retorna_400_com_mensagem(self):
        self.inscricao_atividade(self.participante4)
        self.inscricao_atividade(self.participante5)
        self.inscricao_evento(self.participante6)
        self.autenticar(self.participante6)
        resposta = self.api.post(
            reverse("api:inscrever-atividade"),
            {"atividade": self.atividade.pk},
            format="json",
        )
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("lotada", str(resposta.data).lower())

    def test_15_conflito_de_agenda_no_mesmo_evento_retorna_400(self):
        inscricao = self.inscricao_evento(self.participante4)
        InscricaoAtividade.objects.create(inscricao_evento=inscricao, atividade=self.atividade)
        self.autenticar(self.participante4)
        resposta = self.api.post(
            reverse("api:inscrever-atividade"),
            {"atividade": self.atividade_simultanea.pk},
            format="json",
        )
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("conflita", str(resposta.data).lower())

    def test_16_conflito_de_agenda_entre_eventos_retorna_400(self):
        self.inscricao_atividade(self.participante4)
        self.inscricao_evento(self.participante4, self.outro_evento)
        self.autenticar(self.participante4)
        resposta = self.api.post(
            reverse("api:inscrever-atividade"),
            {"atividade": self.atividade_outro_evento.pk},
            format="json",
        )
        self.assertEqual(resposta.status_code, 400)

    def test_17_cancelar_atividade_libera_vaga(self):
        inscricao = self.inscricao_atividade(self.participante4)
        self.autenticar(self.participante4)
        resposta = self.api.delete(reverse("api:cancelar-atividade", args=[inscricao.pk]))
        self.assertEqual(resposta.status_code, 204)
        self.assertEqual(self.atividade.vagas_restantes, 2)

    def test_18_cancelar_evento_remove_inscricoes_de_atividades(self):
        inscricao_atividade = self.inscricao_atividade(self.participante4)
        inscricao_evento = inscricao_atividade.inscricao_evento
        self.autenticar(self.participante4)
        resposta = self.api.delete(reverse("api:cancelar-evento", args=[inscricao_evento.pk]))
        self.assertEqual(resposta.status_code, 204)
        self.assertFalse(InscricaoAtividade.objects.filter(pk=inscricao_atividade.pk).exists())

    def test_19_participante_nao_cancela_inscricao_alheia(self):
        inscricao = self.inscricao_atividade(self.participante4)
        self.autenticar(self.participante5)
        resposta = self.api.delete(reverse("api:cancelar-atividade", args=[inscricao.pk]))
        self.assertEqual(resposta.status_code, 403)
        self.assertTrue(InscricaoAtividade.objects.filter(pk=inscricao.pk).exists())

    def test_20_agenda_retorna_apenas_atividades_do_token(self):
        propria = self.inscricao_atividade(self.participante4, self.atividade_posterior)
        self.inscricao_atividade(self.participante5, self.atividade)
        self.autenticar(self.participante4)
        resposta = self.api.get(reverse("api:minha-agenda"))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual([item["id"] for item in resposta.data], [propria.pk])

    def test_21_agenda_sem_token_retorna_401(self):
        resposta = self.api.get(reverse("api:minha-agenda"))
        self.assertEqual(resposta.status_code, 401)

    def test_22_lista_atividades_e_paginada(self):
        resposta = self.api.get(reverse("api:atividade-list"))
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("count", resposta.data)
        self.assertIn("results", resposta.data)

    def test_23_busca_atividade_por_titulo_ou_descricao(self):
        resposta = self.api.get(reverse("api:atividade-list"), {"search": "Django"})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual([item["id"] for item in resposta.data["results"]], [self.atividade.pk])

    def test_24_documentacao_swagger_e_schema_estao_publicos(self):
        docs = self.api.get(reverse("api:docs"))
        schema = self.api.get(reverse("api:schema"))
        self.assertEqual(docs.status_code, 200)
        self.assertEqual(schema.status_code, 200)
        self.assertContains(docs, "swagger")

    def test_25_site_html_continua_funcionando(self):
        resposta = self.client.get(reverse("eventos:detalhe", args=[self.evento.pk]))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, self.atividade.titulo)

    def test_desafio_programacao_nao_cresce_consultas_com_atividades(self):
        for numero in range(5):
            sala = Sala.objects.create(
                nome=f"Sala extra {numero}",
                bloco="D",
                capacidade=20,
            )
            Atividade.objects.create(
                evento=self.evento,
                titulo=f"Atividade extra {numero}",
                tipo=Atividade.Tipo.PALESTRA,
                descricao="Cenário para confirmar ausência de N+1.",
                responsavel="Docente",
                sala=sala,
                inicio=momento(10, 8),
                fim=momento(10, 9),
            )

        with self.assertNumQueries(4):
            resposta = self.api.get(
                reverse("api:evento-programacao", args=[self.evento.pk])
            )
            self.assertEqual(resposta.status_code, 200)
            self.assertEqual(len(resposta.data["atividades"]), 8)
