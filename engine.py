"""Motor de Simulação, Otimização e Verificação de Regras do GMC.

Contém:
1. Modelagem determinística / what-if das operações, vendas, DRE, Balanço e Fluxo de Caixa.
2. Motor de regras e validação de restrições (matéria-prima, horas de máquina, operários, espaço, tesouraria).
3. Cenários pré-configurados para o Y15Q2 (Recomendado, Agressivo, Conservador).
4. Explicações detalhadas dos porquês económicos e estratégicos de cada escolha.
"""
from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from typing import Any

try:
    from .data import Quarter
    from .params import (
        ASSEMBLY_MIN_MIN,
        CONTAINER_CAP,
        CO2_PER_ASSEMBLY_HOUR,
        CO2_PER_M2,
        CO2_PER_MACHINE_HOUR,
        DEPRECIATION_RATE_Q,
        DIST_INTERNET_ROUNDTRIP,
        DIST_NAFTA_PORT_ROUNDTRIP,
        EMERGENCY_MP_SURCHARGE,
        EXT_STORAGE_MP,
        EXTRA_QUALITY_MP_SURCHARGE,
        FACTORY_FIXED_PER_M2,
        FACTORY_MAX_USE,
        HOURS_BASE,
        HOURS_SAT,
        HOURS_SUN,
        HR_COSTS,
        INFO_COST,
        INSURANCE,
        INTERNET_USAGE_FEE,
        ISP_PORT_COST,
        LAND_MAX_USE,
        MACHINE_HOURS_BY_SHIFTS,
        MACHINE_MIN,
        MACHINE_PRICE,
        MACHINE_RUN_COST_HOUR,
        MAINT_COST_CONTRACT,
        MAINT_COST_EMERGENCY,
        MARKETS,
        MP_PER_UNIT,
        OVERDRAFT_AUTH_SPREAD,
        OVERDRAFT_UNAUTH_SPREAD,
        OVERHEAD_PER_MACHINE,
        PRODUCT_NAMES,
        PRODUCTS,
        PURCHASING_OVERHEAD,
        REJECT_VALUE,
        SHIFT_PREMIUM,
        SKILLED_MIN_WAGE,
        SPACE_PER_1000_MP,
        SPACE_PER_MACHINE,
        SPACE_PER_SKILLED,
        SPACE_WIP,
        STORAGE_PRODUCT_EU_NET,
        STORAGE_PRODUCT_NAFTA_USD,
        SUPERVISION_PER_SHIFT,
        TAX_RATE,
        TERM_LOAN_RATE,
        TRUCK_DAY_COST,
        UNSKILLED_MIN_PAID_HOURS,
        UNSKILLED_PER_MACHINE_SHIFT,
        UNSKILLED_WAGE_RATIO,
        WARRANTY_COST,
        WEB_CAPACITY,
    )
except ImportError:
    from data import Quarter
    from params import (
        ASSEMBLY_MIN_MIN,
        CONTAINER_CAP,
        CO2_PER_ASSEMBLY_HOUR,
        CO2_PER_M2,
        CO2_PER_MACHINE_HOUR,
        DEPRECIATION_RATE_Q,
        DIST_INTERNET_ROUNDTRIP,
        DIST_NAFTA_PORT_ROUNDTRIP,
        EMERGENCY_MP_SURCHARGE,
        EXT_STORAGE_MP,
        EXTRA_QUALITY_MP_SURCHARGE,
        FACTORY_FIXED_PER_M2,
        FACTORY_MAX_USE,
        HOURS_BASE,
        HOURS_SAT,
        HOURS_SUN,
        HR_COSTS,
        INFO_COST,
        INSURANCE,
        INTERNET_USAGE_FEE,
        ISP_PORT_COST,
        LAND_MAX_USE,
        MACHINE_HOURS_BY_SHIFTS,
        MACHINE_MIN,
        MACHINE_PRICE,
        MACHINE_RUN_COST_HOUR,
        MAINT_COST_CONTRACT,
        MAINT_COST_EMERGENCY,
        MARKETS,
        MP_PER_UNIT,
        OVERDRAFT_AUTH_SPREAD,
        OVERDRAFT_UNAUTH_SPREAD,
        OVERHEAD_PER_MACHINE,
        PRODUCT_NAMES,
        PRODUCTS,
        PURCHASING_OVERHEAD,
        REJECT_VALUE,
        SHIFT_PREMIUM,
        SKILLED_MIN_WAGE,
        SPACE_PER_1000_MP,
        SPACE_PER_MACHINE,
        SPACE_PER_SKILLED,
        SPACE_WIP,
        STORAGE_PRODUCT_EU_NET,
        STORAGE_PRODUCT_NAFTA_USD,
        SUPERVISION_PER_SHIFT,
        TAX_RATE,
        TERM_LOAN_RATE,
        TRUCK_DAY_COST,
        UNSKILLED_MIN_PAID_HOURS,
        UNSKILLED_PER_MACHINE_SHIFT,
        UNSKILLED_WAGE_RATIO,
        WARRANTY_COST,
        WEB_CAPACITY,
    )


@dataclass
class Alert:
    severity: str  # "CRITICAL", "WARNING", "SUCCESS", "INFO"
    category: str  # "Matéria-Prima", "Produção", "Montagem", "Tesouraria", "Qualidade", "Marketing"
    title: str
    message: str
    reason: str
    impact: str
    suggested_action: str


@dataclass
class SimulationResult:
    decisions: dict
    kpis: dict[str, float]
    pnl: dict[str, float]
    balance: dict[str, float]
    cashflow: dict[str, float]
    operations: dict[str, Any]
    hr: dict[str, Any]
    commercial: dict[str, Any]
    alerts: list[Alert] = field(default_factory=list)

    @property
    def has_critical_alerts(self) -> bool:
        return any(a.severity == "CRITICAL" for a in self.alerts)


# ----------------------------------------------------------------------------------------
# Cenários Pré-configurados para Y15Q2
# ----------------------------------------------------------------------------------------

def get_recommended_decisions(q: Quarter | None = None) -> dict:
    """Cenário Recomendado: Otimização Operacional e Arbitragem Financeira (Turnaround).
    
    Principais eixos auditados:
    1. Introduzir o Grande Melhoramento no Produto 1 (stock obsoleto é apenas 44 un., custo sucata ~0€).
    2. Manter Preços Competitivos de Mercado (P1=325€, P2=490€, P3=690€ na UE) para preservar margem bruta >50%.
    3. Encomendar 4.500 un. de MP Spot (evita rotura de stock crítica com apenas 1.468 un. iniciais).
    4. Programar compras de MP 3m (4.500 un.) e 6m (3.000 un.) para reduzir custo unitário médio futuro em ~20%.
    5. Elevar tempos de montagem (P1=125 min, P2=170 min, P3=330 min), absorvendo os 21 operários
       especializados a 94.9% da capacidade normal sem horas extraordinárias e eliminando defeitos.
    6. Salário de 12.00 €/h (regra do sindicato proíbe reduções salariais).
    7. Retirar 200.000 € do depósito a prazo para liquidar o descoberto bancário de 97.987 €,
       eliminando juros de penalização superiores a 15% ao ano.
    8. Expandir Website para 20 portas para anular a insatisfação de 56% e capturar vendas diretas.
    9. Produção equilibrada: P1=1.400, P2=1.050, P3=450 unidades (absorvendo o stock excedente de P3).
    10. Dividendo de 0,06 €/ação (180 k€) para impulsionar o Desempenho do Investimento.
    """
    return {
        # Publicidade e Imagem (k€)
        "adv": {
            "UE": {"Inst": 12.0, "P1": 14.0, "P2": 10.0, "P3": 10.0},
            "Nafta": {"Inst": 6.0, "P1": 6.0, "P2": 6.0, "P3": 5.0},
            "Internet": {"Inst": 6.0, "P1": 6.0, "P2": 5.0, "P3": 5.0},
        },
        # Preços de Venda (€ nos mercados UE/Net, $ no mercado Nafta)
        "price": {
            "UE": {"P1": 325.0, "P2": 490.0, "P3": 690.0},
            "Nafta": {"P1": 335.0, "P2": 490.0, "P3": 725.0},
            "Internet": {"P1": 375.0, "P2": 585.0, "P3": 855.0},
        },
        # Entregas programadas / compromisso de stock
        "deliv": {
            "UE": {"P1": 1050.0, "P2": 750.0, "P3": 300.0},
            "Nafta": {"P1": 120.0, "P2": 140.0, "P3": 60.0},
            "Internet": {"P1": 230.0, "P2": 160.0, "P3": 80.0},
        },
        # Produção planeada (unidades)
        "production": {"P1": 1400.0, "P2": 1050.0, "P3": 450.0},
        # Subcontratação (unidades)
        "subcontract": {"P1": 0.0, "P2": 0.0, "P3": 0.0},
        # Investigação & Desenvolvimento (k€)
        "rd": {"P1": 25.0, "P2": 15.0, "P3": 15.0},
        # Introdução de Grande Melhoramento (1=Sim, 0=Não)
        "improve": {"P1": 1.0, "P2": 0.0, "P3": 0.0},
        # Tempos de montagem (minutos/unidade)
        "assembly_min": {"P1": 125.0, "P2": 170.0, "P3": 330.0},
        # Matéria-prima extra para qualidade (%)
        "extra_mp_pct": {"P1": 3.0, "P2": 3.0, "P3": 2.0},
        # Agentes / Distribuidores
        "agents": {
            "UE": {"n": 3.0, "support": 10.0, "comm": 8.0},
            "Nafta": {"n": 2.0, "support": 8.0, "comm": 8.0},
            "Internet": {"n": 1.0, "support": 8.0, "comm": 5.0},
        },
        # Encomendas de Matéria-Prima (unidades)
        "mp_order": {"spot": 4500.0, "3m": 4500.0, "6m": 3000.0},
        # Horas de manutenção planeadas
        "maintenance_h": 100.0,
        # Turnos na fábrica de máquinas (1, 2 ou 3)
        "shifts": 2,
        # Website
        "ports": 20.0,
        "web_dev": 15.0,
        # Recursos Humanos
        "skilled_hire": 1.0,      # Contratar 1 especializado para manter pipeline de reformas
        "skilled_train": 0.0,
        "wage_eur": 12.00,        # Salário base operários especializados (€/h) - sindicalmente blindado
        "mgmt_budget": 30.0,      # Orçamento de desenvolvimento de gestão (k€)
        "training_days": 4.0,     # Dias de formação de pessoal
        # Finanças e Capital
        "shares": 0.0,            # Aumentos/reduções de capital (k€)
        "dividend": 6.0,          # Dividendos (cêntimos por ação) -> 180 k€
        "term_loan": 0.0,         # Empréstimos a prazo adicionais / reembolsados (k€)
        "deposit": -200.0,        # Movimento depósito a prazo (k€) -> -200k liquida descoberto
        "machines_buy": 0.0,
        "machines_sell": 0.0,
        "factory_expand": 0.0,
        "insurance": 2,           # Plano 2 (ótimo custo-benefício)
        "info_quotas": 1.0,       # Comprar informação de quotas de mercado
        "info_activity": 1.0,     # Comprar informação de atividade dos concorrentes
    }


def get_aggressive_decisions(q: Quarter | None = None) -> dict:
    """Cenário Agressivo: Expansão de Quota de Mercado e Crescimento Forte.
    
    Aumenta produção, investe fortemente em marketing e agentes, contrata mais operários
    e utiliza as máquinas a 98% da capacidade em 2 turnos.
    """
    d = get_recommended_decisions(q)
    d["production"] = {"P1": 1580.0, "P2": 1050.0, "P3": 620.0}
    d["deliv"] = {
        "UE": {"P1": 1250.0, "P2": 800.0, "P3": 440.0},
        "Nafta": {"P1": 160.0, "P2": 140.0, "P3": 90.0},
        "Internet": {"P1": 240.0, "P2": 170.0, "P3": 110.0},
    }
    d["price"]["UE"] = {"P1": 258.0, "P2": 378.0, "P3": 625.0}  # Preço competitivo
    d["adv"]["UE"] = {"Inst": 15.0, "P1": 22.0, "P2": 18.0, "P3": 14.0}
    d["mp_order"] = {"spot": 5500.0, "3m": 5000.0, "6m": 3500.0}
    d["skilled_hire"] = 2.0
    d["agents"]["UE"]["n"] = 4.0
    d["agents"]["Nafta"]["n"] = 2.0
    d["deposit"] = -250.0
    d["dividend"] = 12.0
    return d


def get_conservative_decisions(q: Quarter | None = None) -> dict:
    """Cenário Conservador: Maximização de Margem e Blindagem de Tesouraria.
    
    Preços ligeiramente mais elevados, controlo rigoroso de custos e preservação de liquidez.
    """
    d = get_recommended_decisions(q)
    d["production"] = {"P1": 1350.0, "P2": 900.0, "P3": 520.0}
    d["deliv"] = {
        "UE": {"P1": 1020.0, "P2": 680.0, "P3": 360.0},
        "Nafta": {"P1": 130.0, "P2": 110.0, "P3": 70.0},
        "Internet": {"P1": 200.0, "P2": 140.0, "P3": 80.0},
    }
    d["price"]["UE"] = {"P1": 272.0, "P2": 395.0, "P3": 655.0}  # Margem alta
    d["adv"]["UE"] = {"Inst": 10.0, "P1": 15.0, "P2": 12.0, "P3": 10.0}
    d["mp_order"] = {"spot": 4500.0, "3m": 4000.0, "6m": 2500.0}
    d["skilled_hire"] = 0.0
    d["deposit"] = -150.0
    d["dividend"] = 5.0
    return d


# ----------------------------------------------------------------------------------------
# Motor de Simulação Operacional e Financeira
# ----------------------------------------------------------------------------------------

def simulate_quarter(last_q: Quarter, decisions: dict) -> SimulationResult:
    """Executa a simulação determinística completa do trimestre com base nas decisões.
    
    Produz:
    - Verificações de restrições com Alertas detalhados (Severidade, Causa, Impacto, Ação).
    - Balanço de Operações: Horas de Máquina, Turnos, Horas de Montagem, Matéria-Prima.
    - Projeção de Recursos Humanos: Efetivos, Salários, Absentismo, Horas Extra.
    - Demonstração de Resultados (DRE) Projetada.
    - Demonstração do Fluxo de Caixa Projetado.
    - Balanço Patrimonial Projetado.
    - Estimativa de Cotação e Desempenho do Investimento.
    """
    d = copy.deepcopy(decisions)
    alerts: list[Alert] = []

    # 1. Macroeconomia e Câmbios (extraídos do último trimestre do Grupo)
    fx_usd = last_q.group.get("fx_eur_per_usd", 1.15)
    mp_spot_usd = last_q.group.get("mp_price_usd", {}).get("spot", 13.50)
    mp_3m_usd = last_q.group.get("mp_price_usd", {}).get("3m", 11.50)
    mp_6m_usd = last_q.group.get("mp_price_usd", {}).get("6m", 10.50)
    base_rate_pct = last_q.group.get("base_rate", {}).get("UE", 2.0)

    # 2. Operações: Matéria-Prima
    mp_start = last_q.resources.get("mp_end", 1468.0)
    mp_arriving = last_q.resources.get("mp_arriving_next", 0.0)
    mp_spot_ordered = float(d.get("mp_order", {}).get("spot", 0.0))
    mp_3m_ordered = float(d.get("mp_order", {}).get("3m", 0.0))
    mp_6m_ordered = float(d.get("mp_order", {}).get("6m", 0.0))

    prod = d.get("production", {"P1": 1600.0, "P2": 1100.0, "P3": 650.0})
    extra_mp = d.get("extra_mp_pct", {"P1": 3.0, "P2": 3.0, "P3": 3.0})

    # Consumo base e extra de matéria-prima
    mp_base_needed = sum(prod[p] * MP_PER_UNIT[p] for p in PRODUCTS)
    mp_extra_needed = sum(prod[p] * MP_PER_UNIT[p] * (extra_mp.get(p, 0.0) / 100.0) for p in PRODUCTS)
    mp_total_needed = mp_base_needed + mp_extra_needed

    mp_available_before_spot = mp_start + mp_arriving
    mp_total_available = mp_available_before_spot + mp_spot_ordered

    mp_shortage = max(0.0, mp_total_needed - mp_total_available)
    mp_auto_spot = mp_shortage  # O simulador compra automaticamente se faltar com penalização de 10%
    mp_final = max(0.0, mp_total_available - mp_total_needed)

    if mp_total_available < mp_total_needed:
        alerts.append(Alert(
            severity="CRITICAL",
            category="Matéria-Prima",
            title="Rotura Iminente de Matéria-Prima!",
            message=f"Consumo previsto de {mp_total_needed:,.0f} un. supera stock + chegadas ({mp_total_available:,.0f} un.) em {mp_shortage:,.0f} un.",
            reason="O stock inicial é de apenas 1.468 un. e não há encomendas de trimestres anteriores a chegar neste trimestre.",
            impact=f"O simulador forçará compras automáticas de emergência com sobretaxa punitiva de 10% (+{mp_shortage * (mp_spot_usd/fx_usd) * 0.10:,.0f} €) e risco de corte de produção caso o crédito esgote.",
            suggested_action=f"Aumentar a encomenda Spot de Matéria-Prima para pelo menos {math.ceil((mp_total_needed - mp_available_before_spot)/500)*500:,.0f} unidades imediatamente.",
        ))
    elif mp_final < 800:
        alerts.append(Alert(
            severity="WARNING",
            category="Matéria-Prima",
            title="Stock de Segurança de Matéria-Prima Muito Baixo",
            message=f"Stock final previsto é de {mp_final:,.0f} un. (< 800 un. recomendadas de margem de segurança).",
            reason="Flutuações de produção ou rejeição de componentes podem consumir a margem restante.",
            impact="Aumenta o risco operacional para o trimestre subsequente caso ocorra algum imprevisto.",
            suggested_action="Encomendar +500 unidades no mercado Spot ou reforçar compras a 3 meses.",
        ))
    else:
        alerts.append(Alert(
            severity="SUCCESS",
            category="Matéria-Prima",
            title="Abastecimento de Matéria-Prima Garantido",
            message=f"Stock disponível ({mp_total_available:,.0f} un.) cobre com segurança a produção de {mp_total_needed:,.0f} un. (stock final: {mp_final:,.0f} un.).",
            reason="A encomenda Spot planeada compensou exatamente a ausência de entregas contratadas.",
            impact="Zero compras automáticas com sobretaxa; custo de matéria-prima otimizado.",
            suggested_action="Manter escada de compras a 3m e 6m para capturar descontos a prazo.",
        ))

    # Custo de compras de matéria-prima (€)
    mp_spot_price_eur = (mp_spot_usd / 1000.0) / fx_usd
    mp_3m_price_eur = (mp_3m_usd / 1000.0) / fx_usd
    mp_6m_price_eur = (mp_6m_usd / 1000.0) / fx_usd

    cost_mp_spot = mp_spot_ordered * mp_spot_price_eur
    cost_mp_emergency = mp_auto_spot * mp_spot_price_eur * (1.0 + EMERGENCY_MP_SURCHARGE)
    cost_mp_extra_quality = mp_extra_needed * mp_spot_price_eur * EXTRA_QUALITY_MP_SURCHARGE

    # 3. Operações: Máquinas e Turnos
    machines_count = last_q.resources.get("machines_next", 4.0)
    shifts = int(d.get("shifts", 2))
    hours_per_mach = MACHINE_HOURS_BY_SHIFTS.get(shifts, 1068)
    mach_hours_nominal = machines_count * hours_per_mach

    mach_hours_needed = sum(prod[p] * (MACHINE_MIN[p] / 60.0) for p in PRODUCTS)

    maint_h_decision = float(d.get("maintenance_h", 160.0))
    # Estimativa de avaria / paragem de máquina (reduzida com boa manutenção)
    maint_expected = max(100.0, mach_hours_nominal * 0.04)
    mach_downtime_est = max(20.0, 120.0 - (maint_h_decision * 0.5))
    mach_hours_effective = mach_hours_nominal - mach_downtime_est

    mach_utilization_pct = (mach_hours_needed / mach_hours_effective) * 100.0 if mach_hours_effective else 0.0

    if mach_hours_needed > mach_hours_effective:
        alerts.append(Alert(
            severity="CRITICAL",
            category="Produção",
            title="Sobrecarga das Máquinas / Capacidade Insuficiente!",
            message=f"Produção exige {mach_hours_needed:,.0f} h de máquina, mas a capacidade máxima efetiva em {shifts} turnos é de {mach_hours_effective:,.0f} h (Sobrecarga de {mach_hours_needed - mach_hours_effective:,.0f} h).",
            reason=f"4 máquinas em {shifts} turno(s) não possuem horas físicas suficientes para processar todos os componentes programados.",
            impact="O simulador cortará a produção arbitrariamente ou aplicará subcontratação involuntária de emergência a custos exorbitantes.",
            suggested_action=f"Aumentar o número de turnos para {min(3, shifts + 1)} ou reduzir o lote de produção programado.",
        ))
    elif mach_utilization_pct > 95.0:
        alerts.append(Alert(
            severity="WARNING",
            category="Produção",
            title="Utilização de Máquinas Próxima do Limite Máximo",
            message=f"Taxa de utilização das máquinas está em {mach_utilization_pct:.1f}% ({mach_hours_needed:,.0f} h de {mach_hours_effective:,.0f} h).",
            reason="Margem de segurança para avarias imprevistas é estreita.",
            impact="Se ocorrer uma paragem não planeada, o plano de produção poderá sofrer atrasos parciais.",
            suggested_action="Reforçar as horas de manutenção preventiva para pelo menos 160 horas.",
        ))
    elif mach_utilization_pct < 70.0:
        alerts.append(Alert(
            severity="WARNING",
            category="Produção",
            title="Subutilização de Máquinas / Custos Fixos Ociosos",
            message=f"Utilização das máquinas está em apenas {mach_utilization_pct:.1f}% ({mach_hours_needed:,.0f} h de {mach_hours_effective:,.0f} h).",
            reason="A empresa está a pagar custos fixos de turnos e operadores de máquinas sem tirar pleno partido da capacidade.",
            impact="Custo unitário de fabrico sobe e a margem bruta diminui.",
            suggested_action="Aumentar a produção programada para diluir custos fixos ou rever os turnos.",
        ))
    else:
        alerts.append(Alert(
            severity="SUCCESS",
            category="Produção",
            title="Capacidade de Máquinas Otimizada",
            message=f"Utilização de {mach_utilization_pct:.1f}% ({mach_hours_needed:,.0f} h usadas em {mach_hours_effective:,.0f} h disponíveis).",
            reason="Excelente equilíbrio entre absorção de custos fixos e margem de segurança contra avarias.",
            impact="Minimiza custos unitários de maquinação sem risco de estrangulamento.",
            suggested_action="Manter 2 turnos com 160h de manutenção preventiva contratada.",
        ))

    # Operários não especializados necessários para máquinas
    unskilled_needed = int(machines_count * UNSKILLED_PER_MACHINE_SHIFT * shifts)
    unskilled_start = last_q.resources.get("unskilled_next", 27.0)
    unskilled_hired = max(0, unskilled_needed - int(unskilled_start))
    unskilled_fired = max(0, int(unskilled_start) - unskilled_needed)

    # 4. Operações: Montagem e Operários Especializados
    skilled_available = last_q.resources.get("skilled_next", 21.0)
    asm_min = d.get("assembly_min", {"P1": 125.0, "P2": 170.0, "P3": 330.0})

    # Verificar limite legal de salário (proibição de redução sindical)
    last_wage = last_q.decisions.get("wage_eur", 12.00)
    dec_wage = float(d.get("wage_eur", 12.00))
    if dec_wage < last_wage:
        alerts.append(Alert(
            severity="CRITICAL",
            category="Recursos Humanos",
            title="Violação de Acordo Sindical: Redução Salarial Proibida!",
            message=f"O salário decidido ({dec_wage:.2f} €/h) é inferior ao do trimestre anterior ({last_wage:.2f} €/h).",
            reason="O regulamento oficial do GMC (Secção 5) estipula que o acordo sindical não permite qualquer redução do salário base.",
            impact="O simulador anula a redução e aplica custos de insatisfação laboral, absentismo acrescido e risco iminente de greves.",
            suggested_action=f"Ajustar o salário base para pelo menos {last_wage:.2f} €/h.",
        ))

    # Verificar limites mínimos de montagem da Tabela 5
    for p in PRODUCTS:
        if asm_min.get(p, 0.0) < ASSEMBLY_MIN_MIN[p]:
            alerts.append(Alert(
                severity="CRITICAL",
                category="Montagem",
                title=f"Tempo de Montagem do {p} Abaixo do Mínimo Legal!",
                message=f"Tempo decidido ({asm_min.get(p, 0.0)} min) é inferior ao mínimo obrigatório de {ASSEMBLY_MIN_MIN[p]} min (Tabela 5).",
                reason="Violação direta das especificações técnicas de montagem do simulador.",
                impact="O simulador forçará automaticamente o tempo para o valor mínimo e aplicará penalizações.",
                suggested_action=f"Ajustar o tempo de montagem do {p} para pelo menos {ASSEMBLY_MIN_MIN[p]} minutos.",
            ))

    asm_hours_needed = sum(prod[p] * (asm_min.get(p, ASSEMBLY_MIN_MIN[p]) / 60.0) for p in PRODUCTS)
    asm_hours_normal_cap = skilled_available * HOURS_BASE
    asm_hours_sat_cap = skilled_available * HOURS_SAT.get(shifts, 42)
    asm_hours_sun_cap = skilled_available * HOURS_SUN.get(shifts, 72)
    asm_hours_max_legal = skilled_available * (HOURS_BASE + HOURS_SAT.get(shifts, 42) + HOURS_SUN.get(shifts, 72))

    idle_hours = max(0.0, asm_hours_normal_cap - asm_hours_needed)
    overtime_sat_hours = min(max(0.0, asm_hours_needed - asm_hours_normal_cap), asm_hours_sat_cap)
    overtime_sun_hours = max(0.0, asm_hours_needed - (asm_hours_normal_cap + asm_hours_sat_cap))

    if asm_hours_needed > asm_hours_max_legal:
        alerts.append(Alert(
            severity="CRITICAL",
            category="Montagem",
            title="Défice Crítico de Horas de Montagem!",
            message=f"Montagem exige {asm_hours_needed:,.0f} h, mas o teto legal máximo com todas as horas extraordinárias de {skilled_available:.0f} operários é de {asm_hours_max_legal:,.0f} h.",
            reason="Excesso de produção e/ou tempos de montagem elevados para o efetivo atual de 21 operários.",
            impact="Produtos inacabados, falhas graves no plano de entregas e aumento exponencial de absentismo/despedimentos.",
            suggested_action="Reduzir tempos de montagem ou diminuir o lote de produção programado.",
        ))
    elif idle_hours > 1500:
        alerts.append(Alert(
            severity="WARNING",
            category="Montagem",
            title="Horas Ociosas Excessivas de Operários Especializados",
            message=f"Existem {idle_hours:,.0f} horas normais não utilizadas de montagem ({idle_hours / HOURS_BASE:.1f} operários a receber salário sem trabalhar).",
            reason=f"Com 21 operários disponíveis (vs 17 no Q1), a capacidade normal subiu para {asm_hours_normal_cap:,.0f} h, mas foram planeadas apenas {asm_hours_needed:,.0f} h.",
            impact="A empresa pagará salário integral pelas horas ociosas, degradando o resultado líquido.",
            suggested_action="Aumentar o tempo de montagem dos produtos (ex: P1 para 125 min, P2 para 170 min, P3 para 330 min) para valorizar a qualidade e estrelas, ou produzir mais.",
        ))
    else:
        alerts.append(Alert(
            severity="SUCCESS",
            category="Montagem",
            title="Força de Trabalho de Montagem Equilibrada",
            message=f"{asm_hours_needed:,.0f} h de montagem planeadas para {asm_hours_normal_cap:,.0f} h normais disponíveis ({asm_hours_needed/asm_hours_normal_cap*100:.1f}% de ocupação normal).",
            reason="Absorção praticamente integral dos 21 operários qualificados sem horas ociosas e com recurso mínimo ou nulo a horas extraordinárias caras.",
            impact="Maximiza a qualidade percebida (estrelas) mantendo os custos de mão de obra sob controlo rigoroso.",
            suggested_action="Manter os tempos de montagem em 125/170/330 minutos.",
        ))

    # 5. Análise do Grande Melhoramento do Produto 1
    p1_improvement_available = last_q.products.get("P1", {}).get("improvement", "") == "Major"
    p1_stock = sum(last_q.products.get("P1", {}).get("stock", {}).values())
    p1_decided_improve = float(d.get("improve", {}).get("P1", 0.0)) > 0.5

    if p1_improvement_available and not p1_decided_improve:
        alerts.append(Alert(
            severity="WARNING",
            category="Qualidade",
            title="Oportunidade Estratégica Desperdiçada no Produto 1!",
            message="Existe um GRANDE MELHORAMENTO disponível para o P1 que NÃO foi introduzido nesta decisão.",
            reason="No Q1 o P1 sofreu 76 avarias de garantia (alerta ativo). O stock atual em armazém é de APENAS 44 unidades.",
            impact="O produto continuará a ser percebido como obsoleto e pouco fiável perante os rivais. Manter 44 unidades em stock para evitar refugo é economicamente insignificante face ao ganho de vendas.",
            suggested_action="Ativar a decisão de Grande Melhoramento no P1 (decisão = 1). O refugo de 44 unidades custa menos de 3.000€ e impulsiona a procura em 20%.",
        ))
    elif p1_decided_improve and p1_improvement_available:
        alerts.append(Alert(
            severity="SUCCESS",
            category="Qualidade",
            title="Introdução Oportuna do Grande Melhoramento no P1",
            message=f"Grande Melhoramento do P1 ativado! Stock residual obsoleto a saldar é mínimo ({p1_stock:.0f} unidades).",
            reason="Melhor timing possível: elimina o grave problema de garantias do Q1 (76 avarias) e renova a imagem de mercado.",
            impact="Aumento projetado de +15% a +25% na procura do P1 na UE, Nafta e Internet, com valorização de estrelas de produto.",
            suggested_action="Aproveitar a superioridade técnica para manter preços remuneradores.",
        ))

    # 6. Tesouraria e Descoberto Bancário
    prev_overdraft = last_q.balance.get("overdraft", 97987.0)
    prev_deposit = last_q.cashflow.get("deposit", 1150000.0)
    deposit_movement = float(d.get("deposit", -200.0)) * 1000.0  # decisão em k€

    proj_deposit_end = max(0.0, prev_deposit + deposit_movement)
    credit_limit = last_q.cashflow.get("credit_limit_next", 639000.0)

    if prev_overdraft > 0 and deposit_movement >= 0:
        alerts.append(Alert(
            severity="WARNING",
            category="Tesouraria",
            title="Ineficiência Financeira: Descoberto Caro com Depósito Ocioso!",
            message=f"A empresa mantém {prev_overdraft:,.0f} € em descoberto bancário (taxa > 15%) enquanto tem {prev_deposit:,.0f} € no depósito a prazo a render apenas 2%.",
            reason="Decisão de depósito a prazo não foi utilizada para resgatar fundos e liquidar a dívida de curto prazo.",
            impact=f"Perda líquida desnecessária de mais de 3.500 € em juros de penalização por trimestre.",
            suggested_action="Colocar a decisão de Depósito a Prazo em -150 k€ ou -200 k€ para eliminar o descoberto bancário a custo zero.",
        ))
    elif deposit_movement < 0 and abs(deposit_movement) >= prev_overdraft:
        alerts.append(Alert(
            severity="SUCCESS",
            category="Tesouraria",
            title="Arbitragem de Tesouraria Efetuada com Sucesso",
            message=f"Resgate de {abs(deposit_movement):,.0f} € do depósito a prazo liquida integralmente o descoberto de {prev_overdraft:,.0f} €.",
            reason="Substituição de financiamento caro por liquidez própria retida.",
            impact="Poupança direta de cerca de 3.600 € por trimestre em juros bancários e eliminação do risco de incumprimento.",
            suggested_action=f"Manter {proj_deposit_end:,.0f} € em depósito a prazo como reserva estratégica de liquidez.",
        ))

    # 7. Espaço Fabril (Tabela 26: 25% reservado a circulação; máquinas 25m², operário 10m², MP 5m²/1000un)
    total_factory_area = last_q.resources.get("factory_area_next", 500.0)
    area_machines = machines_count * SPACE_PER_MACHINE
    area_assembly = skilled_available * SPACE_PER_SKILLED
    area_mp = (mp_final / 1000.0) * SPACE_PER_1000_MP
    area_productive_used = area_machines + area_assembly + area_mp
    area_max_usable = total_factory_area * FACTORY_MAX_USE  # 75% da área total (25% é circulação fixa)
    area_free = area_max_usable - area_productive_used

    if area_productive_used > area_max_usable:
        alerts.append(Alert(
            severity="CRITICAL",
            category="Produção",
            title="Excesso de Ocupação da Área Fabril!",
            message=f"Espaço fabril ocupado por máquinas, operários e MP ({area_productive_used:.1f} m²) ultrapassa o limite útil ({area_max_usable:.1f} m² de {total_factory_area:.0f} m²).",
            reason="Área útil esgotada. O simulador reserva obrigatoriamente 25% para circulação e acessos.",
            impact="O simulador rejeitará a contratação de operários adicionais ou compra de novas máquinas.",
            suggested_action="Expandir a fábrica na decisão de construção ou reduzir volumes armazenados.",
        ))
    else:
        alerts.append(Alert(
            severity="SUCCESS",
            category="Produção",
            title="Espaço Fabril Conforme e com Folga",
            message=f"Área útil ocupada de {area_productive_used:.1f} m² de {area_max_usable:.1f} m² úteis ({area_free:.1f} m² livres de margem).",
            reason="Disposição física perfeitamente dimensionada para 4 máquinas, 21 operários e stock de segurança de MP.",
            impact="Operações decorrem sem restrições físicas ou penalizações de espaço.",
            suggested_action="Manter layout atual.",
        ))

    # ------------------------------------------------------------------------------------
    # 8. Estimativa Comercial e Vendas
    # ------------------------------------------------------------------------------------
    sales_units: dict[str, dict[str, float]] = {}
    revenue_market: dict[str, float] = {"UE": 0.0, "Nafta": 0.0, "Internet": 0.0}
    total_sales_units: dict[str, float] = {}

    for p in PRODUCTS:
        total_p_sold = 0.0
        sales_units[p] = {}
        for m in MARKETS:
            # Baseline de vendas do último trimestre
            base_sales = last_q.products.get(p, {}).get("sales", {}).get(m, 0.0)
            base_price = last_q.decisions.get("price", {}).get(m, {}).get(p, 100.0)
            new_price = d.get("price", {}).get(m, {}).get(p, base_price)

            # Elasticidade preço (~ -1.2 a -1.8)
            price_ratio = new_price / base_price if base_price > 0 else 1.0
            price_factor = math.pow(price_ratio, -1.35)

            # Efeito publicidade
            base_adv = last_q.decisions.get("adv", {}).get(m, {}).get(p, 10.0)
            new_adv = d.get("adv", {}).get(m, {}).get(p, 10.0)
            adv_factor = 1.0 + 0.12 * math.log(max(0.1, new_adv) / max(0.1, base_adv)) if base_adv > 0 else 1.0

            # Efeito Grande Melhoramento no P1
            improve_factor = 1.20 if (p == "P1" and p1_decided_improve) else 1.0

            # Estimativa de procura
            est_demand = max(10.0, base_sales * price_factor * adv_factor * improve_factor)

            # Entregas programadas / disponibilidade
            deliv = d.get("deliv", {}).get(m, {}).get(p, est_demand)
            sold = min(est_demand, deliv)

            sales_units[p][m] = round(sold, 1)
            total_p_sold += sold

            # Receita (€ na UE/Net, $ convertido para € em Nafta)
            if m == "Nafta":
                rev_eur = (sold * new_price) / fx_usd
            else:
                rev_eur = sold * new_price
            revenue_market[m] += rev_eur

        total_sales_units[p] = total_p_sold

    # Refugo do stock obsoleto se Grande Melhoramento for ativado
    salvage_revenue = 0.0
    if p1_decided_improve and p1_improvement_available:
        salvage_revenue = p1_stock * REJECT_VALUE["P1"]

    total_gross_revenue = sum(revenue_market.values()) + salvage_revenue

    # ------------------------------------------------------------------------------------
    # 9. Demonstração de Resultados (DRE) Projetada
    # ------------------------------------------------------------------------------------
    # Custos de Matéria-Prima consumida
    cogs_mp = (mp_base_needed * mp_spot_price_eur) + cost_mp_extra_quality + cost_mp_emergency

    # Custos de Mão de Obra
    wage_base = float(d.get("wage_eur", 11.20))
    cost_skilled_normal = skilled_available * HOURS_BASE * wage_base
    cost_skilled_sat = overtime_sat_hours * wage_base * 1.5
    cost_skilled_sun = overtime_sun_hours * wage_base * 2.0
    cost_skilled_total = cost_skilled_normal + cost_skilled_sat + cost_skilled_sun

    unskilled_wage = wage_base * UNSKILLED_WAGE_RATIO
    cost_unskilled_base = unskilled_needed * HOURS_BASE * unskilled_wage
    cost_unskilled_shift = cost_unskilled_base * SHIFT_PREMIUM.get(shifts, 0.0)
    cost_unskilled_total = cost_unskilled_base + cost_unskilled_shift

    # Custos Diretos de Máquinas e Produção
    cost_supervision = SUPERVISION_PER_SHIFT * shifts
    cost_mach_overhead = OVERHEAD_PER_MACHINE * machines_count
    cost_mach_running = mach_hours_needed * MACHINE_RUN_COST_HOUR
    cost_maintenance = maint_h_decision * MAINT_COST_CONTRACT
    cost_planning_inspect = sum(prod.values()) * (1.0 + 1.0)

    # Depreciações (2.5% sobre edifícios e máquinas)
    mach_book_val = last_q.balance.get("machines", 1070870.0)
    buildings_val = last_q.balance.get("buildings", 250000.0)
    depreciation_est = (mach_book_val + buildings_val) * DEPRECIATION_RATE_Q

    # Custos de Transporte e Armazenagem
    transp_est = 25000.0  # estimativa consistente com histórico
    storage_est = 12000.0

    # Custo Total das Vendas (COGS)
    cogs_total = (
        cogs_mp
        + cost_skilled_total
        + cost_unskilled_total
        + cost_supervision
        + cost_mach_overhead
        + cost_mach_running
        + cost_maintenance
        + cost_planning_inspect
        + transp_est
        + storage_est
    )

    gross_profit = total_gross_revenue - cogs_total

    # Custos Administrativos e Estruturais
    total_adv_spend = sum(
        sum(d["adv"][m].values()) for m in MARKETS
    ) * 1000.0

    total_rd_spend = sum(d.get("rd", {}).values()) * 1000.0

    # Custos de Agentes (Apoio + Comissão)
    agent_support_cost = sum(d["agents"][m]["support"] * 1000.0 for m in MARKETS)
    agent_comm_cost = sum(
        revenue_market[m] * (d["agents"][m]["comm"] / 100.0) for m in MARKETS
    )

    # Custos de RH (Recrutamento, Treino, Consultores)
    skilled_hire = float(d.get("skilled_hire", 0.0))
    skilled_train = float(d.get("skilled_train", 0.0))
    consultant_days = float(d.get("training_days", 0.0))
    mgmt_dev_cost = float(d.get("mgmt_budget", 0.0)) * 1000.0

    hr_admin_cost = (
        skilled_hire * HR_COSTS["skilled"]["recruit"]
        + skilled_train * HR_COSTS["skilled"]["train"]
        + unskilled_hired * HR_COSTS["unskilled"]["recruit"]
        + unskilled_fired * HR_COSTS["unskilled"]["dismiss"]
        + consultant_days * HR_COSTS["consultant_day"]
        + mgmt_dev_cost
    )

    # Website (portas + desenvolvimento)
    ports = float(d.get("ports", 20.0))
    web_dev_cost = float(d.get("web_dev", 15.0)) * 1000.0
    website_cost = (ports * ISP_PORT_COST) + web_dev_cost

    # Seguro e Informação
    ins_tier = int(d.get("insurance", 2))
    ins_rate = INSURANCE.get(ins_tier, (0.002, 0.0035))[1]
    ins_premium = (last_q.balance.get("nca", 1370870.0) + last_q.balance.get("inv_products", 83141.0)) * ins_rate

    info_cost = (
        (INFO_COST["quotas"] if d.get("info_quotas", 0) else 0)
        + (INFO_COST["actividade"] if d.get("info_activity", 0) else 0)
    )

    fixed_admin_base = 65000.0  # base de escritório, contabilidade, gestão de topo
    total_admin_expenses = (
        total_adv_spend
        + total_rd_spend
        + agent_support_cost
        + agent_comm_cost
        + hr_admin_cost
        + website_cost
        + ins_premium
        + info_cost
        + fixed_admin_base
        + depreciation_est
    )

    ebit = gross_profit - total_admin_expenses

    # Resultados Financeiros
    interest_in = proj_deposit_end * (base_rate_pct / 100.0 / 4.0)

    # Saldo descoberto projetado
    est_net_cash_flow = gross_profit - total_admin_expenses - cost_mp_spot
    proj_overdraft = max(0.0, prev_overdraft + deposit_movement - est_net_cash_flow)
    if proj_deposit_end > 0 and deposit_movement < -prev_overdraft:
        proj_overdraft = 0.0

    overdraft_rate = (base_rate_pct + (OVERDRAFT_AUTH_SPREAD * 100)) / 100.0 / 4.0
    interest_paid = proj_overdraft * overdraft_rate

    ebt = ebit + interest_in - interest_paid
    income_tax = max(0.0, ebt * TAX_RATE) if ebt > 0 else 0.0
    net_profit = ebt - income_tax
    eps = net_profit / 3000000.0  # 3 milhões de ações

    # ------------------------------------------------------------------------------------
    # 10. Balanço e Fluxo de Caixa Projetados
    # ------------------------------------------------------------------------------------
    dividend_cents = float(d.get("dividend", 0.0))
    dividends_paid = (dividend_cents / 100.0) * 3000000.0

    prev_equity = last_q.balance.get("equity", 3058227.0)
    proj_equity = prev_equity + net_profit - dividends_paid

    # Cotação estimada (modelo proxy de valuation GMC baseado em ROE e crescimento de capitais próprios)
    base_share_price = last_q.group.get("companies", {}).get(1, {}).get("share_price", 111.32)
    roe_quarterly = (net_profit / proj_equity) if proj_equity > 0 else 0.0
    div_yield = dividends_paid / (base_share_price * 3000000.0) if base_share_price > 0 else 0.0

    # Valuation proxy calibrado com o histórico (preço evolui entre +2% a +10% com ROE forte e dividendos)
    valuation_factor = 1.0 + (roe_quarterly * 0.90) + (div_yield * 0.50) + (0.015 if p1_decided_improve else -0.01)
    est_share_price = round(base_share_price * max(0.90, min(1.25, valuation_factor)), 2)
    est_inv_perf = round(est_share_price * 30000.0 + (dividends_paid * 0.01), 0)  # proxy do índice oficial

    # Pegada de Carbono (t CO2e)
    co2_factory = (last_q.resources.get("factory_area_next", 400.0) * CO2_PER_M2) / 1000.0
    co2_mach = (mach_hours_needed * CO2_PER_MACHINE_HOUR) / 1000.0
    co2_asm = (asm_hours_needed * CO2_PER_ASSEMBLY_HOUR) / 1000.0
    co2_total = co2_factory + co2_mach + co2_asm

    kpis = {
        "Vendas": total_gross_revenue,
        "Custo das Vendas": cogs_total,
        "Resultado Bruto": gross_profit,
        "Margem Bruta %": (gross_profit / total_gross_revenue) * 100.0 if total_gross_revenue else 0.0,
        "EBIT": ebit,
        "Margem EBIT %": (ebit / total_gross_revenue) * 100.0 if total_gross_revenue else 0.0,
        "Resultado Líquido": net_profit,
        "Margem Líquida %": (net_profit / total_gross_revenue) * 100.0 if total_gross_revenue else 0.0,
        "EPS (€)": eps,
        "Capitais Próprios": proj_equity,
        "ROE % (trim.)": (net_profit / proj_equity) * 100.0 if proj_equity else 0.0,
        "Cotação Estimada (€)": est_share_price,
        "Desempenho Investimento": est_inv_perf,
        "CO2 Total (t)": co2_total,
    }

    pnl = {
        "Vendas": total_gross_revenue,
        "Custo das Vendas": -cogs_total,
        "Resultado Bruto": gross_profit,
        "Publicidade": -total_adv_spend,
        "Investigação & Desenvolvimento": -total_rd_spend,
        "Agentes e Comissões": -(agent_support_cost + agent_comm_cost),
        "Recursos Humanos e Formação": -hr_admin_cost,
        "Website e ISP": -website_cost,
        "Seguro e Outros": -(ins_premium + info_cost + fixed_admin_base),
        "Depreciações": -depreciation_est,
        "EBIT (Resultado Operacional)": ebit,
        "Juros Recebidos": interest_in,
        "Juros Pagos": -interest_paid,
        "EBT (Antes de Impostos)": ebt,
        "Imposto sobre o Rendimento": -income_tax,
        "Resultado Líquido": net_profit,
    }

    balance = {
        "Activo Não Corrente": (mach_book_val + buildings_val - depreciation_est),
        "Inventário Estimado": (mp_final * mp_spot_price_eur) + 80000.0,
        "Clientes a Receber": total_gross_revenue * 0.60,
        "Depósito a Prazo": proj_deposit_end,
        "Caixa / Saldo Líquido": max(0.0, 50000.0 - proj_overdraft),
        "Total Activo": (mach_book_val + buildings_val - depreciation_est) + (mp_final * mp_spot_price_eur) + 80000.0 + (total_gross_revenue * 0.60) + proj_deposit_end,
        "Descoberto Bancário": proj_overdraft,
        "Fornecedores a Pagar": cost_mp_spot + 150000.0,
        "Capitais Próprios": proj_equity,
    }

    cashflow = {
        "Recebimentos de Clientes": total_gross_revenue * 0.75,
        "Pagamentos Operacionais": -(cogs_total + total_admin_expenses - depreciation_est),
        "Juros Recebidos": interest_in,
        "Juros Pagos": -interest_paid,
        "Movimento Depósito": deposit_movement,
        "Dividendos Pagos": -dividends_paid,
        "Descoberto Final Estimado": proj_overdraft,
        "Depósito Final Estimado": proj_deposit_end,
    }

    operations = {
        "mach_hours_needed": mach_hours_needed,
        "mach_hours_effective": mach_hours_effective,
        "mach_utilization_pct": mach_utilization_pct,
        "shifts": shifts,
        "asm_hours_needed": asm_hours_needed,
        "asm_hours_normal_cap": asm_hours_normal_cap,
        "idle_hours": idle_hours,
        "overtime_sat_hours": overtime_sat_hours,
        "overtime_sun_hours": overtime_sun_hours,
        "mp_start": mp_start,
        "mp_spot_ordered": mp_spot_ordered,
        "mp_3m_ordered": mp_3m_ordered,
        "mp_6m_ordered": mp_6m_ordered,
        "mp_total_needed": mp_total_needed,
        "mp_final": mp_final,
        "mp_shortage": mp_shortage,
        "area_used_est": area_productive_used,
        "area_max_allowed": area_max_usable,
        "area_free": area_free,
        "co2_total": co2_total,
    }

    hr = {
        "skilled_available": skilled_available,
        "skilled_hire": skilled_hire,
        "skilled_train": skilled_train,
        "unskilled_needed": unskilled_needed,
        "unskilled_start": unskilled_start,
        "unskilled_hired": unskilled_hired,
        "unskilled_fired": unskilled_fired,
        "wage_base": wage_base,
        "cost_skilled_total": cost_skilled_total,
        "cost_unskilled_total": cost_unskilled_total,
    }

    commercial = {
        "sales_units": sales_units,
        "revenue_market": revenue_market,
        "total_sales_units": total_sales_units,
        "salvage_revenue": salvage_revenue,
        "total_gross_revenue": total_gross_revenue,
    }

    return SimulationResult(
        decisions=d,
        kpis=kpis,
        pnl=pnl,
        balance=balance,
        cashflow=cashflow,
        operations=operations,
        hr=hr,
        commercial=commercial,
        alerts=alerts,
    )
