<h1 align="center">🖍️ Doodle</h1>

<p align="center"><strong>Transforme “não entendi” em um desenho.</strong></p>
<p align="center">Explicações ilustradas para agentes de IA. Specs curtos. Diagramas SVG fáceis de entender.</p>

<p align="center">
  <a href="https://github.com/santunesigor/doodle/actions/workflows/test.yml"><img src="https://github.com/santunesigor/doodle/actions/workflows/test.yml/badge.svg" alt="Testes"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white" alt="Python 3.8 ou mais novo"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="Licença MIT"></a>
</p>

<p align="center">
  <a href="#instalação">Instalar</a> · <a href="#uso">Usar</a> · <a href="#exemplos">Exemplos</a> ·
  <a href="docs/tutorial.pt-BR.md">Tutorial</a> · <a href="CONTRIBUTING.md">Contribuir</a> ·
  <a href="README.md">English</a>
</p>

Doodle é uma [Agent Skill](https://agentskills.io/) para **Claude Code, Codex, Cursor e outros agentes compatíveis**.
Explica bugs, fluxos de código, protocolos e conceitos em um documento Markdown para iniciantes, no seu idioma.

![Comparação entre merge e rebase gerada pelo Doodle](examples/git-rebase/img/git-rebase-pt-br-merge-ou-rebase.svg)

## Instalação

O renderizador precisa de **Python 3.8+** e usa apenas a biblioteca padrão. Não exige chaves de API nem pacotes Python.
Sem Python, a skill usa Mermaid.

Instale com a [CLI skills](https://github.com/vercel-labs/skills) e escolha seu agente:

```bash
npx skills add santunesigor/doodle --skill doodle
```

Isso instala no projeto atual. Acrescente `--global` para usar o Doodle em vários projetos.

<details>
<summary><strong>Codex</strong></summary>

Instale globalmente pelo terminal:

```bash
npx skills add santunesigor/doodle --skill doodle --agent codex --global
```

Ou peça ao Codex para usar o instalador integrado:

```text
$skill-installer install https://github.com/santunesigor/doodle/tree/main/skills/doodle
```

</details>

<details>
<summary><strong>Claude Code</strong></summary>

Rode dentro do Claude Code:

```text
/plugin marketplace add santunesigor/doodle
/plugin install doodle@doodle
```

Ou use a CLI skills:

```bash
npx skills add santunesigor/doodle --skill doodle --agent claude-code --global
```

</details>

Para instalar manualmente ou desenvolver uma cópia local, veja o [tutorial](docs/tutorial.pt-BR.md#1-instalar).
Se o agente não encontrar a skill depois da instalação, abra uma sessão nova.

## Uso

Peça com palavras normais:

```text
Me explica como o DNS funciona com desenhos. Sou iniciante.
```

```text
Não entendi esse bug. Mostra o fluxo com diagramas, usando o código deste repositório.
```

```text
Explain git rebase with drawings, in English.
```

No Codex, você também pode chamar diretamente: `$doodle me explica como o DNS funciona com desenhos`.

O agente lê as evidências relevantes, escreve `<tema>.md`, renderiza os desenhos em `img/` e responde com o caminho do documento.
Abra a prévia do Markdown no editor ou faça commit do documento e das imagens para vê-los no GitHub.

## Como funciona

O nome significa **Diagrams Over Overly Dense Long Explanations**: desenhos no lugar de explicações longas e densas.
O agente escreve uma especificação curta do desenho, em vez de código SVG:

```doodle
timeline: O que o git rebase main faz
Acha o ponto de partida | onde a sua branch saiu da main | info
Guarda os seus commits | A e B viram receitas de mudança
Pula para a ponta da main | pega o que o time já juntou
Refaz A e B | viram A' e B', com hashes novos | warn
Pronto | história em linha reta | ok
```

O renderizador cuida da disposição, das quebras de texto, das cores, dos temas claro e escuro e do estilo opcional `@sketch`.
Specs curtos deixam o código SVG fora do contexto do agente; a economia real de tokens depende do desenho e do tokenizador.

Cada explicação começa com três frases, apresenta os termos novos e desenvolve a ideia com um desenho por passo.
Quando o assunto é seu projeto, usa código, logs e caminhos de arquivos reais como evidência.

### Sete tipos de desenho

| Tipo | Melhor para |
| --- | --- |
| `timeline` | Eventos e sua ordem |
| `flow` | Decisões, desvios e caminhos |
| `cycle` | Processos que se repetem |
| `compare` | Alternativas e antes/depois |
| `tree` | Pastas e hierarquias |
| `stack` | Camadas e arquitetura |
| `sequence` | Requisições, respostas e protocolos |

Veja as opções e um exemplo de cada tipo na [referência de sintaxe](skills/doodle/references/dsl.md).

## Exemplos

| Explicação | Idioma | Diagramas |
| --- | --- | --- |
| [Por que o git rebase “reescreve a história”?](examples/git-rebase/git-rebase-pt-br.md) | Português | Timeline, compare, flow |
| [How does my browser find a website?](examples/dns/how-dns-works.md) | English | Tree, sequence, stack, cycle |

![O que o git rebase main faz, passo a passo](examples/git-rebase/img/git-rebase-pt-br-o-que-o-git-rebase-main-faz.svg)

## Rodar sem agente

```bash
python3 skills/doodle/scripts/doodle.py notas.md
python3 skills/doodle/scripts/doodle.py spec.txt -o desenho.svg
```

No modo Markdown, o comando renderiza os blocos `doodle` no próprio arquivo. Os specs ficam em comentários HTML para você
editar e renderizar novamente. Use `-o assets/diagrams` para escolher outra pasta de imagens; repita a opção nas próximas
renderizações daquele documento. Todos os blocos e caminhos de saída são validados antes de gravar os arquivos.

## Organização do repositório

```text
skills/doodle/
  SKILL.md           Instruções e gatilhos de ativação
  agents/            Metadados de apresentação no Codex
  scripts/           Renderizador Python sem dependências
  references/        Sintaxe dos desenhos
examples/            Explicações ilustradas e seus SVGs
docs/                Tutoriais em inglês e português
tests/               Testes do parser, renderizador e edição do Markdown
```

## Contribuir

Relatos de bugs, exemplos mais claros e melhorias pontuais são bem-vindos. Veja o [CONTRIBUTING.md](CONTRIBUTING.md) para
preparar o ambiente e saber o que incluir em um pull request. Você pode contribuir em português ou inglês.

```bash
python3 -m unittest discover -s tests -v
```

## Licença

[MIT](LICENSE).
