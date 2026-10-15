<h1 align="center">Doodle</h1>

<p align="center"><sub><strong>D</strong>iagrams <strong>O</strong>ver <strong>O</strong>verly <strong>D</strong>ense <strong>L</strong>ong <strong>E</strong>xplanations<br>Desenhos no lugar de explicações longas e densas.</sub></p>

<p align="center"><strong>Transforme “não entendi” em um desenho.</strong></p>
<p align="center">Explicações ilustradas para agentes de IA. Poucas linhas de texto. Diagramas SVG fáceis de entender.</p>

<p align="center">
  <a href="https://github.com/santunesigor/doodle/actions/workflows/test.yml"><img src="https://github.com/santunesigor/doodle/actions/workflows/test.yml/badge.svg" alt="Testes"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white" alt="Python 3.8 ou mais novo"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="Licença MIT"></a>
</p>

<p align="center">
  <a href="#instalação">Instalar</a> · <a href="#uso">Usar</a> · <a href="#do-seu-jeito">Personalizar</a> ·
  <a href="#exemplos">Exemplos</a> ·
  <a href="docs/tutorial.pt-BR.md">Tutorial</a> · <a href="CONTRIBUTING.md">Contribuir</a> ·
  <a href="README.md">English</a>
</p>

Doodle é uma [Agent Skill](https://agentskills.io/) para **Claude Code, Codex, Cursor e outros agentes compatíveis**.
Explica bugs, fluxos de código, protocolos e conceitos em um documento Markdown no seu nível, no seu idioma.

<p align="center">
  <img src="examples/git-rebase/img/git-rebase-pt-br-merge-ou-rebase.svg" alt="Comparação entre merge e rebase gerada pelo Doodle">
</p>

## Instalação

O renderizador precisa de **Python 3.8+** e usa apenas a biblioteca padrão. Não exige chaves de API nem pacotes Python.
Sem Python, a skill usa Mermaid.

O instalador [CLI skills](https://github.com/vercel-labs/skills) também precisa de Node.js 22.20+ com `npx` e Git.
Se não usa Node.js, escolha a opção nativa do Codex/Claude Code abaixo ou a instalação manual do tutorial.
Para usar a CLI, rode na pasta do seu projeto e escolha seu agente:

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

```text
Explica o fluxo de checkout para os devs seniores novos, a fundo, com o tema blueprint.
```

No Codex, você também pode chamar diretamente: `$doodle me explica como o DNS funciona com desenhos`.

O agente lê as evidências relevantes, escreve `<tema>.md`, renderiza os desenhos em `img/` e responde com o caminho do documento.
Abra a prévia do Markdown no editor ou faça commit do documento e das imagens para vê-los no GitHub.

## Como funciona

O agente escreve uma especificação curta do desenho, em vez de código SVG:

```doodle
timeline: O que o git rebase main faz
Acha o ponto de partida | onde a sua branch saiu da main | info
Guarda os seus commits | A e B viram receitas de mudança
Pula para a ponta da main | pega o que o time já juntou
Refaz A e B | viram A' e B', com hashes novos | warn
Pronto | história em linha reta | ok
```

O renderizador cuida da disposição, das quebras de texto, das cores, dos modos claro e escuro, de cinco temas e do estilo
opcional `@sketch`. Ele também revisa as especificações: um tom digitado errado ou uma seta para uma caixa que não existe
vira um aviso com o número da linha, para o agente corrigir antes de você ver.
Especificações curtas deixam o código SVG fora do contexto do agente; a economia real de tokens depende do desenho e do tokenizador.

Cada explicação começa com três frases, apresenta os termos novos e desenvolve a ideia com um desenho por passo.
Quando o assunto é seu projeto, usa código, logs e caminhos de arquivos reais como evidência.

### Nove tipos de desenho

| Tipo | Melhor para |
| --- | --- |
| `timeline` | Eventos e sua ordem |
| `flow` | Decisões, desvios e caminhos |
| `cycle` | Processos que se repetem |
| `compare` | Alternativas e antes/depois |
| `tree` | Pastas e hierarquias |
| `stack` | Camadas e arquitetura |
| `sequence` | Requisições, respostas e protocolos |
| `bars` | Números: tempo, tamanho, quantidade, custo |
| `hub` | Do que algo é feito; o vocabulário essencial |

Veja as opções e um exemplo de cada tipo na [referência de sintaxe](skills/doodle/references/dsl.md).

## Do seu jeito

O Doodle adapta **como escreve** e **como desenha**. Diga uma vez ao agente, por exemplo "sempre explique para devs
seniores e use o tema clean com o nosso roxo", e ele guarda isso num `doodle.json`:

```json
{
  "theme": "clean",
  "colors": {"info": "#6d28d9"},
  "audience": "developer",
  "depth": "deep",
  "language": "pt-BR",
  "docsDir": "docs/explicacoes"
}
```

| Configuração | Opções |
| --- | --- |
| `audience` | `kid` (criança), `beginner` (iniciante, padrão), `developer`, `expert` |
| `depth` | `quick` (dois desenhos), `standard`, `deep` (inclui erros comuns e um quiz) |
| `theme` | `paper` (padrão), `clean`, `candy`, `blueprint`, `chalk` |
| `colors` | uma cor `#hex` por tom; as versões do modo escuro são geradas para você |
| `scheme` | `auto` (segue o modo claro/escuro), `light`, `dark` |

Coloque no projeto (`doodle.json`, procurado da pasta do documento até a raiz do repositório) ou em
`~/.config/doodle/config.json` para todos os projetos. Um desenho isolado pode trocar de tema com `@theme chalk`.
Veja todas as configurações em [customize.md](skills/doodle/references/customize.md).

<p align="center">
  <img src="examples/themes/img/themes-can-i-deploy-paper.svg" width="49%" alt="Tema paper">
  <img src="examples/themes/img/themes-can-i-deploy-clean.svg" width="49%" alt="Tema clean">
  <img src="examples/themes/img/themes-can-i-deploy-candy.svg" width="32%" alt="Tema candy">
  <img src="examples/themes/img/themes-can-i-deploy-blueprint.svg" width="32%" alt="Tema blueprint">
  <img src="examples/themes/img/themes-can-i-deploy-chalk.svg" width="32%" alt="Tema chalk">
</p>

## Exemplos

| Explicação | Idioma | Diagramas |
| --- | --- | --- |
| [Por que o git rebase “reescreve a história”?](examples/git-rebase/git-rebase-pt-br.md) | Português | Timeline, compare, flow |
| [How does my browser find a website?](examples/dns/how-dns-works.md) | English | Tree, sequence, stack, cycle |
| [Doodle themes](examples/themes/themes.md) | English | O mesmo fluxo nos cinco temas |

<p align="center">
  <img src="examples/git-rebase/img/git-rebase-pt-br-o-que-o-git-rebase-main-faz.svg" alt="O que o git rebase main faz, passo a passo">
</p>

## Rodar sem agente

Em um terminal compatível com Bash, clone o repositório e renderize um exemplo pequeno:

```bash
git clone https://github.com/santunesigor/doodle.git
cd doodle
printf '%s\n' 'stack: Olá' 'Navegador | info' 'Servidor | ok' > demo.txt
python3 skills/doodle/scripts/doodle.py demo.txt
```

Abra o `demo.svg` gerado no navegador. Acrescente `--theme chalk` para ver outro visual, ou veja os nove tipos no
[tutorial](docs/tutorial.pt-BR.md#5-escrever-os-seus-próprios-desenhos).

Para um arquivo Markdown com blocos `doodle`, rode `python3 skills/doodle/scripts/doodle.py notas.md` na raiz do repositório.
Isso **altera o próprio `notas.md`**. As especificações ficam em comentários HTML para editar e renderizar novamente.
Para guardar as imagens em outra pasta, use `"imageDir": "assets/diagrams"` no `doodle.json` (ou passe `-o assets/diagrams` em toda execução).
No modo Markdown, as especificações e os caminhos dos SVGs são verificados antes de gravar os arquivos; `--check` valida e
revisa sem gravar nada.

## Organização do repositório

```text
skills/doodle/
  SKILL.md           Instruções e gatilhos de ativação
  agents/            Metadados de apresentação no Codex
  scripts/           Renderizador Python sem dependências
  references/        Sintaxe dos desenhos e personalização
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
