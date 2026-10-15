# Tutorial do Doodle

> [Read in English](tutorial.md)

Este tutorial leva uns 10 minutos. Você vai instalar o Doodle, pedir a sua primeira explicação ilustrada, mudar um
desenho e aprender a escrever desenhos por conta própria.

## 1. Instalar

Você precisa de **Python 3.8 ou mais novo**. Confira com `python3 --version`.

Escolha um dos jeitos abaixo.

**Claude Code** (marketplace de plugins), dentro de uma sessão do Claude Code:

```
/plugin marketplace add santunesigor/doodle
/plugin install doodle@doodle
```

**Codex, Cursor, Claude Code e outros agentes com suporte a skills:**

```bash
npx skills add santunesigor/doodle
```

**Manual** (qualquer agente que leia `~/.claude/skills`):

```bash
git clone https://github.com/santunesigor/doodle
cp -r doodle/skills/doodle ~/.claude/skills/
```

**Para testar uma cópia local antes de publicar:** crie um link em vez de copiar a pasta. Assim as suas edições
valem na hora.

```bash
ln -s /caminho/para/doodle/skills/doodle ~/.claude/skills/doodle
```

Abra uma sessão **nova** depois de instalar, porque as skills são carregadas quando a sessão começa. Para conferir,
pergunte "quais skills você tem?". O `doodle` deve aparecer na lista.

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

## 3. Todo documento tem o mesmo formato

O Doodle escreve sempre na mesma ordem, pensada para a ficha cair:

1. **Em três frases:** o que acontece, por que acontece e o que resolve.
2. **Peças que você precisa conhecer:** uma tabela curta com os termos novos.
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
python3 ~/.claude/skills/doodle/scripts/doodle.py como-o-dns-funciona.md
```

Rodar de novo é sempre seguro. O comando redesenha todas as imagens do arquivo e não mexe no resto do texto.

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

A sintaxe completa, com todas as opções, está em
[skills/doodle/references/dsl.md](../skills/doodle/references/dsl.md) (em inglês).

### Opções

Coloque cada opção numa linha própria, logo depois do título:

- `@sketch` dá cara de desenho à mão.
- `@vertical` ou `@horizontal` força a direção de um `timeline` ou `flow`.
- `@arrow` desenha setas entre as colunas do `compare` ou as camadas do `stack`.

### Renderizar um desenho sozinho

Salve o bloco (sem as cercas ```) num arquivo `.txt`:

```bash
python3 doodle.py pizza.txt               # cria pizza.svg
python3 doodle.py pizza.txt -o saida.svg  # escolhe o nome
echo "stack: Oi
A
B" | python3 doodle.py - > oi.svg         # lê da entrada padrão
```

## 6. Problemas comuns

| Problema | Solução |
|---|---|
| `error: line 3: unknown kind 'pizza'` | A primeira linha precisa começar com um dos 7 tipos, em inglês. |
| `error: 'cycle' needs at least 2 rows` | Acrescente linhas ou escolha outro tipo. |
| Um texto virou o tom | A última célula que é exatamente uma palavra de tom (`ok`, `bad`…) vira o tom. Reescreva, por exemplo `status \| tudo certo`. |
| Uma caixa ficou alta demais | Use rótulos de até 4 palavras e notas de até 12, ou divida a ideia em dois desenhos. |
| As imagens não aparecem no GitHub | Faça commit da pasta `img/` junto com o `.md`. |
| Não tem Python na máquina | O agente escreve blocos ` ```mermaid ` no lugar. O GitHub também mostra esses blocos, com visual mais simples. |
| A skill não é usada | Abra uma sessão nova depois de instalar, ou peça direto: "usa a skill doodle". |
