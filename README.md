# Deal Hunter

> Monitoramento inteligente de ofertas com Python, Web Scraping, histórico de preços e notificações via Telegram.

O **Deal Hunter** é um sistema automatizado desenvolvido em Python para monitorar lojas, páginas de ofertas e, futuramente, grupos/canais do Telegram em busca de produtos que atendam a critérios definidos pelo usuário.

O sistema coleta informações sobre produtos, normaliza os dados, compara preços, mantém um histórico de valores e identifica oportunidades de compra. Quando uma oferta considerada relevante é encontrada, o usuário recebe uma notificação diretamente no Telegram.

O projeto foi pensado para funcionar de maneira **automatizada, econômica e escalável**, podendo executar uma vez por dia em vez de permanecer ativo 24 horas por dia.

---

## Objetivo

Encontrar automaticamente produtos realmente interessantes sem precisar ficar monitorando manualmente dezenas de lojas, grupos e sites.

Em vez de depender apenas do desconto informado pela loja:

```text
"20% OFF"
```

o sistema busca responder:

```text
Esse produto realmente está barato?
```

Para isso, o Deal Hunter pode utilizar:

* preço atual;
* preço anterior;
* histórico de preços;
* média de preço;
* menor preço registrado;
* marca;
* modelo;
* especificações técnicas;
* garantia;
* vendedor;
* confiabilidade da loja;
* regras personalizadas;
* pontuação da oferta.

O objetivo final é transformar milhares de produtos e promoções em poucas notificações realmente relevantes.

---

# Exemplo

Suponha que o usuário esteja procurando:

```text
SSD
1 TB
SATA III
Leitura >= 500 MB/s
Gravação >= 450 MB/s
Marca confiável
Preço <= R$ 600
```

O sistema encontra:

```text
WD Green 1 TB SATA

Preço atual: R$ 529,90
Média dos últimos 30 dias: R$ 649,90
Menor preço registrado: R$ 499,90

Leitura: 545 MB/s
Gravação: 550 MB/s
Garantia: 3 anos

Score: 91/100
```

O Telegram recebe:

```text
🚨 OFERTA ENCONTRADA

WD Green 1 TB SATA

💰 R$ 529,90
📉 18,5% abaixo da média
📊 Score: 91/100

✅ 1 TB
✅ SATA III
✅ 545 MB/s leitura
✅ 550 MB/s gravação
✅ Marca confiável

🏪 Amazon

🔗 Link da oferta
```

---

# Principais funcionalidades

## Monitoramento de lojas

O sistema pode monitorar diferentes lojas e fontes de dados.

Exemplos:

* Amazon
* KaBuM
* Pichau
* Terabyte
* Mercado Livre
* Magalu
* outras lojas de informática
* páginas específicas de promoções

Cada fonte possui um scraper próprio.

```text
scrapers/
├── amazon.py
├── kabum.py
├── pichau.py
└── terabyte.py
```

Isso permite alterar uma loja sem quebrar o restante do sistema.

---

# Coleta de produtos

Os scrapers coletam dados como:

```text
Nome
Marca
Modelo
Preço
Preço anterior
Desconto
URL
Loja
Vendedor
Disponibilidade
Especificações
```

Os dados coletados são posteriormente normalizados.

Exemplo:

```python
{
    "name": "SSD WD Green 1TB",
    "brand": "Western Digital",
    "model": "WDS100T3G0A",
    "price": 529.90,
    "store": "Amazon",
    "seller": "Amazon",
    "capacity_gb": 1000,
    "interface": "SATA",
    "read_mb": 545,
    "write_mb": 550
}
```

---

# Sistema de regras

O usuário pode definir exatamente o que procura.

Exemplo:

```json
{
    "category": "ssd",
    "capacity_gb": 1000,
    "interface": "sata",
    "max_price": 600,
    "min_read_mb": 500,
    "min_write_mb": 450
}
```

Também podem existir regras relacionadas à marca:

```json
{
    "allowed_brands": [
        "Western Digital",
        "WD",
        "SanDisk",
        "Samsung",
        "Kingston",
        "Crucial"
    ]
}
```

Ou regras de qualidade:

```json
{
    "minimum_warranty_years": 3,
    "marketplace_allowed": false
}
```

---

# Histórico de preços

Uma das principais funcionalidades do projeto é evitar depender apenas do preço informado pela loja.

O sistema armazena o histórico.

Exemplo:

```text
Data         Preço
01/09        R$ 699,90
02/09        R$ 679,90
03/09        R$ 649,90
04/09        R$ 649,90
05/09        R$ 619,90
06/09        R$ 599,90
07/09        R$ 579,90
08/09        R$ 549,90
09/09        R$ 529,90
```

A partir desses dados, o sistema pode calcular:

* menor preço;
* maior preço;
* preço médio;
* mediana;
* variação percentual;
* tendência;
* preço dos últimos 7 dias;
* preço dos últimos 30 dias;
* preço dos últimos 90 dias.

Isso permite detectar promoções reais.

---

# Detecção de promoção real

Uma loja pode dizer:

```text
DE R$ 999
POR R$ 699
```

Mas o histórico pode mostrar:

```text
Preço médio: R$ 679
```

Nesse caso, a promoção anunciada não é tão interessante.

O Deal Hunter pode identificar isso automaticamente.

Exemplo:

```text
Preço anunciado: R$ 699
Média histórica: R$ 679
```

Resultado:

```text
⚠️ Não é uma promoção relevante.
```

Por outro lado:

```text
Preço atual: R$ 499
Média histórica: R$ 679
```

Resultado:

```text
🔥 Oferta relevante.
```

---

# Sistema de pontuação

As ofertas podem receber uma pontuação automática.

Exemplo:

```text
Preço abaixo do limite       +30
Preço muito abaixo da média  +20
Marca confiável              +15
Garantia >= 3 anos           +10
TLC                          +5
Loja confiável               +10
Produto em queda de preço    +10
```

Resultado:

```text
Score = 100
```

Outro produto:

```text
Preço baixo                   +25
Marca desconhecida            +5
Garantia curta                +2
Sem histórico                 +0
Vendedor desconhecido         +0

Score = 32
```

Assim, o sistema não precisa enviar toda oferta encontrada.

---

# Níveis de alerta

As notificações podem possuir diferentes níveis.

## Informativo

```text
Score: 50–69
```

Oferta razoável, mas não excepcional.

## Bom negócio

```text
Score: 70–84
```

Oferta que merece atenção.

## Excelente negócio

```text
Score: 85–94
```

Grande oportunidade.

## Oferta excepcional

```text
Score: 95–100
```

Preço extremamente abaixo do histórico ou uma combinação excepcional de preço e qualidade.

---

# Notificações

O canal inicial será o Telegram.

O sistema pode utilizar um Bot do Telegram para enviar:

```text
🚨 NOVA OFERTA
```

ou:

```text
🔥 OFERTA EXCEPCIONAL
```

ou:

```text
📉 MENOR PREÇO HISTÓRICO
```

Cada mensagem pode conter:

```text
Produto
Preço
Preço anterior
Média histórica
Menor preço histórico
Desconto
Loja
Vendedor
Especificações
Score
Link
```

---

# Execução

O projeto não precisa necessariamente ficar rodando 24/7.

A primeira estratégia será:

```text
22:00
  ↓
Executar script
  ↓
Coletar ofertas
  ↓
Normalizar dados
  ↓
Atualizar banco
  ↓
Comparar preços
  ↓
Aplicar regras
  ↓
Calcular score
  ↓
Enviar notificações
  ↓
Finalizar
```

Isso reduz bastante a infraestrutura necessária.

---

# Agendamento

O sistema pode ser executado utilizando:

* GitHub Actions;
* cron;
* Windows Task Scheduler;
* Linux systemd timer;
* VPS;
* Raspberry Pi;
* Docker.

Para a primeira versão, a preferência é:

```text
GitHub Actions
```

porque permite executar o projeto periodicamente sem manter um computador pessoal ligado.

---

# Arquitetura

A arquitetura planejada é:

```text
                 ┌─────────────────┐
                 │ Scheduler       │
                 │ GitHub Actions  │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Application     │
                 │ Python          │
                 └────────┬────────┘
                          │
          ┌───────────────┼────────────────┐
          │               │                │
          ▼               ▼                ▼
     Amazon          KaBuM             Pichau
     Scraper         Scraper           Scraper
          │               │                │
          └───────────────┼────────────────┘
                          ▼
                 ┌─────────────────┐
                 │ Normalizer      │
                 └────────┬────────┘
                          ▼
                 ┌─────────────────┐
                 │ Product Rules   │
                 └────────┬────────┘
                          ▼
                 ┌─────────────────┐
                 │ Price Analyzer  │
                 └────────┬────────┘
                          ▼
                 ┌─────────────────┐
                 │ SQLite          │
                 └────────┬────────┘
                          ▼
                 ┌─────────────────┐
                 │ Deal Scorer     │
                 └────────┬────────┘
                          ▼
                 ┌─────────────────┐
                 │ Telegram        │
                 └─────────────────┘
```

---

# Estrutura do projeto

Estrutura inicial planejada:

```text
deal-hunter/
│
├── app/
│   │
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── amazon.py
│   │   ├── kabum.py
│   │   ├── pichau.py
│   │   ├── terabyte.py
│   │   └── mercadolivre.py
│   │
│   ├── parsers/
│   │   ├── __init__.py
│   │   └── product_parser.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── product.py
│   │   └── price.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── analyzer.py
│   │   ├── scorer.py
│   │   ├── notifier.py
│   │   └── history.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── repositories.py
│   │   └── migrations.py
│   │
│   └── config/
│       ├── rules.py
│       └── settings.py
│
├── tests/
│   ├── test_scrapers.py
│   ├── test_parser.py
│   ├── test_scorer.py
│   └── test_history.py
│
├── data/
│   └── .gitkeep
│
├── .github/
│   └── workflows/
│       └── daily.yml
│
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

# Banco de dados

A primeira versão utiliza SQLite.

Estrutura conceitual:

```text
products
---------
id
name
brand
model
category
url

prices
------
id
product_id
store
seller
price
timestamp

specifications
--------------
product_id
capacity_gb
interface
read_mb
write_mb
nand
tbw
warranty_years
```

Também podem existir tabelas adicionais:

```text
stores
alerts
rules
notifications
price_events
```

---

# Controle de produtos já processados

O sistema não deve enviar a mesma oferta repetidamente.

Exemplo:

```text
10:00
WD Green
R$ 529
```

Notificação enviada.

Às 22:00:

```text
WD Green
R$ 529
```

Nenhuma nova notificação.

Porém:

```text
WD Green
R$ 499
```

pode gerar:

```text
🔥 NOVO MENOR PREÇO
```

Isso evita spam.

---

# Controle de alertas

O sistema pode registrar:

```text
produto
preço
momento do alerta
tipo do alerta
score
```

Tipos possíveis:

```text
NEW_PRODUCT
PRICE_DROP
HISTORICAL_LOW
GREAT_DEAL
BACK_IN_STOCK
```

---

# Futuro: monitoramento do Telegram

Uma segunda etapa do projeto pode permitir analisar grupos e canais do Telegram aos quais o usuário possui acesso.

Arquitetura:

```text
Conta Telegram
      ↓
Telethon
      ↓
Mensagens
      ↓
Extração de links
      ↓
Identificação do produto
      ↓
Consulta da oferta
      ↓
Análise
      ↓
Score
      ↓
Notificação
```

A ideia é encontrar mensagens como:

```text
SSD WD 1TB por R$499

https://...
```

e transformá-las em dados estruturados.

---

# Extração inteligente de mensagens

Exemplo:

```text
🔥 SSD WD Green 1TB SATA
de R$699 por R$499
cupom: SSD50
https://...
```

O sistema poderia extrair:

```json
{
    "brand": "WD",
    "model": "Green",
    "capacity_gb": 1000,
    "technology": "SATA",
    "price": 499,
    "coupon": "SSD50",
    "url": "https://..."
}
```

---

# Futuro: múltiplas fontes

O sistema pode combinar:

```text
Lojas
+
Grupos Telegram
+
Canais Telegram
+
Sites de promoções
+
APIs
+
Feeds
```

Cada fonte alimenta o mesmo pipeline.

```text
                    ┌── Amazon
                    ├── KaBuM
                    ├── Pichau
                    ├── Terabyte
                    ├── Mercado Livre
                    ├── Telegram
                    └── Promoções
                         │
                         ▼
                    Normalização
                         │
                         ▼
                       Banco
                         │
                         ▼
                       Análise
```

---

# Futuro: comparação entre lojas

Quando o mesmo produto aparecer em várias lojas:

```text
WD Green 1TB

Amazon       R$ 529
KaBuM        R$ 559
Pichau       R$ 579
Mercado Livre R$ 499
```

O sistema pode automaticamente selecionar:

```text
Melhor preço: R$499
```

mas também considerar:

```text
Preço
Frete
Garantia
Vendedor
Reputação
Tempo de entrega
```

Portanto, o menor preço não necessariamente será o melhor negócio.

---

# Futuro: custo real

O sistema pode calcular:

```text
Preço do produto
+
Frete
-
Cupom
=
Custo final
```

Exemplo:

```text
Produto: R$ 499
Frete:   R$ 30
Cupom:   -R$ 20

Total:   R$ 509
```

Isso evita considerar uma oferta barata que fica cara por causa do frete.

---

# Futuro: personalização

O usuário pode possuir diversos perfis de busca.

Exemplo:

```text
Perfil: PC

SSD:
máx. R$600

RAM:
DDR4
32 GB
máx. R$500

GPU:
RTX 4060
máx. R$1800
```

Outro perfil:

```text
Perfil: Casa

Monitor:
24"
IPS
75 Hz+
máx. R$700
```

---

# Futuro: comandos do Telegram

O usuário poderá interagir com o bot.

Exemplos:

```text
/start
```

```text
/config
```

```text
/precos ssd
```

```text
/ofertas
```

```text
/historico WD Green 1TB
```

```text
/adicionar "RTX 4060" 1800
```

```text
/remover "RTX 4060"
```

Assim, o Telegram deixa de ser apenas um canal de notificação e passa a ser a interface do sistema.

---

# Futuro: dashboard

Uma interface web pode ser criada posteriormente.

Possíveis tecnologias:

```text
Streamlit
```

ou:

```text
FastAPI
+
React
```

O dashboard poderia mostrar:

```text
Produtos monitorados
Ofertas encontradas
Menores preços
Quedas recentes
Histórico
Lojas
Categorias
Alertas enviados
```

Exemplo:

```text
──────────────────────────────────────
 DEAL HUNTER
──────────────────────────────────────

Produtos monitorados: 147

Ofertas hoje: 12

Melhor oferta:
SSD WD Green 1TB
R$529
-18% da média

Menor preço histórico:
R$499

──────────────────────────────────────
```

---

# Futuro: gráficos

O preço de um produto poderia ser visualizado:

```text
R$
700 | ●
650 |   ●
600 |      ●
550 |          ●
500 |              ●
450 |
    └────────────────────
      Tempo
```

Isso ajudaria o usuário a decidir se compra agora ou espera.

---

# Futuro: previsão de preço

Com histórico suficiente, o sistema poderá tentar identificar comportamento de preços.

Exemplo:

```text
Produto:
SSD WD Green 1TB

Preço atual:
R$579

Histórico:
R$699
R$649
R$619
R$579
```

O sistema poderia classificar:

```text
Tendência: queda
```

ou:

```text
Tendência: estabilidade
```

ou:

```text
Tendência: alta
```

Uma etapa mais avançada poderia utilizar modelos de Machine Learning.

---

# Futuro: inteligência artificial

IA não será necessária para a primeira versão.

Entretanto, pode ser utilizada posteriormente para tarefas como:

## Classificação

Identificar automaticamente a categoria:

```text
"SSD Kingston 1TB SATA"
```

→

```text
Categoria: SSD
```

## Extração de especificações

Transformar descrição em dados estruturados.

## Normalização

Reconhecer que:

```text
WD Green 1TB
Western Digital Green 1000GB
WDS100T3G0A
```

podem representar o mesmo produto.

## Resumo

Gerar uma explicação:

```text
Boa oportunidade porque o preço atual está
17% abaixo da média dos últimos 30 dias e
é o segundo menor preço registrado.
```

## Análise de oferta

Um modelo de linguagem poderia atuar como uma camada final de análise, mas somente depois que os dados fundamentais estiverem estruturados.

---

# Segurança

Credenciais nunca devem ser armazenadas diretamente no código.

Exemplo incorreto:

```python
TOKEN = "123456789:ABC..."
```

A abordagem correta utiliza variáveis de ambiente:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

No GitHub Actions, esses valores devem ser armazenados como:

```text
GitHub Secrets
```

O arquivo:

```text
.env
```

nunca deve ser enviado para o Git.

---

# Limitações e cuidados

Scraping deve ser implementado de maneira responsável.

Sites diferentes podem possuir:

* proteção anti-bot;
* JavaScript;
* Cloudflare;
* mudanças frequentes no HTML;
* limites de requisições;
* APIs próprias;
* restrições em termos de uso.

Por isso, cada scraper deverá ser desenvolvido de maneira independente e com controle de frequência.

Sempre que existir uma API oficial ou mecanismo apropriado, ela deve ser considerada antes de scraping direto.

O projeto também deve respeitar os termos e políticas aplicáveis de cada serviço.

---

# Tecnologias

Stack inicial:

```text
Python 3.12+
requests
BeautifulSoup
SQLite
pytest
python-dotenv
python-telegram-bot
GitHub Actions
```

Possíveis tecnologias futuras:

```text
Playwright
Telethon
Pydantic
SQLAlchemy
FastAPI
Streamlit
Docker
PostgreSQL
Polars
Pandas
Machine Learning
LLMs
```

---

# Conceitos praticados

Este projeto foi pensado também como projeto de aprendizagem.

Durante seu desenvolvimento serão praticados conceitos como:

### Python

* funções;
* classes;
* módulos;
* pacotes;
* exceptions;
* type hints;
* dataclasses;
* arquivos;
* JSON;
* variáveis de ambiente;
* logging.

### Web

* HTTP;
* requests;
* headers;
* status codes;
* HTML;
* CSS selectors;
* parsing;
* APIs REST;
* paginação.

### Banco de dados

* SQLite;
* SQL;
* relacionamentos;
* índices;
* consultas;
* histórico;
* migrations.

### Engenharia de software

* arquitetura;
* separação de responsabilidades;
* interfaces;
* testes;
* tratamento de erros;
* logging;
* configuração;
* Git;
* CI/CD.

### Data Engineering

* coleta;
* transformação;
* normalização;
* armazenamento;
* qualidade de dados;
* histórico;
* processamento incremental.

### DevOps

* GitHub Actions;
* secrets;
* automação;
* jobs agendados;
* Docker futuramente.

---

# Roadmap

## Fase 1 — MVP

* [ ] Criar scraper de uma loja
* [ ] Extrair nome
* [ ] Extrair preço
* [ ] Extrair URL
* [ ] Criar banco SQLite
* [ ] Salvar produtos
* [ ] Salvar preços
* [ ] Criar filtro por preço
* [ ] Criar bot Telegram
* [ ] Enviar primeira notificação

## Fase 2 — Sistema de monitoramento

* [ ] Detectar produto novo
* [ ] Detectar mudança de preço
* [ ] Evitar notificações duplicadas
* [ ] Histórico de preços
* [ ] Comparação com média
* [ ] Detectar menor preço
* [ ] Logs
* [ ] Testes automatizados

## Fase 3 — Múltiplas lojas

* [ ] Amazon
* [ ] KaBuM
* [ ] Pichau
* [ ] Terabyte
* [ ] Mercado Livre
* [ ] Normalização entre lojas
* [ ] Comparação automática

## Fase 4 — Sistema de pontuação

* [ ] Score
* [ ] Regras personalizadas
* [ ] Peso por característica
* [ ] Classificação de ofertas
* [ ] Diferentes níveis de alerta

## Fase 5 — Automação

* [ ] GitHub Actions
* [ ] Execução diária
* [ ] Secrets
* [ ] Monitoramento de falhas
* [ ] Retry automático

## Fase 6 — Telegram avançado

* [ ] Ler grupos/canais autorizados
* [ ] Telethon
* [ ] Extração de links
* [ ] Identificação de produtos
* [ ] Comandos do bot
* [ ] Configuração pelo Telegram

## Fase 7 — Dashboard

* [ ] Streamlit
* [ ] Histórico
* [ ] Gráficos
* [ ] Produtos monitorados
* [ ] Ofertas
* [ ] Estatísticas

## Fase 8 — Inteligência

* [ ] Normalização inteligente
* [ ] IA para classificação
* [ ] análise automática
* [ ] previsão de tendência
* [ ] recomendações personalizadas

---

# Exemplo de fluxo completo

```text
┌──────────────────────┐
│ GitHub Actions       │
│ 22:00                │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Scrapers             │
│ Amazon / KaBuM / etc │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Normalização         │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ SQLite               │
│ Histórico            │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Regras do usuário    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Price Analyzer       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Deal Scorer          │
└──────────┬───────────┘
           │
           ▼
       Score >= 70?
         /      \
       Não      Sim
       │         │
       ▼         ▼
   Ignorar    Telegram
                 │
                 ▼
              Usuário
```

---

# Objetivo final

O objetivo final do Deal Hunter é funcionar como um **radar pessoal de preços**.

Em vez de:

```text
entrar em 10 lojas
abrir 20 páginas
comparar preços
olhar histórico
entrar em grupos
procurar promoções
```

o usuário define:

```text
O que quero
Quanto quero pagar
Quais marcas aceito
Quais características são importantes
```

e o sistema faz o monitoramento.

O resultado esperado é:

```text
Muitos produtos
      ↓
Muitos preços
      ↓
Filtros
      ↓
Histórico
      ↓
Análise
      ↓
Score
      ↓
Poucas ofertas realmente relevantes
      ↓
Telegram
```

---

# Possíveis expansões

O projeto pode evoluir para:

```text
Price Tracker
        +
Deal Finder
        +
Recommendation Engine
        +
Telegram Bot
        +
Dashboard
        +
Price Analytics
```

Também pode ser transformado em uma plataforma multiusuário, na qual cada usuário possua:

```text
suas preferências
seus produtos
seus limites
seus alertas
seu histórico
```

---

# Licença

Definir posteriormente.

---

# Status

🚧 Em desenvolvimento

A primeira versão do projeto terá como foco:

```text
Python
+
Web Scraping
+
SQLite
+
Histórico de preços
+
Telegram
+
GitHub Actions
```

O objetivo inicial não é construir um sistema extremamente complexo, mas criar uma base sólida e extensível que possa evoluir progressivamente.

---

# Autor

Desenvolvido como projeto de estudo e prática de:

```text
Python
Web Scraping
Automação
APIs
Banco de Dados
Data Engineering
DevOps
```

---

# Arquitetura atual do pipeline

O Deal Hunter utiliza uma arquitetura **transparente e multi-fonte** baseada no protocolo `Source[Offer]`:

```text
       APIs / Feeds / Agregadores / Scrapers
                         ↓
                   Source[Offer]
                         ↓
                    Offer Comum
                         ↓
                   Normalização
                         ↓
               Classificação por Regras
                         ↓
                      SQLite
                         ↓
               Histórico de Preços
                         ↓
             Análise de Preço & Deal Score
                         ↓
                 Filtro Anti-Spam
                         ↓
                 Notificação Telegram
```

### Fontes Implementadas:
* `PelandoSource` (`app/sources/pelando.py`): Agregador de ofertas via consulta HTTP com timeout e fallback silencioso.
* `PromobitSource` (`app/sources/promobit.py`): Agregador de ofertas via consulta HTTP resiliente.
* `KabumSource` (`app/sources/kabum.py`): Scraper Playwright + BeautifulSoup integrado ao protocolo `Source`.
* `PichauSource` (`app/sources/pichau.py`): Adaptador resiliente. Em caso de bloqueio anti-bot ou WAF, registra aviso e permite o pipeline continuar.
* `TerabyteSource` (`app/sources/terabyte.py`): Adaptador resiliente com tratamento de erros gracioso.

### Princípio da Resiliência:
O pipeline de dados (`app/sources/collection.py`) captura exceções de cada fonte individualmente. Se uma loja ou agregador falhar ou aplicar bloqueios, o sistema registra um aviso no log (`[WARNING] Fonte X indisponível`) e **continua a execução normalmente com as demais fontes saudáveis**.

## Componentes implementados

* `app/models/offer.py`: Modelo comum de oferta independente da origem;
* `app/sources/base.py`: Protocolo `Source[OfferT]`;
* `app/sources/collection.py`: Coleta desacoplada com isolamento de falhas por fonte;
* `app/services/normalizer.py`: Normalização de texto, loja, URL e preços;
* `app/services/classifier.py`: Classificação determinística por palavras-chave com prioridade;
* `app/services/price_analyzer.py`: Média histórica, menor preço e distância da média;
* `app/services/deal_scorer.py`: Score explicável de 0 a 100;
* `app/services/notification_rules.py`: Regra anti-spam;
* `app/database/migrations.py`: Schema histórico não destrutivo;
* `app/database/repositories.py`: Persistência no SQLite.

## Execução local

Instale as dependências com:

```powershell
uv sync
uv run playwright install chromium
```

Configure `.env` a partir de `.env.example` e execute:

```powershell
uv run python main.py
```

Os testes unitários rodam com:

```powershell
uv run pytest -q
```

Todos os testes de fontes utilizam mocks e não fazem requisições reais.

