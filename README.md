# 🏢 PrediMan Shopping — Plataforma de Manutenção Preditiva Inteligente

![Python](https://img.shields.io/badge/Python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.140-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.60-ff69b4)
![Docker](https://img.shields.io/badge/Docker-✓-2496ED)
![JWT](https://img.shields.io/badge/JWT-autenticação-orange)
![PWA](https://img.shields.io/badge/PWA-instalável-purple)
![Tests](https://img.shields.io/badge/testes-80_passando-success)

> **Sistema completo de manutenção preditiva para shopping centers — da detecção de anomalias à execução da ordem de serviço no celular do técnico.**

---

## 🎯 O Problema

Shoppings centers operam com dezenas de equipamentos críticos (chillers, subestações, bombas, iluminação) que, quando falham, causam:

- ❌ **Paradas não programadas** → lojas fecham, cliente reclama
- ❌ **Multas regulatórias** → fator de potência baixo (ANEEL)
- ❌ **Manutenção corretiva** → 70% do tempo da equipe
- ❌ **Falta de histórico** → sem dados para decisões

## ✅ A Solução

**PrediMan Shopping** é uma plataforma que:

1. 📡 **Monitora equipamentos 24/7** com sensores (ou simulador para MVP)
2. 🧠 **Detecta anomalias automaticamente** com regras de engenharia + machine learning
3. 📋 **Gera ordens de serviço** automaticamente com diagnóstico
4. 📖 **Entrega o procedimento (POP)** completo no celular do técnico
5. 📊 **Dashboard em tempo real** para o gestor de facilities

---

## 🏗️ Arquitetura
```
[ Sensores IoT / Simulador ]
│
▼
[ FastAPI — Motor Analítico ]
│
┌────┴────┐
▼ ▼
[ PostgreSQL ] [ Dashboard Streamlit ]
│
▼
[ PWA Mobile ]

```


### Microsserviços (Docker Compose)

| Serviço | Responsabilidade | Porta |
|---------|-----------------|-------|
| **api** | Ingestão de dados, motor analítico, geração de OS, autenticação JWT | `8000` |
| **dashboard** | Painel do gestor com KPIs, gráficos e mapa do shopping | `8501` |
| **simulator** | Gera dados realistas de 6 equipamentos com anomalias configuráveis | — |
| **db** | PostgreSQL — armazena equipamentos, leituras, OS, POPs, usuários | `5432` |

---

## 🛠️ Equipamentos Monitorados

| Equipamento | Sensores | Anomalias Detectadas |
|-------------|----------|---------------------|
| **Chiller** | Vibração, ΔT, corrente | Desgaste de rolamento, baixa eficiência, sobrecarga |
| **Subestação** | Tensão, corrente, FP, temperatura | FP baixo (multa ANEEL), sobrecarga, oscilação |
| **Bomba recalque** | Vibração, corrente, nível | Cavitação, obstrução, poço seco |
| **Iluminação** | Corrente, estado | Timer falho, lâmpadas queimadas, degradação |

---

## 📊 Funcionalidades

### Para o Gestor (Dashboard)
- ✅ Cards KPI (equipamentos, OS ativas, alertas críticos, economia)
- ✅ Mapa do shopping com status em tempo real
- ✅ Gráfico de tendência de anomalias
- ✅ Tabela de últimas ordens de serviço
- ✅ Auto-refresh suave

### Para o Técnico (PWA Mobile)
- ✅ App instalável (iOS/Android) — funciona offline
- ✅ Lista de OS pendentes por prioridade
- ✅ POP completo: EPIs, ferramentas, passo a passo, riscos
- ✅ Atualização de status (Iniciar → Pausar → Concluir)

### Segurança
- ✅ Autenticação JWT com tokens de expiração
- ✅ Senhas com hash bcrypt (nunca texto puro)
- ✅ Rotas protegidas por papel (técnico, gestor, admin)
- ✅ Variáveis de ambiente para secrets

---

## 🚀 Como Rodar

### Pré-requisitos
- [Docker](https://www.docker.com/) e Docker Compose instalados

### 1. Clone o repositório


git clone https://github.com/TONIRESILIENTE/prediman-shopping.git
cd prediman-shopping

### 2. Configure o ambiente

cp .env.example .env
Edite .env e defina uma SECRET_KEY forte:
python -c "import secrets; print(secrets.token_urlsafe(32))"

### 3. Suba o sistema

docker-compose up --build -d

### 4. Acesse
```
Interface	URL
📡 API (Swagger)    http://localhost:8000/docs
📊 Dashboard	    http://localhost:8501
📱 PWA Mobile	    http://localhost:8000/pwa/index.html

```
## 🧪 Testes

#### Todos os testes (dentro do container)
docker exec -it prediman_api python -m pytest -v

#### Cobertura
docker exec -it prediman_api python -m pytest --cov=src --cov-report=term-missing

Resultado: 80 testes passando ✅

### 🛠️ Stack Tecnológica
```
Categoria	    Tecnologia
Backend	        FastAPI, Pydantic, SQLAlchemy
Frontend	    Streamlit, Plotly
Mobile	        PWA (HTML/CSS/JS vanilla)
Banco	        PostgreSQL
Autenticação	JWT, bcrypt
Infra	        Docker, Docker Compose
Testes	        Pytest
CI/CD	        GitHub Actions

```

## 📁 Estrutura do Projeto

```
prediman-shopping/
├── src/
│   ├── api/            # FastAPI — rotas, schemas, middleware
│   ├── analytics/      # Motor analítico — regras + ML
│   ├── simulator/      # Simulador de sensores industriais
│   ├── dashboard/      # Streamlit — painel do gestor
│   ├── pwa/            # PWA Mobile — app do técnico
│   ├── services/       # Lógica de negócio (OS, POPs, auth)
│   └── database/       # Modelos SQLAlchemy + migrações
├── tests/              # 80 testes automatizados
├── docker-compose.yml  # Orquestração dos 4 serviços
├── .env.example        # Template de variáveis de ambiente
└── README.md

```
## 🔮 Roadmap
Versão	                 Funcionalidade
v1.0 ✅	        MVP: monitoramento, diagnóstico, OS, POPs, dashboard, PWA
v1.1 🔲	         POPs com animações Lottie (vídeos curtos dos procedimentos)
v1.2 🔲	         Dashboard em HTML/CSS puro (visual mais profissional)
v2.0 🔲	         Integração com sensores reais (ESP32 + MQTT)

## 👤 Autor
#### Toni Almeida Muniz — Profissional de manutenção industrial em transição para tecnologia.

º 🔗 GitHub

º 💼 LinkedIn