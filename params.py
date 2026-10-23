"""Parâmetros oficiais do simulador GMC (Manual do Participante, secção TABELAS).

Todos os valores foram retirados do HTML oficial do manual (manual_html/manual.html).
Cada constante indica a tabela de origem para poder ser verificada.
"""

PRODUCTS = ["P1", "P2", "P3"]
MARKETS = ["UE", "Nafta", "Internet"]
PRODUCT_NAMES = {"P1": "Produto 1", "P2": "Produto 2", "P3": "Produto 3"}

# Tabela 5 - Parâmetros de fabrico por unidade
MACHINE_MIN = {"P1": 60, "P2": 75, "P3": 120}          # minutos de maquinação
ASSEMBLY_MIN_MIN = {"P1": 100, "P2": 150, "P3": 300}   # tempo mínimo de montagem
MP_PER_UNIT = {"P1": 1, "P2": 2, "P3": 3}              # unidades de matéria-prima

# Tabela 6 - Conservação
MAINT_COST_CONTRACT = 85.0     # €/hora contratada por máquina
MAINT_COST_EMERGENCY = 175.0   # €/hora não contratada

# Tabela 7 - Horas máximas por máquina por trimestre e operários não especializados
MACHINE_HOURS_BY_SHIFTS = {1: 576, 2: 1068, 3: 1602}
UNSKILLED_PER_MACHINE_SHIFT = 4

# Tabela 8 - Valorização de produtos rejeitados
REJECT_VALUE = {"P1": 40, "P2": 80, "P3": 120}

# Tabela 9 - Preço do serviço de garantia por unidade
WARRANTY_COST = {"P1": 60, "P2": 150, "P3": 250}

# Tabela 10 - Custos de produção
SUPERVISION_PER_SHIFT = 12500
OVERHEAD_PER_MACHINE = 3500
MACHINE_RUN_COST_HOUR = 8
PLANNING_PER_UNIT = 1
INSPECTION_PER_UNIT = 1

# Tabela 11 - Capacidade do contentor (unidades)
CONTAINER_CAP = {"P1": 500, "P2": 250, "P3": 125}

# Tabela 12 - Transporte
TRUCK_DAY_COST = 650
ATLANTIC_CROSSING = 8000
MAX_KM_DAY = 400
DIST_NAFTA_PORT_ROUNDTRIP = 500    # 250 km x 2 (confirmado no relatório: 500 km)
DIST_INTERNET_ROUNDTRIP = 300      # 150 km x 2 (confirmado no relatório: 300 km)

# Tabela 13 - Compras e armazenagem
PURCHASING_OVERHEAD = 7500
EMERGENCY_MP_SURCHARGE = 0.10      # compra imprevista = preço ocasião + 10%
EXTRA_QUALITY_MP_SURCHARGE = 0.50  # matéria-prima extra = preço ocasião + 50%
EXT_STORAGE_MP = 2.50
EXT_STORAGE_COMPONENT = 3.00
STORAGE_PRODUCT_EU_NET = 3.50
STORAGE_PRODUCT_NAFTA_USD = 4.0

# Tabela 15 - Recursos humanos (recrutamento, rescisão, treino)
HR_COSTS = {
    "skilled": {"recruit": 2000, "dismiss": 5000, "train": 8500},
    "unskilled": {"recruit": 1000, "dismiss": 2000},
    "consultant_day": 1000,
}

# Tabela 16 - Horas máximas por homem por trimestre
HOURS_BASE = 420
HOURS_SAT = {1: 84, 2: 42, 3: 42}     # pagas a base + 50%
HOURS_SUN = {1: 72, 2: 72, 3: 72}     # pagas a base + 100%
SHIFT_PREMIUM = {1: 0.0, 2: 1 / 3, 3: 2 / 3}

# Tabela 17 - Mínimos
UNSKILLED_MIN_PAID_HOURS = 360
SKILLED_MIN_WAGE = 9.0
UNSKILLED_WAGE_RATIO = 0.65
STRIKE_HOURS_WEEK = 48

# Tabela 18 - Máquinas
MACHINE_PRICE = 300000
DEPRECIATION_RATE_Q = 0.025
MACHINE_DISMANTLE_COST = 60000

# Tabela 20 - Parâmetros financeiros
CREDIT_CONTROL_PER_UNIT = 1.0
FACTORY_FIXED_PER_M2 = 20.0
TAX_RATE = 0.30
OVERDRAFT_AUTH_SPREAD = 0.04
OVERDRAFT_UNAUTH_SPREAD = 0.10
TERM_LOAN_RATE = 0.10

# Tabela 22 - Seguros: plano -> (franquia %, prémio %) sobre Activo Não Corrente + Inventário
INSURANCE = {
    0: (1.00, 0.0),
    1: (0.001, 0.006),
    2: (0.002, 0.0035),
    3: (0.003, 0.0020),
    4: (0.004, 0.0010),
}

# Tabela 23 - Prazos de recebimento (fracção das vendas do trimestre que fica por receber)
RECEIVABLE_FRACTION = {"UE": 60 / 90, "Nafta": 1.0, "Internet": 0.0}

# Tabela 4 - Internet
INTERNET_USAGE_FEE = 0.03
ISP_JOIN_COST = 7500
ISP_PORT_COST = 1000

# Tabela 2 - Informação de marketing
INFO_COST = {"quotas": 5000, "actividade": 7500}

# Tabela 3 - Agentes / distribuidores
AGENT_MIN_SUPPORT = 5000
AGENT_RECRUIT = 7500
AGENT_DISMISS = 5000

# Tabela 25 - Capacidade do website (portas -> visitas/hora reais)
WEB_CAPACITY = {1: 2, 2: 7, 5: 31, 10: 81, 20: 190, 50: 537}

# Tabela 26 - Espaço
LAND_MAX_USE = 0.80
FACTORY_MAX_USE = 0.75
SPACE_PER_MACHINE = 25
SPACE_PER_SKILLED = 10
SPACE_PER_1000_MP = 5
SPACE_WIP = {"P1": 0.25, "P2": 0.5, "P3": 1.0}

# Tabela 27 - Pegada de carbono (kg CO2e)
CO2_PER_M2 = 9.50
CO2_PER_MACHINE_HOUR = 2.82
CO2_PER_ASSEMBLY_HOUR = 0.52

