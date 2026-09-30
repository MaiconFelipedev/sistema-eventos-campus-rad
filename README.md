# Sistema de Inscrições em Eventos do Campus

Projeto Django desenvolvido para a atividade de ponto extra da disciplina de Rapid Application Development (RAD), no IFPB.

## Integrante

- Maicon Felipe da Silva Souza

## O que o sistema faz

- apresenta uma lista pública de eventos e a programação completa;
- oferece cadastro, login e logout com recursos nativos do Django;
- permite que organizadores gerenciem somente seus próprios eventos e atividades;
- permite inscrição e cancelamento em eventos e atividades;
- calcula vagas diretamente do banco usando a capacidade da sala;
- bloqueia conflitos de sala e de agenda, inclusive entre eventos diferentes;
- mostra a agenda pessoal ordenada por data e hora;
- oferece painel restrito com os inscritos dos eventos do organizador;
- implementa o desafio opcional de lista de espera com promoção automática.

## Tecnologias

- Python 3
- Django 5.2.17
- SQLite
- HTML e CSS

Não são utilizadas bibliotecas de terceiros além do Django.

## Como executar

### PowerShell

```powershell
cd C:\Users\maicon.felipe\Documents\RAD\eventos-campus-django
.\.venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py configurar_eventos
python manage.py runserver 127.0.0.1:8009
```

### Git Bash

```bash
cd /c/Users/maicon.felipe/Documents/RAD/eventos-campus-django
source .venv/Scripts/activate
python manage.py migrate
python manage.py configurar_eventos
python manage.py runserver 127.0.0.1:8009
```

Acesse `http://127.0.0.1:8009/`.

## Contas de teste

Todas usam a senha `Eventos@2026`.

| Usuário | Papel | Finalidade |
|---|---|---|
| `admin_eventos` | Superusuário | Cadastrar e conferir salas no Admin |
| `organizador2` | Organizador | Gerenciar a Semana de Tecnologia |
| `organizador3` | Organizador | Gerenciar a Jornada Científica e testar propriedade |
| `participante4` | Participante | Inscrições e agenda |
| `participante5` | Participante | Ocupar a última vaga da sala pequena |

Admin: `http://127.0.0.1:8009/admin/`.

## Mapa dos dados demonstrativos

### Salas

| Sala | Bloco | Capacidade |
|---|---:|---:|
| Laboratório 01 | B | **2** |
| Auditório Central | A | 80 |
| Sala 12 | C | 35 |

### Eventos

- **Semana de Tecnologia 2026:** 20/10/2026, das 08h às 18h, inscrições abertas.
- **Jornada Científica 2026:** 20/10/2026 às 08h30 até 21/10/2026 às 17h, inscrições abertas. Seu período cruza com a Semana de Tecnologia.
- **Encontro de Egressos 2026:** 22/10/2026, das 09h às 17h, inscrições fechadas.

### Atividades e sobreposições

- **Abertura da Semana de Tecnologia:** Auditório Central, 20/10, 09h–10h30.
- **Painel de Pesquisa Aplicada:** Sala 12, 20/10, 09h–10h30. Simultâneo à abertura, mas em outra sala.
- **Minicurso de Dados:** Laboratório 01, 20/10, 09h–10h30. Simultâneo às duas atividades anteriores.
- **Oficina Django:** Laboratório 01, 20/10, 14h–16h. Usa a mesma sala do minicurso em outro horário e começa lotada pelos participantes 4 e 5.

Esses dados permitem demonstrar limite de vagas, conflito entre eventos, sala ocupada e horários não conflitantes.

## Testes

```powershell
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
```

Resultado esperado: **37 testes aprovados**, nenhuma inconsistência e nenhuma migration pendente.

Os testes cobrem os 27 critérios de aceitação, as restrições técnicas e o desafio opcional.

## Requisitos pendentes

Nenhum requisito obrigatório ficou pendente. O desafio opcional de lista de espera também foi implementado.

## Observação sobre o banco

O arquivo `db.sqlite3` está versionado exclusivamente porque a atividade exige os dados demonstrativos prontos. A pasta `.venv` permanece ignorada.
