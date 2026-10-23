# 🏢 GMC Enterprise Management Platform

> **Sistema Integrado de Apoio à Decisão Estratégica para o Global Management Challenge (GMC)**
> Empresa 1 | Grupo 0

Esta plataforma substitui a análise manual de folhas de Excel por um sistema interativo e completo de inteligência empresarial, com motor de simulação determinística (*what-if*), validação física de restrições em tempo real e benchmarking competitivo das 8 empresas do grupo.

---

## 🚀 Como Executar Localmente

### 1. Clonar o repositório
```bash
git clone <URL_DO_REPOSITORIO>
cd <PASTA_DO_REPOSITORIO>
```

### 2. Criar ambiente virtual e instalar dependências
```bash
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Iniciar a aplicação
```bash
streamlit run app.py
```
Aceda no seu browser em: **`http://localhost:8501`**

---

## 🌐 Deploy em 1 Clique (Streamlit Community Cloud)

1. Faça push deste repositório para o seu GitHub.
2. Aceda a [share.streamlit.io](https://share.streamlit.io/) e faça login com o GitHub.
3. Clique em **"New app"**.
4. Selecione este repositório, branch `main`, e defina o ficheiro principal como `app.py`.
5. Clique em **"Deploy"**! A sua plataforma ficará online com link público seguro para partilhar com os colegas de equipa.

---

## 📦 Estrutura do Projeto

* `app.py`: Interface de utilizador interativa construída em Streamlit com design executivo dark slate e gráficos Plotly.
* `engine.py`: Motor determinístico de projeção financeira (DRE, Balanço, Fluxo de Caixa, Cotação) e validação de restrições operacionais.
* `data.py`: Parser de alta fidelidade para relatórios trimestrais do GMC (`History/*.Xls`).
* `params.py`: Especificações e constantes oficiais das 28 tabelas do Manual do Participante.
* `History/`: Relatórios trimestrais históricos oficiais (`PT_HstY14Q1.Xls` a `PT_HstY15Q1.Xls`).

---

## 🎯 Funcionalidades Principais

1. **Cockpit Executivo & Scorecard**: Diagnóstico de alto nível, decomposição DuPont do ROE e histórico dos 5 trimestres.
2. **Simulador de Decisões Y15Q2**: Teste de cenários (*Otimizado*, *Agressivo*, *Conservador*) com validação em tempo real de matéria-prima, horas de máquina, montagem e tesouraria.
3. **Marketing & Preços**: Análise de rentabilidade e margens de contribuição nos mercados UE, Nafta e Internet.
4. **Produção & Supply Chain**: Dimensionamento de turnos, manutenção de máquinas e escada de custos de matéria-prima (*cost laddering*).
5. **Recursos Humanos**: Gestão dos 21 operários qualificados, tempos de montagem e controlo de horas ociosas/extraordinárias.
6. **Finanças & Tesouraria**: Arbitragem de tesouraria (eliminação de descoberto bancário via depósito a prazo) e projeção de liquidez.
7. **Inteligência Competitiva**: Comparativo detalhado das 8 equipas do grupo.
8. **Manual Oficial Interativo**: Consulta instantânea das tabelas de parâmetros e regras do simulador.

---

## 👥 Autores
Equipa Empresa 1 — Global Management Challenge 2026/2027
