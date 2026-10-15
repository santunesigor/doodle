# Doodle 🖍️

**D**iagrams **O**ver **O**verly **D**ense **L**ong **E**xplanations ("desenhos no lugar de explicações longas e densas").

Uma skill para agentes de IA (Claude Code, Codex, Cursor…) que explica qualquer coisa (um bug, um fluxo do código,
um protocolo, um conceito) em **um arquivo Markdown com desenhos limpos e simpáticos**, pensado para iniciantes.

> [Read in English](README.md)

![O que o git rebase main faz](examples/git-rebase/img/git-rebase-pt-br-o-que-o-git-rebase-main-faz.svg)

## Por quê

Pedir para uma IA "desenhar" costuma terminar de um destes dois jeitos:

- **SVG escrito à mão** fica bonito, mas gasta uns 1.000 tokens por desenho, e setas e textos saem desalinhados.
- **Mermaid** é barato, mas tem cara genérica e não cobre todo tipo de desenho.

No Doodle, o agente escreve um **spec de texto curtinho**. Um script Python sem dependências transforma esse spec
em um SVG caprichado, com modo escuro, quebra de texto automática e cores consistentes.

```doodle
timeline: O que o git rebase main faz
Acha o ponto de partida | onde a sua branch saiu da main | info
Guarda os seus commits | A e B viram "receitas" de mudança
Pula para a ponta da main | pega o que o time já juntou
Refaz A e B | viram A' e B', com hashes novos | warn
Pronto | história em linha reta | ok
```

Essas 6 linhas geram a imagem acima. Nos nossos testes, os mesmos 4 desenhos custaram **1,4 KB de spec, contra 15,3 KB
de SVG à mão: cerca de 11 vezes menos tokens**. E o agente nunca precisa ler os SVGs de volta.

## O que você ganha

- **Uma estrutura de explicação que funciona:** resumo em três frases → "peças que você precisa conhecer" →
  um desenho por passo → por que importa → provas.
- **7 tipos de desenho:** `timeline`, `flow`, `cycle`, `compare`, `tree`, `stack` e `sequence`.
- **Fica bonito em qualquer lugar:** GitHub, VS Code e Obsidian, no **tema claro e no escuro**. Há também o estilo
  `@sketch`, com cara de desenho à mão.
- **Escrito no seu idioma:** você pede em português, a explicação sai em português.
- **Sem dependências:** só Python 3.8+. Sem Python, o agente usa Mermaid.

## Instalação

**Claude Code** (marketplace de plugins):

```
/plugin marketplace add santunesigor/doodle
/plugin install doodle@doodle
```

**Qualquer agente com suporte a skills** (Codex, Cursor, Claude Code…), via [skills](https://skills.sh):

```bash
npx skills add santunesigor/doodle
```

**Manual:**

```bash
git clone https://github.com/santunesigor/doodle
cp -r doodle/skills/doodle ~/.claude/skills/
```

## Uso

**Primeira vez? Siga o [tutorial de 10 minutos](docs/tutorial.pt-BR.md).**

É só pedir:

> me explica como o DNS funciona com desenhos
>
> não entendi esse bug, me mostra com imagens

O agente escreve `<tema>.md`, roda o renderizador e te passa o caminho do arquivo.

Você também pode rodar o renderizador direto:

```bash
python3 skills/doodle/scripts/doodle.py notas.md   # renderiza cada bloco ```doodle no próprio arquivo
python3 skills/doodle/scripts/doodle.py spec.txt   # um spec -> spec.svg
```

Os blocos renderizados ficam no arquivo como comentários `<!-- doodle ... -->`. Dá para editar e rodar de novo.

## Exemplos

- [Por que o `git rebase` "reescreve a história"?](examples/git-rebase/git-rebase-pt-br.md) (português: timeline, compare, flow)
- [How does my browser find a website?](examples/dns/how-dns-works.md) (inglês: tree, sequence, stack, cycle)

A sintaxe completa está em [skills/doodle/references/dsl.md](skills/doodle/references/dsl.md).

## Desenvolvimento

```bash
python3 -m unittest discover -s tests
```

## Licença

MIT
