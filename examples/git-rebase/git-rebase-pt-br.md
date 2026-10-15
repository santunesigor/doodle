# Por que o `git rebase` "reescreve a história"?

## Em três frases

1. Cada commit guarda o conteúdo e, normalmente, um ou mais pais; seu ID (hash) depende desses dados e dos metadados.
2. O rebase pega os seus commits e os **refaz em cima de outro ponto**. Eles ganham um pai novo e, por isso, IDs novos.
3. Se outra pessoa já tinha os commits antigos, a história dela e a sua **deixam de bater**.

---

## Peças que você precisa conhecer

| Peça | O que é |
|---|---|
| **Commit** | Uma "foto" do projeto com mensagem, autoria e referências aos pais. O primeiro não tem pai; um merge pode ter vários. |
| **Hash** | O ID do commit, como `a1b2c3d`. Depende do conteúdo, dos pais e dos metadados, como autoria e mensagem. |
| **Branch** | Uma etiqueta que aponta para o último commit de uma linha de trabalho. |
| **main** | A branch principal, onde o time junta o trabalho. |

---

## Passo 1: o que o `git rebase main` faz, na ordem

Neste exemplo, sua branch tem os commits A e B, e a `main` avançou desde que você criou a branch.
Você roda `git rebase main` estando na sua branch.

<!-- doodle
timeline: O que o git rebase main faz
Acha o ponto de partida | onde a sua branch saiu da main | info
Guarda os seus commits | A e B viram "receitas" de mudança
Pula para a ponta da main | pega o que o time já juntou
Refaz A e B | viram A' e B', com hashes novos | warn
Pronto | história em linha reta | ok
-->
![O que o git rebase main faz](img/git-rebase-pt-br-o-que-o-git-rebase-main-faz.svg)

- A' reaplica **a mudança de A sobre a nova base**. O conteúdo completo pode mudar, porque inclui as mudanças da `main`.
- O pai mudou, então o hash também muda. Se houver conflito, você precisa resolvê-lo antes de continuar.
- Os commits antigos A e B não são apagados na hora. A sua branch deixa de apontar para eles, mas outras referências
  podem mantê-los acessíveis.

---

## Passo 2: merge e rebase chegam ao mesmo código por caminhos diferentes

<!-- doodle
compare: Merge ou rebase?
## Merge | junta as duas linhas | info
Pode criar commit de merge | warn
Não muda nenhum hash | ok
Seguro em branch compartilhada | ok
## Rebase | refaz a sua linha em cima da outra | info
História em linha reta | ok
Muda os hashes dos seus commits | warn
Perigoso em branch compartilhada | bad
-->
![Merge ou rebase?](img/git-rebase-pt-br-merge-ou-rebase.svg)

- Quando não há conflitos e as mesmas mudanças são combinadas, o código final pode ser igual. **A história é diferente.**
- Se as branches divergiram, o merge cria um commit que liga as duas linhas. Se uma já contém a outra, ele pode apenas
  avançar a etiqueta da branch, sem criar commit: isso é um *fast-forward*.

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
- Se outra pessoa já baixou a branch, ela ainda tem os hashes antigos. Se a história remota for substituída,
  um `git pull` pode exigir reconciliação ou acabar duplicando mudanças.

---

## Quando isso dá problema

O problema de colaboração aparece quando **as duas coisas** acontecem juntas:

1. você deu rebase em commits que **já estavam no servidor**; e
2. alguém **já tinha baixado** esses commits.

Se você tentar substituir esses commits no servidor, um push comum pode ser recusado. Combine a atualização com o time
antes de reescrever uma branch compartilhada. Se a equipe optar por isso, `--force-with-lease` verifica se a referência
remota ainda corresponde ao estado esperado; essa verificação não elimina o trabalho de reconciliar as cópias dos colegas.

## Referências

- [Como o Git reaplica commits e como recuperar uma branch após rebase](https://git-scm.com/docs/git-rebase).
- [Merge e fast-forward](https://git-scm.com/docs/git-merge).
- [Push e a opção --force-with-lease](https://git-scm.com/docs/git-push).
