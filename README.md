# 🕵️ Detetive de Passagens

App pessoal que vigia promoções de passagens e milhas e preços de voos **saindo de Vitória (VIX)**, com avisos no Telegram.

## O que ele faz

| Quando | O quê |
|---|---|
| De hora em hora | Lê os blogs Melhores Destinos, Passageiro de Primeira e Pontos pra Voar, classifica cada promoção (antecedência, região, milhas, se sai de Vitória, documento, visto e vacina) e avisa no Telegram. Também lê seus comandos do bot. |
| 1x por dia (7h) | Preço ida e volta (7 noites) dos **favoritos** e de 1/7 dos outros destinos, numa janela de 3 meses que gira entre +1, +4, +7 e +10 meses. Avisa quando cai 15% (favoritos) ou 25% (outros) abaixo do normal. Também atualiza o câmbio e o lembrete do passaporte. |
| Toda segunda | Varre os destinos mais baratos saindo de Vitória (próximos 6 meses + meses distantes) e manda o resumo do "Real forte". |

Promoções para países que pedem visto ficam escondidas (dá para mostrar no app).

## Custo

- GitHub (robô e app): grátis.
- Telegram: grátis.
- Apify: cerca de US$ 0,002 por consulta. A estimativa fica abaixo de US$ 0,50 por mês. Há uma trava em US$ 3,50/mês (variável `LIMITE_APIFY_USD`).

## Configuração (uma vez)

1. **Telegram**: fale com o @BotFather, mande `/newbot` e escolha nome e usuário. Guarde o *token* (não compartilhe com ninguém).
2. **Apify**: em console.apify.com, vá em Settings → API & Integrations e copie o *Personal API token*.
3. **GitHub**, neste repositório, em Settings → Secrets and variables → Actions → *New repository secret*:
   - `TELEGRAM_TOKEN` = token do bot
   - `APIFY_TOKEN` = token do Apify
4. **App**: em Settings → Pages, escolha *Deploy from a branch*, depois `main` e a pasta `/docs`. O endereço aparece ali (algo como `https://SEU-USUARIO.github.io/detetive-passagens/`). No iPhone: abra no Safari, toque em Compartilhar e depois em *Adicionar à Tela de Início*.
5. **Ligar**: na aba Actions, toque em *Detetive de Passagens* e depois em *Run workflow*. Em seguida mande `/start` para o seu bot. O primeiro `/start` vira o dono e só ele recebe avisos.

## Comandos do bot

`/favoritos` · `/favoritar Salvador` · `/remover SSA` · `/passaporte 2031-05-20` · `/status` · `/ajuda`

## Onde mexer

- `robo/base_dados.py`: destinos, categorias, regras de documento, visto e vacina por país (com a data em que foram conferidas).
- `docs/dados/guia_vistos.json`: aba Visto e saúde.
- `robo/voos.py`: janelas, noites e limites de queda de preço.
- Testes: `python testes/test_robo.py` e `python testes/simular.py`.
