# Tutorial do Doodle

> [Read in English](tutorial.md)

Este tutorial leva uns 10 minutos. Você vai instalar o Doodle, pedir a sua primeira explicação ilustrada, mudar um
desenho e aprender a escrever desenhos por conta própria.

## 1. Instalar

Você precisa de **Python 3.8 ou mais novo**. Confira com `python3 --version`.
O instalador com `npx` também precisa de Node.js 22.20+ e Git; as opções de plugin nativo e instalação manual abaixo dispensam Node.js.
Os exemplos de terminal usam sintaxe Bash (Linux, macOS, WSL ou Git Bash).

Escolha um dos jeitos abaixo.

**Claude Code** (marketplace de plugins), dentro de uma sessão do Claude Code:

```
/plugin marketplace add santunesigor/doodle
/plugin install doodle@doodle
```

**Codex, Cursor, Claude Code e outros agentes com suporte a skills:**

```bash
npx skills add santunesigor/doodle --skill doodle
```

A CLI instala no projeto atual por padrão. Para instalar globalmente em um agente, use:

```bash
npx skills add santunesigor/doodle --skill doodle --agent codex --global
```

Troque `codex` por `claude-code` ou `cursor` para esses agentes.

**Manual (Codex):**

```bash
git clone https://github.com/santunesigor/doodle
mkdir -p ~/.agents/skills
cp -R doodle/skills/doodle ~/.agents/skills/
```

Para o Claude Code, use `~/.claude/skills` como destino. Instale em uma pasta `doodle` nova para não mesclar os arquivos
com uma cópia existente.

**Para testar uma cópia local antes de publicar (Codex):** na raiz do repositório, crie um link em vez de copiar a pasta.
Assim as suas edições valem na hora. Escolha entre a cópia acima e este link:

```bash
mkdir -p ~/.agents/skills
ln -s "$PWD/skills/doodle" ~/.agents/skills/doodle
```

Se o agente não encontrar a skill depois da instalação, abra uma sessão **nova**. Para conferir, pergunte "quais skills
você tem?". O `doodle` deve aparecer na lista. No Codex, você pode chamá-la com `$doodle`.

## 2. A sua primeira explicação

Peça com palavras normais, em qualquer idioma:

> Me explica como o DNS funciona com desenhos. Sou iniciante.

O agente vai:

1. ler o código, os logs ou a documentação, se o assunto for do seu projeto;
2. escrever `como-o-dns-funciona.md` (o nome vem do assunto), com os desenhos como blocos curtos de texto;
3. rodar o renderizador, que cria as imagens em `img/`;
4. responder com o caminho do arquivo e um resumo curto.

Para ler, abra o arquivo `.md`:

- **VS Code:** `Ctrl+Shift+V` (`Cmd+Shift+V` no Mac) abre a pré-visualização.
- **GitHub:** faça commit do `.md` **e** da pasta `img/`. Os desenhos seguem o seu tema, claro ou escuro.
- **Obsidian:** abra a pasta como um vault.

Veja resultados prontos em [examples/git-rebase](../examples/git-rebase/git-rebase-pt-br.md) e
[examples/dns](../examples/dns/how-dns-works.md).

### Como pedir bem

| Você quer | Peça assim |
|---|---|
| Entender um bug no seu código | "Não entendo por que o `checkout()` falha duas vezes. Me explica com desenhos, usando os logs em `logs/hoje.txt`." |
| Entender um conceito | "Me explica OAuth com imagens, como se eu tivesse 5 anos." |
| Um idioma específico | "Explain it with drawings, in English." (a resposta já segue o idioma em que você escreve) |
| Um nome ou lugar para o arquivo | "…e salva em `docs/explicacoes/`." |
| Visual de desenho à mão | "…usa o estilo sketch." |
| Outro leitor | "…para uma criança de 10 anos." / "…para devs seniores, pula o básico." |
| Mais ou menos detalhe | "Versão rápida, por favor." / "Vai a fundo e me faz um quiz no final." |
| Outro visual | "…com o tema chalk." / "…no roxo da nossa marca, #6d28d9." |
| Sempre do mesmo jeito | "De agora em diante, explica sempre para devs com o tema clean." (fica salvo no `doodle.json`) |

## 3. Todo documento tem o mesmo formato

O Doodle escreve sempre na mesma ordem, pensada para a ficha cair. Uma explicação `quick` fica só com a primeira parte
e um ou dois desenhos; uma `deep` acrescenta "Erros comuns" e um quiz curto para você se testar.

1. **Em três frases:** a ideia principal, como funciona e por que importa (ou o que resolve o problema).
2. **Peças que você precisa conhecer:** uma tabela curta quando houver pelo menos três termos novos.
3. **Passos:** cada passo faz uma afirmação, com um desenho e alguns tópicos que terminam no "por quê".
4. **Quando acontece / Por que importa.**
5. **Provas:** logs, números e caminhos de arquivo reais. Essa seção só aparece quando existe prova de verdade.

## 4. Mudar um desenho

Depois de renderizado, cada desenho fica no arquivo como um comentário logo acima da imagem:

```
<!-- doodle
cycle: O ciclo do cache
Consulta completa | percorre a árvore (lento) | info
Resposta guardada | fica pelo tempo do TTL | ok
-->
![O ciclo do cache](img/como-o-dns-funciona-o-ciclo-do-cache.svg)
```

Você tem dois jeitos de mudar:

- **Pedir ao agente:** "No desenho 2, marca o passo do cache como problema e acrescenta um passo para quando o TTL vence."
- **Editar você mesmo:** mude o texto dentro do comentário e rode o renderizador de novo:

```bash
python3 ~/.agents/skills/doodle/scripts/doodle.py como-o-dns-funciona.md
```

Esse caminho é o da instalação manual no Codex; para uma cópia manual no Claude Code, use `~/.claude/skills`.
Se instalou pelo marketplace de plugins, peça ao agente para renderizar o documento de novo; a pasta do plugin pode ser outra.
O comando redesenha as imagens e preserva o texto ao redor. Specs ou caminhos de saída inválidos deixam o documento e as
imagens existentes intactos. Se escolheu outra pasta de imagens com `-o`, repita a opção em cada renderização,
ou defina `imageDir` uma vez no `doodle.json` (veja a [seção 6](#6-do-seu-jeito)).

## 5. Escrever os seus próprios desenhos

Dá para usar o Doodle sem agente. Escreva um bloco ` ```doodle ` em qualquer arquivo Markdown e rode o renderizador
nele.

Todo bloco tem o mesmo formato:

```doodle
timeline: Um pedido de pizza
> o subtítulo é opcional
Pedido feito | o app manda para a pizzaria | info
Forno cheio | espera 20 minutos | warn
Entregue | ainda quente | ok
```

- **A primeira linha** é `tipo: Título`. O tipo fica em inglês.
- **Cada linha** é `rótulo | nota | tom`. Só o rótulo é obrigatório.
- **Os tons** contam a história: `ok` é verde (o caminho saudável ou a correção), `bad` é vermelho (a parte quebrada),
  `warn` é amarelo (o passo arriscado), `info` é azul (um ator ou uma entrada) e `neutral` é cinza (o padrão).

### Qual tipo usar

| A pergunta que você quer responder | Tipo |
|---|---|
| Em que ordem as coisas acontecem? | `timeline` |
| O que decide o quê? Onde o caminho se divide? | `flow` |
| Por que isso fica se repetindo? | `cycle` |
| O que mudou? Qual opção é melhor? | `compare` |
| Onde fica? O que está dentro do quê? | `tree` |
| O que fica em cima do quê? | `stack` |
| Quem conversa com quem? | `sequence` |
| Quanto? Quanto tempo? | `bars` |
| Do que isso é feito? | `hub` |

### Um exemplo pequeno de cada

```doodle
flow: Posso subir para produção?
[a] Testes passaram? | warn
[b] Sobe | ok
[c] Corrige antes | bad
a -> b: sim
a -> c: não
c -> a: tenta de novo
```

```doodle
compare: Senha ou passkey?
@arrow
## Senha | bad
Dá para adivinhar
Cai em phishing
## Passkey | ok
Nada para adivinhar
Presa ao site verdadeiro
```

```doodle
tree: Onde fica a configuração
app/
  config/
    default.json | valores base
    prod.json | sobrescreve o default | warn
  main.py
```

```doodle
stack: Um app web
@arrow
Navegador | o que a pessoa vê | info
Servidor da API
Banco de dados | onde os dados moram | ok
```

```doodle
sequence: Fazendo login
Usuário | info
Usuário -> App: e-mail + senha
App -> Banco: confere a senha
Banco ~> App: confere | ok
App ~> Usuário: bem-vindo! | ok
```

```doodle
cycle: O ciclo de code review
Escreve o código | info
Abre o pull request
Revisão pede mudanças | warn
Corrige e envia | ok
```

```doodle
bars: Tempo de build por etapa
Instalar | 40 s
Testes | 95 s | warn
Empacotar | 25 s | ok
```

```doodle
hub: O que um commit guarda
Commit | info
Foto dos arquivos | todos, como estavam
Pai | o commit anterior
Autor | quem e quando
Mensagem | por que mudou
```

A sintaxe completa, com todas as opções, está em
[skills/doodle/references/dsl.md](../skills/doodle/references/dsl.md) (em inglês).

### Opções

Coloque cada opção numa linha própria, logo depois do título:

- `@sketch` dá cara de desenho à mão.
- `@vertical` ou `@horizontal` força a direção de um `timeline` ou `flow`.
- `@arrow` desenha setas entre as colunas do `compare`, as camadas do `stack` ou a partir do centro de um `hub`.
- `@theme chalk` desenha só esse desenho em outro tema.

### Renderizar um desenho sozinho

Em uma cópia local deste repositório, salve o exemplo da pizza acima (sem as cercas) como `pizza.txt` na raiz.
Se ainda não tem uma cópia, rode `git clone https://github.com/santunesigor/doodle.git` e depois `cd doodle`.
Na raiz do repositório:

```bash
python3 skills/doodle/scripts/doodle.py pizza.txt
python3 skills/doodle/scripts/doodle.py pizza.txt -o saida.svg
printf '%s\n' 'stack: Oi' 'A' 'B' | python3 skills/doodle/scripts/doodle.py - > oi.svg
```

Isso cria `pizza.svg`, `saida.svg` e `oi.svg`. Abra um SVG no navegador para ver o desenho.
Para renderizar Markdown, use o mesmo comando com o caminho do `.md`; o comando altera o próprio arquivo.
Acrescente `--check` para só validar: nada é gravado, e o renderizador lista erros e avisos com o número da linha.

## 6. Do seu jeito

O Doodle lê as suas preferências de um `doodle.json`. Crie um no seu projeto com:

```bash
python3 skills/doodle/scripts/doodle.py --init
```

Depois mude só o que importa para você. Tudo é opcional:

```json
{
  "theme": "candy",
  "audience": "kid",
  "depth": "quick",
  "language": "pt-BR",
  "notes": "Use metáforas de futebol."
}
```

- **Como desenha:** `theme` (`paper`, `clean`, `candy`, `blueprint`, `chalk`), `sketch`, `colors` (uma cor `#hex`
  por tom), `scheme` (`auto`, `light`, `dark`) e `imageDir`. Experimente com `--theme NOME`, ou veja todos lado a lado
  na [galeria de temas](../examples/themes/themes.md).
- **Como escreve:** `audience` (`kid`, `beginner`, `developer`, `expert`), `depth` (`quick`, `standard`, `deep`),
  `language`, `docsDir` (onde salvar as explicações novas) e `notes` (as regras da casa, em palavras normais).

O Doodle procura o `doodle.json` mais próximo, da pasta do documento até a raiz do repositório. Padrões para todos os
seus projetos ficam em `~/.config/doodle/config.json`. Rode `doodle.py --settings` para ver o que está valendo.
Você não precisa editar JSON: diga ao agente "de agora em diante, sempre…" e ele salva a preferência.
Todas as configurações estão em [customize.md](../skills/doodle/references/customize.md) (em inglês).

## 7. Problemas comuns

| Problema | Solução |
|---|---|
| `error: notas.md:3: unknown kind 'pizza'` | A primeira linha precisa começar com um dos 9 tipos, em inglês. |
| `error: cycle needs at least 2 rows` | Acrescente linhas ou escolha outro tipo. |
| `warning: … 'Hom' matches no node` | Uma seta do `flow` cita uma caixa que não existe, então uma nova foi criada. Corrija o nome ou use o `[id]`. |
| `warning: … 'warnn' is shown as a note` | Um tom digitado errado. Corrija a grafia. |
| Uma nota virou um tom | A última célula que é exatamente uma palavra de tom (`ok`, `bad`…) vira o tom. Reescreva, por exemplo `status \| tudo certo`. |
| Uma caixa ficou alta demais | Use rótulos de até 4 palavras e notas de até 12, ou divida a ideia em dois desenhos. |
| As imagens não aparecem no GitHub | Faça commit da pasta `img/` junto com o `.md`. |
| Não tem Python na máquina | O agente escreve blocos ` ```mermaid ` no lugar. O GitHub também mostra esses blocos, com visual mais simples. |
| `npx: command not found` | Instale Node.js ou escolha a instalação por plugin nativo/manual. |
| `SVG output must stay inside 'img'` | Se usou `-o assets/diagrams` antes, repita a opção, ou defina `imageDir` no `doodle.json`. Mantenha os links das imagens dentro da pasta escolhida. |
| A skill não é usada | Abra uma sessão nova depois de instalar, ou peça direto: "usa a skill doodle". |
