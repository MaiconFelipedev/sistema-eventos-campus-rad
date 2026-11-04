# Sistema de Inscrições em Eventos do Campus — Site e API REST

Projeto Django desenvolvido nas atividades **07 — Sistema de eventos** e
**08 — API REST do Sistema de Eventos** da disciplina de Rapid Application
Development (RAD), no IFPB.

## Integrante

- Maicon Felipe da Silva Souza

## Funcionalidades

### Site HTML

- lista pública de eventos e programação completa;
- cadastro, login e logout com recursos nativos do Django;
- gestão de eventos e atividades pelos respectivos organizadores;
- inscrição e cancelamento em eventos e atividades;
- bloqueio de sala lotada, conflito de sala e conflito na agenda do participante;
- agenda pessoal ordenada por data e hora;
- painel restrito com inscritos do evento;
- lista de espera com promoção automática.

### API REST

- endpoints públicos para eventos, atividades e programação;
- autenticação por token para operações protegidas;
- CRUD de eventos e atividades com autorização por proprietário;
- inscrição e cancelamento em eventos e atividades;
- agenda isolada pelo participante autenticado;
- paginação, busca e ordenação;
- schema OpenAPI e documentação Swagger;
- programação completa com serializers aninhados e consultas otimizadas.

## Tecnologias

- Python 3;
- Django 5.2.17;
- Django REST Framework 3.16.1;
- drf-spectacular 0.28.0;
- SQLite;
- HTML e CSS.

## Como executar

### PowerShell

```powershell
cd C:\Users\maicon.felipe\Documents\RAD\eventos-campus-django
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py configurar_eventos
python manage.py runserver 127.0.0.1:8009
```

### Git Bash

```bash
cd /c/Users/maicon.felipe/Documents/RAD/eventos-campus-django
source .venv/Scripts/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py configurar_eventos
python manage.py runserver 127.0.0.1:8009
```

Endereços principais:

- site: `http://127.0.0.1:8009/`;
- API navegável: `http://127.0.0.1:8009/api/`;
- documentação Swagger: `http://127.0.0.1:8009/api/docs/`;
- schema OpenAPI: `http://127.0.0.1:8009/api/schema/`;
- administração: `http://127.0.0.1:8009/admin/`.

## Contas e tokens de teste

Todas as contas usam a senha `Eventos@2026`.

| Usuário | Papel | Token |
|---|---|---|
| `admin_eventos` | Superusuário | `0173a2e7d6effbb77e9cd970381d9683f71ae171` |
| `organizador2` | Organizador da Semana de Tecnologia | `323a245ac14f7f68f1cb123d65b1041f309b1c89` |
| `organizador3` | Organizador da Jornada Científica | `4be2526d1683a6deb33db903976345e4b099fdec` |
| `participante4` | Participante com inscrições demonstrativas | `44893f35139a4ffd739148de7388abb713050bac` |
| `participante5` | Participante que ocupa a última vaga | `2ac96ce24a95ae66d2994adba394562218278f82` |

Cabeçalho de autenticação:

```http
Authorization: Token 44893f35139a4ffd739148de7388abb713050bac
```

Também é possível obter o token enviando `username` e `password` para
`POST /api/token/`.

## Endpoints

| Método | Endpoint | Acesso | Finalidade |
|---|---|---|---|
| GET | `/api/eventos/` | Público | Lista paginada de eventos |
| GET | `/api/eventos/{id}/` | Público | Detalhes de um evento |
| GET | `/api/eventos/{id}/programacao/` | Público | Evento, atividades, salas e vagas em uma requisição |
| POST | `/api/eventos/` | Organizador | Criar evento; organizador vem do token |
| PUT/PATCH/DELETE | `/api/eventos/{id}/` | Dono do evento | Alterar ou excluir evento próprio |
| GET | `/api/atividades/` | Público | Lista paginada, pesquisável e ordenável |
| GET | `/api/atividades/?search=django` | Público | Busca por título ou descrição |
| GET | `/api/atividades/?ordering=inicio` | Público | Ordenação por data de início |
| POST | `/api/atividades/` | Organizador do evento | Criar atividade |
| PUT/PATCH/DELETE | `/api/atividades/{id}/` | Organizador do evento | Alterar ou excluir atividade própria |
| GET | `/api/salas/` | Público | Lista das salas |
| POST | `/api/inscricoes/eventos/` | Token | Inscrever o participante do token em evento |
| DELETE | `/api/inscricoes/eventos/{id}/` | Dono | Cancelar inscrição e atividades vinculadas |
| POST | `/api/inscricoes/atividades/` | Token | Inscrever o participante do token em atividade |
| DELETE | `/api/inscricoes/atividades/{id}/` | Dono | Cancelar inscrição na atividade |
| GET | `/api/minha-agenda/` | Token | Agenda exclusiva do participante autenticado |
| POST | `/api/token/` | Usuário e senha | Obter token |
| GET | `/api/schema/` | Público | Schema OpenAPI |
| GET | `/api/docs/` | Público | Documentação Swagger navegável |

## Onde ficam as regras de negócio

As regras compartilhadas pelo site e pela API ficam em dois pontos:

- `eventos/models.py`: consistência do próprio objeto, como período válido e
  conflito de sala;
- `eventos/services.py`: operações que envolvem vários objetos ou concorrência,
  como inscrições, capacidade, conflitos de agenda e cancelamentos em cascata.

As views HTML e as views da API chamam os mesmos serviços. Os serializers não
reescrevem as regras: eles chamam `full_clean()` dos models antes de salvar. Isso
evita que o site aceite algo que a API recuse, ou o contrário.

O organizador e o participante nunca são aceitos do JSON. O organizador vem de
`request.user` no serializer de evento, e o participante vem do token nos endpoints
de inscrição.

## ViewSet e views de função

- `EventoViewSet` e `AtividadeViewSet` foram escolhidos para os recursos CRUD,
  pois o router oferece URLs consistentes e reduz repetição.
- As inscrições, cancelamentos e agenda usam views com `@api_view`, pois são
  ações de negócio e não um CRUD genérico de tabelas. Elas chamam diretamente os
  serviços que o site HTML já utilizava.

## Teste central: a mesma regra nas duas portas

Regra escolhida: **uma atividade não recebe inscrições além da capacidade da
sala**.

Com as duas vagas do Laboratório 01 ocupadas e o usuário `admin_eventos`
previamente inscrito no evento, foi enviado pela API:

```http
POST /api/inscricoes/atividades/
Authorization: Token 0173a2e7d6effbb77e9cd970381d9683f71ae171
Content-Type: application/json

{"atividade": 2}
```

Resultado:

- código HTTP: `400 Bad Request`;
- corpo: `{"erros":["A atividade está lotada. Use a lista de espera."]}`;
- regra verificada em `eventos/services.py`, função `inscrever_na_atividade()`;
- o site HTML chama a mesma função por `inscrever_atividade_view()`.

Portanto, não existem duas cópias dessa regra. O teste automatizado correspondente
é `test_14_atividade_lotada_retorna_400_com_mensagem`.

## Dados demonstrativos

### Salas

| Sala | Bloco | Capacidade |
|---|---:|---:|
| Laboratório 01 | B | **2** |
| Auditório Central | A | 80 |
| Sala 12 | C | 35 |

### Eventos

- **Semana de Tecnologia 2026:** 20/10/2026, 08h–18h;
- **Jornada Científica 2026:** 20/10/2026 08h30 até 21/10/2026 17h;
- **Encontro de Egressos 2026:** 22/10/2026, inscrições fechadas.

Os eventos e atividades possuem sobreposições planejadas para demonstrar conflito
de sala, conflito de agenda e horários permitidos.

## Testes automatizados

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test -v 2
```

Resultado esperado: **63 testes aprovados** — os 37 testes do site, os 25
critérios da API e o teste do desafio opcional —, nenhuma migration pendente e
nenhuma inconsistência.

## Desafio opcional — programação em uma requisição

`GET /api/eventos/{id}/programacao/` devolve o evento, as atividades, a sala e as
vagas restantes em uma única requisição HTTP. O queryset usa `select_related` e
`prefetch_related`, de forma que a quantidade de consultas ao banco não cresce
para cada atividade serializada, evitando o problema N+1. A medição automatizada
permaneceu em **4 consultas** mesmo serializando oito atividades.

## Observação sobre o banco

O arquivo `db.sqlite3` está versionado porque as atividades exigem dados e tokens
demonstrativos prontos. A pasta `.venv` permanece ignorada.
