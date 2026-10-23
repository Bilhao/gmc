"""Leitura dos Relatórios de Gestão do GMC (ficheiros PT_Hst*.Xls / relatórios trimestrais).

O layout dos separadores é fixo (verificado em Y14Q1..Y15Q1), por isso a leitura é feita
por coordenadas, com verificação dos rótulos para detectar alterações de formato.
"""
from __future__ import annotations

import glob
import io
import os
import re
from dataclasses import dataclass, field

import pandas as pd
import xlrd

try:
    from .params import MARKETS, PRODUCTS
except ImportError:
    from params import MARKETS, PRODUCTS

PROD_COLS = {"P1": 20, "P2": 22, "P3": 24}        # separador Resources and products
DEC_PROD_COLS = {"P1": 5, "P2": 7, "P3": 9}        # separador Your decisions
COMPANY_COLS = list(range(5, 13))                  # Group information: empresas 1..8


def _num(v, default=0.0):
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return default
    return default


def _txt(v):
    return str(v).strip() if v is not None else ""


class LayoutError(Exception):
    pass


@dataclass
class Quarter:
    label: str
    year: int
    q: int
    source: str
    decisions: dict = field(default_factory=dict)
    resources: dict = field(default_factory=dict)
    products: dict = field(default_factory=dict)
    admin: dict = field(default_factory=dict)
    pnl: dict = field(default_factory=dict)
    balance: dict = field(default_factory=dict)
    cashflow: dict = field(default_factory=dict)
    group: dict = field(default_factory=dict)

    @property
    def order(self):
        return self.year * 10 + self.q


def _check(sheet, r, c, expected):
    got = _txt(sheet.cell_value(r, c)).lower()
    if expected.lower() not in got:
        raise LayoutError(f"[{sheet.name}] célula ({r},{c}) esperava '{expected}', encontrou '{got}'")


def parse_workbook(path_or_bytes, name: str | None = None) -> Quarter:
    if isinstance(path_or_bytes, (bytes, bytearray)):
        wb = xlrd.open_workbook(file_contents=path_or_bytes)
        src = name or "upload"
    else:
        wb = xlrd.open_workbook(path_or_bytes)
        src = os.path.basename(path_or_bytes)

    d = wb.sheet_by_name("Your decisions")
    r = wb.sheet_by_name("Resources and products")
    f = wb.sheet_by_name("Financial statements")
    g = wb.sheet_by_name("Group information")

    _check(r, 5, 2, "Terreno detido")
    _check(f, 6, 8, "Vendas")
    _check(g, 36, 2, "Cotação")
    _check(d, 13, 13, "Agentes UE")

    D = lambda rr, cc: _num(d.cell_value(rr, cc))
    R = lambda rr, cc: _num(r.cell_value(rr, cc))
    F = lambda rr, cc: _num(f.cell_value(rr, cc))
    G = lambda rr, cc: _num(g.cell_value(rr, cc))

    year = int(G(1, 10)) or int(D(8, 15))
    q = int(G(1, 12)) or int(D(8, 18))
    label = f"Y{str(year)[-2:]}Q{q}"
    qt = Quarter(label=label, year=year, q=q, source=src)

    # ---------------- Decisões tomadas nesse trimestre ----------------
    mkt_rows = {"UE": 0, "Nafta": 1, "Internet": 2}
    dec = {
        "adv": {m: {"Inst": D(13 + i, 4), **{p: D(13 + i, c) for p, c in DEC_PROD_COLS.items()}} for m, i in mkt_rows.items()},
        "price": {m: {p: D(18 + i, c) for p, c in DEC_PROD_COLS.items()} for m, i in mkt_rows.items()},
        "deliv": {m: {p: D(23 + i, c) for p, c in DEC_PROD_COLS.items()} for m, i in mkt_rows.items()},
        "improve": {p: D(28, c) for p, c in DEC_PROD_COLS.items()},
        "rd": {p: D(29, c) for p, c in DEC_PROD_COLS.items()},
        "assembly_min": {p: D(30, c) for p, c in DEC_PROD_COLS.items()},
        "extra_mp_pct": {p: D(31, c) for p, c in DEC_PROD_COLS.items()},
        "subcontract": {p: D(34, c) for p, c in DEC_PROD_COLS.items()},
        "agents": {
            "UE": {"n": D(13, 15), "support": D(13, 19), "comm": D(13, 22)},
            "Nafta": {"n": D(14, 15), "support": D(14, 19), "comm": D(14, 22)},
            "Internet": {"n": 1, "support": D(15, 19), "comm": D(15, 22)},
        },
        "mp_order": {"spot": D(18, 15), "3m": D(18, 19), "6m": D(18, 22)},
        "maintenance_h": D(19, 15),
        "shifts": int(D(19, 22)) or 1,
        "ports": D(20, 15),
        "web_dev": D(20, 22),
        "skilled_hire": D(23, 15),
        "skilled_train": D(23, 22),
        "wage_eur": D(24, 15) + D(24, 16) / 100.0,
        "mgmt_budget": D(25, 15),
        "training_days": D(25, 22),
        "shares": D(28, 15),
        "dividend": D(28, 22),
        "term_loan": D(29, 15),
        "deposit": D(29, 22),
        "machines_buy": D(30, 15),
        "machines_sell": D(30, 22),
        "factory_expand": D(31, 15),
        "insurance": int(D(31, 22)),
        "info_quotas": D(34, 15),
        "info_activity": D(34, 22),
    }
    qt.decisions = dec

    # ---------------- Recursos ----------------
    qt.resources = {
        "land": R(5, 6), "access": R(6, 6), "land_free": R(7, 6), "factory_area_next": R(8, 6),
        "space_circulation": R(9, 6), "space_machines": R(10, 6), "space_assembly": R(11, 6),
        "space_mp": R(12, 6), "space_free": R(13, 6),
        "machines_dismantled": R(16, 6), "machines_last": R(17, 6), "machines_bought": R(18, 6),
        "machines_next": R(19, 6),
        "mach_hours_avail": R(21, 6), "mach_downtime": R(22, 6), "mach_hours_used": R(23, 6),
        "maint_hours": R(24, 6), "mach_eff": R(25, 6),
        "mp_start": R(28, 6), "mp_spot": R(29, 6), "mp_shortage": R(30, 6), "mp_lost": R(31, 6),
        "mp_used": R(32, 6), "mp_end": R(33, 6),
        "mp_next_last_q": R(35, 6), "mp_next_prev_q": R(36, 6), "mp_next2": R(37, 6),
        "web_ports": R(40, 6), "web_visits": R(41, 6), "web_failed_pct": R(42, 6), "web_dissatisfaction": R(43, 6),
        "skilled_start": R(5, 13), "unskilled_start": R(5, 14),
        "skilled_hired": R(6, 13), "unskilled_hired": R(6, 14), "skilled_trained": R(7, 13),
        "skilled_fired": R(8, 13), "unskilled_fired": R(8, 14),
        "skilled_left": R(9, 13), "unskilled_left": R(9, 14),
        "skilled_next": R(10, 13), "unskilled_next": R(10, 14),
        "asm_hours_avail": R(14, 14), "absenteeism": R(15, 14),
        "absenteeism_flag": _txt(r.cell_value(15, 15)) == "!" or _txt(r.cell_value(15, 15)) not in ("", "0.0"),
        "asm_hours_used": R(16, 14), "strike_warning": R(18, 14),
        "agents": {m: {"start": R(24, c), "lost": R(25, c), "dismissed": R(26, c), "new": R(27, c), "next": R(28, c)}
                   for m, c in zip(MARKETS, (12, 13, 14))},
        "transport": {m: {"km": R(34, c), "loads": R(35, c)} for m, c in zip(MARKETS, (12, 13, 14))},
        "co2": {"heating": R(41, 13), "production": R(42, 13), "total": R(43, 13)},
    }
    qt.resources["mp_arriving_next"] = qt.resources["mp_next_last_q"] + qt.resources["mp_next_prev_q"]

    # ---------------- Produtos ----------------
    prods = {}
    for p, c in PROD_COLS.items():
        flag = _txt(r.cell_value(34, c + 1))
        prods[p] = {
            "scheduled": R(4, c), "produced": R(5, c), "rejected": R(6, c),
            "deliv": {m: R(10 + i, c) for i, m in enumerate(MARKETS)},
            "orders": {m: R(15 + i, c) for i, m in enumerate(MARKETS)},
            "sales": {m: R(20 + i, c) for i, m in enumerate(MARKETS)},
            "backlog": {m: R(25 + i, c) for i, m in enumerate(MARKETS)},
            "stock": {m: R(29 + i, c) for i, m in enumerate(MARKETS)},
            "warranty": R(34, c), "warranty_flag": flag == "!",
            "improvement": _txt(r.cell_value(37, c)),
            "comp_used": R(40, c), "comp_bought": R(41, c), "comp_end": R(42, c),
        }
    qt.products = prods

    # ---------------- Despesas administrativas ----------------
    admin_labels = ["Publicidade", "Distribuidor Internet", "Fornecedor Serviço Internet (ISP)", "Agentes e Distribuidores",
                    "Departamento de Vendas", "Serviço de Garantia", "Investigação e Desenvolvimento",
                    "Desenvolvimento de Website", "Recrutamento e Formação", "Conservação das Máquinas",
                    "Armazenagem e Compras", "Informações", "Controle de Crédito", "Prémios de Seguros",
                    "Administração e Gestão", "Outros Custos"]
    qt.admin = {lab: F(6 + i, 5) for i, lab in enumerate(admin_labels)}
    qt.admin["TOTAL"] = F(22, 5)
    qt.admin["insurance_claim"] = F(31, 5)
    qt.admin["insurance_deductible"] = F(32, 5)

    qt.pnl = {
        "sales": F(6, 11), "inv_start": F(8, 11), "components": F(9, 11), "raw_materials": F(10, 11),
        "machine_ops": F(11, 11), "unskilled_wages": F(12, 11), "skilled_wages": F(13, 11),
        "quality_control": F(14, 11), "transport": F(15, 11), "inv_end": F(16, 11), "cogs": F(17, 11),
        "gross": F(18, 11), "admin": F(19, 11), "insurance_income": F(20, 11), "depreciation": F(21, 11),
        "ebit": F(22, 11), "fin_income": F(23, 11), "fin_cost": F(24, 11), "taxable": F(25, 11),
        "tax": F(26, 11), "net": F(27, 11), "eps": F(28, 11), "dividends": F(30, 11),
        "retained_prev": F(32, 11), "retained": F(33, 11),
        "taxable_cum_prev": F(26, 5), "taxable_cum": F(27, 5),
    }
    qt.balance = {
        "land": F(7, 17), "buildings": F(8, 17), "machines": F(9, 17), "nca": F(10, 17),
        "inv_products": F(13, 17), "inv_components": F(14, 17), "inv_mp": F(15, 17),
        "receivables": F(16, 17), "cash": F(17, 17), "ca": F(18, 17), "assets": F(19, 17),
        "tax_payable": F(22, 17), "payables": F(23, 17), "overdraft": F(24, 17), "cl": F(25, 17),
        "term_loans": F(26, 17), "equity_liab": F(28, 17),
        "share_capital": F(31, 17), "share_premium": F(32, 17), "retained": F(33, 17), "equity": F(34, 17),
    }
    qt.cashflow = {
        "receipts": F(7, 23), "insurance": F(8, 23), "payments": F(9, 23), "tax": F(10, 23), "cfo": F(11, 23),
        "interest_in": F(14, 23), "asset_sales": F(15, 23), "capex": F(16, 23), "cfi": F(17, 23),
        "shares_issued": F(20, 23), "buyback": F(21, 23), "dividends": F(22, 23), "loans": F(23, 23),
        "interest_paid": F(24, 23), "cff": F(25, 23), "change": F(27, 23), "cash_prev": F(28, 23),
        "cash_end": F(29, 23), "deposit": F(30, 23),
        "credit_limit_next": F(32, 23), "credit_potential_next": F(33, 23),
    }

    # ---------------- Informação do grupo ----------------
    companies = {}
    for i, c in enumerate(COMPANY_COLS, start=1):
        companies[i] = {
            "share_price": G(36, c), "market_cap": G(37, c), "dividends": G(39, c), "inv_perf": G(40, c),
            "price": {
                "P1": {"UE": G(44, c), "Nafta": G(45, c), "Internet": G(46, c)},
                "P2": {"UE": G(47, c), "Nafta": G(48, c), "Internet": G(49, c)},
                "P3": {"UE": G(50, c), "Nafta": G(51, c), "Internet": G(52, c)},
            },
            "employees": G(54, c), "skilled_wage": G(55, c) / 100.0, "agents": G(56, c),
            "nca": G(64, c), "inventory": G(65, c), "receivables": G(66, c), "cash": G(67, c),
            "tax_payable": G(70, c), "payables": G(71, c), "overdraft": G(72, c), "term_loans": G(74, c),
            "share_capital": G(77, c), "share_premium": G(78, c), "retained": G(79, c), "equity": G(80, c),
            "adv_total": G(101, c), "rd_total": G(102, c),
            "stars": {k: _txt(g.cell_value(rr, c)).count("*") for k, rr in
                      (("P1", 104), ("P2", 105), ("P3", 106), ("Web", 107))},
            "share": {p: {m: G(88 + pi * 3 + mi, c) for mi, m in enumerate(MARKETS)} for pi, p in enumerate(PRODUCTS)},
        }
    report = " ".join(_txt(g.cell_value(rr, 5)) for rr in range(23, 32)).strip()
    qt.group = {
        "group_no": G(1, 8),
        "gdp": {"UE": G(5, 6), "Nafta": G(5, 7), "RoW": G(5, 8)},
        "unemployment": {"UE": G(6, 6), "Nafta": G(6, 7)},
        "trade_balance": {"UE": G(7, 6), "Nafta": G(7, 7)},
        "base_rate": {"UE": G(10, 6), "Nafta": G(10, 7)},
        "fx_eur_per_usd": G(10, 11),
        "construction_m2": G(13, 6),
        "component_cost_min": {p: G(16, 6 + i) for i, p in enumerate(PRODUCTS)},
        "component_cost_max": {p: G(17, 6 + i) for i, p in enumerate(PRODUCTS)},
        "mp_price_usd": {"spot": G(20, 6), "3m": G(20, 7), "6m": G(20, 8)},
        "business_report": re.sub(r"\s+", " ", report),
        "paid_info_requested": _txt(g.cell_value(85, 10)).lower() != "not requested",
        "companies": companies,
    }
    return qt


def load_folder(folder: str, prefix: str = "PT_") -> list[Quarter]:
    files = sorted(glob.glob(os.path.join(folder, f"{prefix}*.Xls")) + glob.glob(os.path.join(folder, f"{prefix}*.xls")))
    qs = {}
    for fp in files:
        try:
            qt = parse_workbook(fp)
            qs[qt.label] = qt
        except Exception as e:  # noqa: BLE001
            print(f"[GMC] erro a ler {fp}: {e}")
    return sorted(qs.values(), key=lambda x: x.order)


# ----------------------------------------------------------------------------------------
# Tabelas analíticas (pandas)
# ----------------------------------------------------------------------------------------

def kpi_frame(qs: list[Quarter]) -> pd.DataFrame:
    rows = []
    for qt in qs:
        p, b, cf, rs = qt.pnl, qt.balance, qt.cashflow, qt.resources
        own = qt.group["companies"].get(1, {})
        units_sold = sum(sum(v["sales"].values()) for v in qt.products.values())
        units_prod = sum(v["produced"] for v in qt.products.values())
        rejected = sum(v["rejected"] for v in qt.products.values())
        warranty = sum(v["warranty"] for v in qt.products.values())
        orders = sum(sum(v["orders"].values()) for v in qt.products.values())
        backlog = sum(sum(v["backlog"].values()) for v in qt.products.values())
        stock = sum(sum(v["stock"].values()) for v in qt.products.values())
        sales = p["sales"]
        rows.append({
            "Trimestre": qt.label,
            "Cotação": own.get("share_price", 0),
            "Desempenho Investimento": own.get("inv_perf", 0),
            "Vendas": sales,
            "Custo das Vendas": p["cogs"],
            "Resultado Bruto": p["gross"],
            "Despesas Administrativas": p["admin"],
            "Depreciações": p["depreciation"],
            "EBIT": p["ebit"],
            "Resultado Líquido": p["net"],
            "EPS": p["eps"],
            "Margem Bruta %": 100 * p["gross"] / sales if sales else None,
            "Margem EBIT %": 100 * p["ebit"] / sales if sales else None,
            "Margem Líquida %": 100 * p["net"] / sales if sales else None,
            "Capitais Próprios": b["equity"],
            "ROE % (trim.)": 100 * p["net"] / b["equity"] if b["equity"] else None,
            "Activo Total": b["assets"],
            "Clientes": b["receivables"],
            "Fornecedores": b["payables"],
            "Depósito/Caixa (balanço)": b["cash"],
            "Financiamentos obtidos": b["overdraft"],
            "Saldo de caixa líquido": cf["cash_end"],
            "Fluxo Operacional": cf["cfo"],
            "Liquidez geral": b["ca"] / b["cl"] if b["cl"] else None,
            "Prazo médio recebimento (dias)": 90 * b["receivables"] / sales if sales else None,
            "Limite financiamento próx. trim.": cf["credit_limit_next"],
            "Potencial crédito próx. trim.": cf["credit_potential_next"],
            "Unidades vendidas": units_sold,
            "Unidades produzidas": units_prod,
            "Encomendas (unid.)": orders,
            "Encomendas em atraso": backlog,
            "Inventário produtos (unid.)": stock,
            "Taxa de rejeição %": 100 * rejected / units_prod if units_prod else None,
            "Taxa de garantia %": 100 * warranty / units_sold if units_sold else None,
            "Taxa de serviço %": 100 * units_sold / orders if orders else None,
            "Horas máquina disp.": rs["mach_hours_avail"],
            "Horas máquina usadas": rs["mach_hours_used"],
            "Utilização máquinas %": 100 * rs["mach_hours_used"] / rs["mach_hours_avail"] if rs["mach_hours_avail"] else None,
            "Eficiência máquinas %": rs["mach_eff"],
            "Horas montagem disp.": rs["asm_hours_avail"],
            "Horas montagem usadas": rs["asm_hours_used"],
            "Utilização montagem %": 100 * rs["asm_hours_used"] / rs["asm_hours_avail"] if rs["asm_hours_avail"] else None,
            "Absentismo (h)": rs["absenteeism"],
            "Op. especializados (próx.)": rs["skilled_next"],
            "Op. não especializados (próx.)": rs["unskilled_next"],
            "Saídas não especializados": rs["unskilled_left"],
            "Saídas especializados": rs["skilled_left"],
            "MP inicial": rs["mp_start"], "MP comprada ocasião": rs["mp_spot"], "MP usada": rs["mp_used"], "MP final": rs["mp_end"],
            "MP a chegar próx. trim.": rs["mp_arriving_next"],
            "Preço MP ocasião ($/1000)": qt.group["mp_price_usd"]["spot"],
            "Preço MP 3m ($/1000)": qt.group["mp_price_usd"]["3m"],
            "Preço MP 6m ($/1000)": qt.group["mp_price_usd"]["6m"],
            "Câmbio €/$": qt.group["fx_eur_per_usd"],
            "Taxa juro BCE %": qt.group["base_rate"]["UE"],
            "Desemprego UE %": qt.group["unemployment"]["UE"],
            "Desemprego Nafta %": qt.group["unemployment"]["Nafta"],
            "PIB UE": qt.group["gdp"]["UE"], "PIB Nafta": qt.group["gdp"]["Nafta"],
            "Visitas website": rs["web_visits"], "Insatisfação website": rs["web_dissatisfaction"],
            "CO2 total (t)": rs["co2"]["total"],
            "Publicidade total": qt.admin.get("Publicidade", 0),
            "I&D total": qt.admin.get("Investigação e Desenvolvimento", 0),
        })
    return pd.DataFrame(rows).set_index("Trimestre")


def product_market_frame(qs: list[Quarter]) -> pd.DataFrame:
    rows = []
    for qt in qs:
        for p, v in qt.products.items():
            for m in MARKETS:
                price = qt.decisions["price"][m][p]
                rows.append({
                    "Trimestre": qt.label, "Produto": p, "Mercado": m,
                    "Preço": price, "Entregas": v["deliv"][m], "Encomendas": v["orders"][m],
                    "Vendas (unid.)": v["sales"][m], "Atraso": v["backlog"][m], "Inventário": v["stock"][m],
                    "Receita": price * v["sales"][m],
                    "Publicidade (k€)": qt.decisions["adv"][m][p],
                    "Vendas perdidas (est.)": max(0.0, v["orders"][m] - v["sales"][m]),
                })
    return pd.DataFrame(rows)


def product_frame(qs: list[Quarter]) -> pd.DataFrame:
    rows = []
    for qt in qs:
        for p, v in qt.products.items():
            sold = sum(v["sales"].values())
            rows.append({
                "Trimestre": qt.label, "Produto": p,
                "Programado": v["scheduled"], "Produzido": v["produced"], "Rejeitado": v["rejected"],
                "Vendido": sold, "Encomendas": sum(v["orders"].values()), "Inventário": sum(v["stock"].values()),
                "Atraso": sum(v["backlog"].values()), "Garantias": v["warranty"], "Alerta garantia": v["warranty_flag"],
                "Melhoramento disponível": v["improvement"],
                "Tempo montagem (min)": qt.decisions["assembly_min"][p], "I&D (k€)": qt.decisions["rd"][p],
                "Melhoramento introduzido": qt.decisions["improve"][p],
                "Taxa rejeição %": 100 * v["rejected"] / v["produced"] if v["produced"] else None,
                "Taxa garantia %": 100 * v["warranty"] / sold if sold else None,
                "Estrelas": qt.group["companies"].get(1, {}).get("stars", {}).get(p, 0),
            })
    return pd.DataFrame(rows)


def admin_frame(qs: list[Quarter]) -> pd.DataFrame:
    data = {qt.label: {k: v for k, v in qt.admin.items() if k not in ("TOTAL", "insurance_claim", "insurance_deductible")} for qt in qs}
    return pd.DataFrame(data)


def companies_frame(qt: Quarter) -> pd.DataFrame:
    rows = []
    for i, c in qt.group["companies"].items():
        rows.append({
            "Empresa": i, "Cotação": c["share_price"], "Capitalização": c["market_cap"], "Desempenho Inv.": c["inv_perf"],
            "Dividendos": c["dividends"], "Capitais Próprios": c["equity"], "Caixa": c["cash"],
            "Financiamentos": c["overdraft"] + c["term_loans"], "Clientes": c["receivables"], "Inventário": c["inventory"],
            "Publicidade": c["adv_total"], "I&D": c["rd_total"], "Empregados": c["employees"],
            "Salário especializado (€/h)": c["skilled_wage"], "Agentes": c["agents"],
            "★ P1": c["stars"]["P1"], "★ P2": c["stars"]["P2"], "★ P3": c["stars"]["P3"], "★ Web": c["stars"]["Web"],
            **{f"Preço {p} {m}": c["price"][p][m] for p in PRODUCTS for m in MARKETS},
        })
    return pd.DataFrame(rows).set_index("Empresa")

