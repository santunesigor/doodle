# Por que o `git rebase` "reescreve a história"?

## Em três frases

1. Cada commit guarda **quem é o pai dele**, e o ID (hash) do commit depende do conteúdo **e** desse pai.
2. O rebase pega os seus commits e os **refaz em cima de outro ponto**. Eles ganham um pai novo e, por isso, IDs novos.
3. Se outra pessoa já tinha os commits antigos, a história dela e a sua **deixam de bater**.

---

## Peças que você precisa conhecer

| Peça | O que é |
|---|---|
| **Commit** | Uma "foto" do projeto, com uma mensagem e um ponteiro para o commit anterior (o pai). |
| **Hash** | O ID do commit, como `a1b2c3d`. É calculado a partir do conteúdo e do pai. |
| **Branch** | Uma etiqueta que aponta para o último commit de uma linha de trabalho. |
| **main** | A branch principal, onde o time junta o trabalho. |

---

## Passo 1: o que o `git rebase main` faz, na ordem

<!-- doodle
timeline: O que o git rebase main faz
Acha o ponto de partida | onde a sua branch saiu da main | info
Guarda os seus commits | A e B viram "receitas" de mudança
Pula para a ponta da main | pega o que o time já juntou
Refaz A e B | viram A' e B', com hashes novos | warn
Pronto | história em linha reta | ok
-->
![O que o git rebase main faz](img/git-rebase-pt-br-o-que-o-git-rebase-main-faz.svg)

- O conteúdo de A' é igual ao de A, mas **o pai mudou**, então o hash muda.
- Os commits antigos A e B não são apagados na hora. Eles só **ficam sem nenhuma branch apontando** para eles.

---

## Passo 2: merge e rebase chegam ao mesmo código por caminhos diferentes

<!-- doodle
compare: Merge ou rebase?
## Merge | junta as duas linhas | info
Cria um commit de merge | warn
Não muda nenhum hash | ok
Seguro em branch compartilhada | ok
## Rebase | refaz a sua linha em cima da outra | info
História em linha reta | ok
Muda os hashes dos seus commits | warn
Perigoso em branch compartilhada | bad
-->
![Merge ou rebase?](img/git-rebase-pt-br-merge-ou-rebase.svg)

- O código final é o mesmo. **O que muda é o desenho da história.**

---

## Passo 3: a regra prática

<!-- doodle
flow: Posso dar rebase?
[a] Quero atualizar a minha branch
[b] Alguém já baixou essa branch? | warn
[c] Pode dar rebase | ok
[d] Use merge | info
a -> b
b -> c: não
b -> d: sim
-->
![Posso dar rebase?](img/git-rebase-pt-br-posso-dar-rebase.svg)

- Se a branch **só existe na sua máquina**, ou só você mexe nela, o rebase deixa a história limpa sem incomodar ninguém.
- Se outra pessoa já baixou a branch, os commits dela apontam para hashes que "sumiram". O próximo `git pull` dela
  vira uma bagunça de commits repetidos.

---

## Quando isso dá problema

O problema só aparece quando **as duas coisas** acontecem juntas:

1. você deu rebase em commits que **já estavam no servidor**; e
2. alguém **já tinha baixado** esses commits.

Nesse caso, você precisa de `git push --force` para subir a branch, e o colega precisa refazer o trabalho dele em
cima da nova história.
