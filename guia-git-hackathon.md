# Guia Git — Claude Impact Lab (24/05)

---

## ANTES DE COMEÇAR A TRABALHAR (sempre)

```bash
cd ~/Documents/ClaudeImpactLab
git pull
```

---

## DEPOIS DE FAZER MUDANÇAS (salvar + enviar)

```bash
git add .
git commit -m "descreve o que você fez aqui"
git push
```

---

## SE O PUSH DER ERRO (alguém pushou antes de você)

```bash
git pull --rebase
git push
```

---

## EXEMPLOS DE MENSAGENS DE COMMIT

```bash
git commit -m "adicionei análise de custo por inferência"
git commit -m "atualizei README com descrição do problema"
git commit -m "adicionei dados do IBGE na pasta research"
```

---

## CONFERIR O QUE MUDOU

```bash
git status
```

---

## RESUMO MENTAL

```
pull → trabalha → add → commit → push
(baixa)          (prepara) (salva) (envia)
```

**Regra de ouro:** sempre `git pull` antes de começar e antes de dar push.

---

## SE TRAVAR

Fala pro Claude Code:
> "faz commit de tudo com a mensagem 'X' e dá push"

Ele resolve.
