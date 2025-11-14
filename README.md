# 🧠 LEME - Inteligência Artificial

> **Sistema de Recomendação Inteligente e Inclusivo para Upskilling Profissional**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3.2-orange.svg)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Funcionalidades](#-funcionalidades)
- [Arquitetura](#-arquitetura)
- [Instalação](#-instalação)
- [Uso da API](#-uso-da-api)
- [Modelos de IA](#-modelos-de-ia)
- [Integração Frontend](#-integração-frontend)
- [Testes](#-testes)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Contribuindo](#-contribuindo)

---

## 🎯 Visão Geral

O **LEME IA** é o coração do sistema de recomendação da plataforma LEME. Utiliza **Machine Learning** para:

1. **Sugerir trilhas personalizadas** de upskilling baseadas no perfil do usuário
2. **Prever taxa de sucesso** para ajustar recomendações
3. **Garantir acessibilidade** ativando adaptações automáticas (TTS, Libras, etc.)

### 🌟 Diferenciais

- ✅ **Inclusão em primeiro lugar**: Detecta e adapta conteúdo para usuários com deficiências
- ✅ **Simples e eficaz**: Apenas 4 features (área, acessibilidade, progresso, tempo)
- ✅ **Alta acurácia**: >85% na classificação de trilhas
- ✅ **API RESTful**: 3 endpoints simples para integração

---

## 🚀 Funcionalidades

### 1. Recomendação de Trilhas
- Analisa perfil do usuário (área profissional + acessibilidade)
- Sugere trilha ideal entre **12 opções** (6 padrão + 6 acessíveis)
- Retorna **5 módulos progressivos** por trilha

### 2. Previsão de Sucesso
- Estima probabilidade de conclusão (0-100%)
- Classifica em: **Alta** | **Média** | **Baixa**
- Permite ajustes proativos (ex: módulos mais simples)

### 3. Adaptações de Acessibilidade
- **Cegos**: Text-to-Speech, Alto Contraste, Navegação por Teclado
- **Surdos/Libras**: Vídeos em Libras, Legendas
- **Sem deficiências**: Interface padrão

---

## 🏗️ Arquitetura

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Frontend  │ ──────> │   API Flask  │ ──────> │  Modelos IA │
│   (React)   │  JSON   │  (Python)    │  .pkl   │  (sklearn)  │
└─────────────┘         └──────────────┘         └─────────────┘
      │                        │
      │                        ▼
      │                 ┌──────────────┐
      └───────────────> │  Adaptações  │
        Ativa TTS/Libras│  (Frontend)  │
                        └──────────────┘
```

### Fluxo de Funcionamento

1. **Usuário faz login** → Frontend coleta perfil
2. **POST /suggest_trilha** → API retorna trilha + adaptações
3. **Frontend ativa recursos** → TTS, Libras, etc.
4. **Usuário completa módulos** → XP salvo no banco
5. **POST /predict_sucesso** → API prevê engajamento futuro

---

## 💻 Instalação

### Pré-requisitos

- Python 3.9+
- pip

### Passo a Passo

```bash
# 1. Clonar repositório
git clone https://github.com/seu-usuario/leme-ia.git
cd leme-ia

# 2. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Executar API
cd src
python api.py
```

A API estará disponível em: **http://localhost:5000**

---

## 📡 Uso da API

### 1. Health Check

Verifica se a API está online.

```bash
GET /health
```

**Resposta:**
```json
{
  "status": "ok",
  "timestamp": "2024-11-13T10:30:00",
  "modelos": true
}
```

---

### 2. Sugerir Trilha

Retorna trilha personalizada baseada no perfil.

```bash
POST /suggest_trilha
Content-Type: application/json
```

**Request Body:**
```json
{
  "area": "Advogado",
  "acessibilidade": "cego",
  "modulos_concluidos": 0,
  "tempo_plataforma_dias": 0
}
```

**Response:**
```json
{
  "trilha": "IA para Advogados (Acessível)",
  "modulos": [
    "Módulo 1: Introdução à IA Jurídica",
    "Módulo 2: Automação de Contratos",
    "Módulo 3: Análise de Jurisprudência com IA",
    "Módulo 4: Ética e Responsabilidade Digital",
    "Módulo 5: Prática com Ferramentas Jurídicas"
  ],
  "adaptacoes": [
    "text_to_speech",
    "alto_contraste",
    "navegacao_teclado"
  ],
  "confianca": 0.89
}
```

**Campos:**
- `trilha`: Nome da trilha recomendada
- `modulos`: Array com 5 módulos
- `adaptacoes`: Lista de recursos a ativar no frontend
- `confianca`: Confiança do modelo (0-1)

---

### 3. Prever Sucesso

Estima taxa de conclusão do usuário.

```bash
POST /predict_sucesso
Content-Type: application/json
```

**Request Body:**
```json
{
  "area": "Design",
  "acessibilidade": "libras",
  "modulos_concluidos": 3,
  "tempo_plataforma_dias": 20
}
```

**Response:**
```json
{
  "taxa_sucesso": 0.78,
  "categoria": "alta",
  "recomendacao": "Usuário tem boa chance de completar a trilha"
}
```

**Campos:**
- `taxa_sucesso`: Probabilidade de conclusão (0-1)
- `categoria`: `alta` | `media` | `baixa`
- `recomendacao`: Texto sugerido para o dashboard

---

## 🤖 Modelos de IA

### 1. Modelo de Classificação (Random Forest)

**Objetivo:** Classificar usuário em uma das 12 trilhas.

**Features:**
- `area_encoded`: Área profissional (0-5)
- `acess_encoded`: Tipo de acessibilidade (0-2)
- `modulos_concluidos`: Progresso (0-20)
- `tempo_plataforma_dias`: Engajamento (0-180)

**Métricas:**
- Acurácia: **87%**
- Validação cruzada: **85% ±3%**

### 2. Modelo de Regressão (Random Forest Regressor)

**Objetivo:** Prever taxa de conclusão (0-1).

**Features:** As mesmas do modelo de classificação.

**Métricas:**
- RMSE: **0.08**
- R² Score: **0.72**
- MAE: **0.06**

### 3. Análise de Equidade

Ambos os modelos foram testados para viés:
- Diferença de acurácia entre grupos: **<5%** ✅
- Erro equilibrado entre usuários com/sem deficiências

---

## 🎨 Integração Frontend

### Campos Obrigatórios no Cadastro

O frontend deve coletar:

```javascript
{
  area: "Advogado" | "Design" | "Secretariado" | "Contabilidade" | "Logistica" | "SoftSkills",
  acessibilidade: "cego" | "libras" | "nenhuma"
}
```

## 🧪 Testes

```bash
# Executar todos os testes
pytest tests/test_api.py -v

# Teste específico
pytest tests/test_api.py::test_suggest_trilha_advogado_cego -v
```
---

## 📁 Estrutura do Projeto

```
leme-ia/
├── notebooks/                    # Google Colab (Treinamento)
│   ├── criar_dataset.ipynb
│   ├── eda.ipynb
│   ├── modelo_classificacao.ipynb
│   └── modelo_regressao.ipynb
│
├── models/                       # Modelos treinados
│   ├── leme_modelo_classificacao.pkl
│   ├── leme_modelo_regressao.pkl
│   ├── leme_scaler_class.pkl
│   ├── leme_scaler_reg.pkl
│   └── leme_encoders.pkl
│
├── data/                         # Dados
│   ├── leme_dataset.csv
│   └── leme_trilhas.json
│
├── src/                          # Código da API
│   └── api.py
│
├── tests/                        # Testes
│   └── test_api.py
│
├── requirements.txt              # Dependências
└── README.md                     # Documentação
```

---

## 📊 Áreas e Trilhas Disponíveis

| Área | Trilha Padrão | Trilha Acessível |
|------|---------------|------------------|
| **Advogado** | IA para Advogados | IA para Advogados (Acessível) |
| **Design** | IA para Designers | IA para Designers (Acessível) |
| **Secretariado** | IA para Secretariado | IA para Secretariado (Acessível) |
| **Contabilidade** | IA para Contabilidade | IA para Contabilidade (Acessível) |
| **Logística** | IA para Logística | IA para Logística (Acessível) |
| **Soft Skills** | Soft Skills Essenciais | Soft Skills Essenciais (Acessível) |

Cada trilha possui **5 módulos progressivos**.

---

## 🔮 Próximos Passos

- [ ] Deploy da API (Railway/Heroku)
- [ ] Adicionar feedback loop (re-treinar com dados reais)
- [ ] Suporte a mais idiomas (inglês, espanhol)
- [ ] Modelo de NLP para chatbot de suporte

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👥 Time

- **Felipe** - Machine Learning & API
- **Gustavo** - Frontend & Backend
- **Nikolas** - Python & Suporte

---

## 📞 Contato

Para dúvidas ou sugestões, abra uma [issue](https://github.com/seu-usuario/leme-ia/issues) ou envie um email para: contato@leme.com

---

<div align="center">
  <strong>Feito com ❤️ para democratizar o acesso à educação inclusiva</strong>
</div>