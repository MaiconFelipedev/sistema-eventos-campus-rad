# Roteiro para acompanhar o desenvolvimento no VS Code

Este arquivo mostra, na ordem, onde cada parte foi implementada e o que observar.

## 1. Abrir o projeto

1. Abra o VS Code.
2. Escolha **Arquivo > Abrir Pasta**.
3. Selecione `C:\Users\maicon.felipe\Documents\RAD\eventos-campus-django`.
4. Pressione `Ctrl+Shift+P`, escolha **Python: Select Interpreter** e selecione `.venv\Scripts\python.exe`.

## 2. Configuração do Django

Abra `config/settings.py` e confira:

- `eventos.apps.EventosConfig` em `INSTALLED_APPS`;
- SQLite em `DATABASES`;
- idioma `pt-br` e fuso `America/Sao_Paulo`;
- pasta global de templates e CSS;
- redirecionamentos de autenticação.

Abra `config/urls.py` para ver login e logout nativos, cadastro público e inclusão de `eventos.urls`.

## 3. Modelagem

Abra `eventos/models.py`.

1. `Sala`: nome, bloco e capacidade mínima 1.
2. `Evento`: período, inscrições abertas e organizador preenchido pelo sistema.
3. `Atividade`: evento, tipo, responsável, sala e intervalo de data/hora.
4. `InscricaoEvento`: relação única entre evento e participante.
5. `InscricaoAtividade`: liga a atividade à inscrição no evento; `CASCADE` garante o cancelamento conjunto.
6. `ListaEspera`: desafio opcional, ordenado pela chegada.

No método `Atividade.clean`, observe a fórmula de sobreposição:

```python
inicio__lt=self.fim,
fim__gt=self.inicio,
```

Ela detecta interseções parciais e também quando um intervalo contém o outro. Horários que apenas se encostam são permitidos.

## 4. Migration e banco

Abra `eventos/migrations/0001_initial.py`. Ela cria as tabelas e restrições de unicidade.

Para reproduzir no terminal:

```powershell
python manage.py makemigrations
python manage.py migrate
```

## 5. Formulários

Abra `eventos/forms.py`.

- `CadastroForm` reaproveita `UserCreationForm`.
- `EventoForm` não expõe o organizador.
- `AtividadeForm` recebe o evento pela URL e não permite escolhê-lo no formulário.
- Datas usam campos `datetime-local`.

## 6. Papéis e autorização

Abra `eventos/permissions.py`.

- O papel é conferido pelo grupo `Organizadores`.
- `OrganizadorRequiredMixin` protege as views de classe.
- Nenhuma autorização depende de `is_superuser`.

Abra `eventos/context_processors.py` para ver como o template recebe o papel do usuário.

## 7. Regras de negócio

Abra `eventos/services.py`.

- `inscrever_no_evento`: recusa evento fechado e duplicidade.
- `inscrever_na_atividade`: exige inscrição no evento, verifica capacidade e conflito global.
- `cancelar_atividade`: remove apenas uma atividade e libera a vaga.
- `cancelar_evento`: remove a inscrição e todas as atividades relacionadas.
- `entrar_na_lista_espera`: exige evento e atividade lotada.
- `promover_primeiro_elegivel`: promove a primeira pessoa sem conflito atual.

As operações usam `transaction.atomic()` e consultam o banco no momento do envio.

## 8. Views e URLs

Abra `eventos/views.py` e `eventos/urls.py`.

- Lista e detalhe são públicos.
- CRUD exige grupo de organizador e filtra pelo proprietário.
- Agenda exige login e filtra pelo usuário atual.
- Painel mostra apenas eventos do organizador logado.
- Ações de inscrição e cancelamento usam `@login_required` e `@require_POST`.

Isso atende à exigência de proteção por mixin e por decorador.

## 9. Admin

Abra `eventos/admin.py`.

Cada entidade tem colunas relevantes, filtros e pesquisa. Salas são cadastradas e conferidas pelo Admin.

## 10. Interface

Abra:

- `templates/base.html`: navegação conforme o papel;
- `templates/eventos/evento_list.html`: lista pública;
- `templates/eventos/evento_detail.html`: programação, vagas e ações condicionais;
- `templates/eventos/minha_agenda.html`: agenda pessoal e posições na fila;
- `templates/eventos/painel_organizador.html`: inscritos por atividade;
- `static/css/app.css`: layout responsivo.

Esconder o botão melhora a interface, mas a proteção real permanece nos services e views.

## 11. Dados demonstrativos

Abra `eventos/management/commands/configurar_eventos.py`.

O comando cria as cinco contas, três salas, eventos cruzados e atividades simultâneas. As senhas são criadas com `set_password`, nunca atribuídas diretamente.

Execute:

```powershell
python manage.py configurar_eventos
```

O comando é idempotente: pode ser executado novamente sem duplicar os dados principais.

## 12. Testes

Abra `eventos/tests.py`.

- `CriteriosAceitacaoTests`: testes numerados de 01 a 27 conforme o PDF.
- `RestricoesTecnicasTests`: POST, isolamento da agenda e casos de sobreposição.
- `ListaEsperaTests`: ordem, posição, promoção automática e conflito posterior.

Execute:

```powershell
python manage.py test
```

Resultado esperado: `Ran 37 tests` e `OK`.

## 13. Teste manual no navegador

1. Execute `python manage.py runserver 127.0.0.1:8009`.
2. Abra `http://127.0.0.1:8009/` sem login e confira as páginas públicas.
3. Entre como `participante4` / `Eventos@2026` e confira **Minha agenda**.
4. Entre como `organizador2` / `Eventos@2026` e confira edição, atividades e painel.
5. Entre como `organizador3` e tente acessar pela URL um evento do organizador 2.
6. Entre como `admin_eventos` no `/admin/` para conferir as salas.
7. Cadastre uma nova conta e confirme que ela não recebe opções de organizador.

## 14. Estrutura final da entrega

O repositório conterá:

- projeto completo;
- migration inicial;
- `requirements.txt`;
- `db.sqlite3` com dados;
- `README.md` com contas e mapa dos dados;
- este roteiro;
- `.venv` fora do Git.
