"""
Integração WhatsApp para ÉVORA Connect
Comandos e parsers para automação via WhatsApp
"""
import re
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from decimal import Decimal


# ============================================================================
# PARSERS DE COMANDOS E DETECÇÃO
# ============================================================================

@dataclass
class ParsedListing:
    """Resultado do parse de uma oferta/produto"""
    title: str
    brand: Optional[str]
    price_value: Optional[Decimal]
    price_currency: Optional[str]
    promo_labels: List[str]
    media_urls: List[str]
    discount_pct: Optional[Decimal] = None


@dataclass
class Intent:
    """Intenção detectada em um comando"""
    name: str
    args: Dict


# Regex patterns
PRICE_RE = re.compile(r'(?P<curr>\$|US\$|R\$)\s?(?P<val>\d+(?:[\.,]\d{1,2})?)', re.I)
QTY_RE = re.compile(r'(?P<qty>\d+)\s*x', re.I)
DISC_RE = re.compile(r'(?P<pct>\d{1,3})\s?%(\s?off|\s?desconto)?', re.I)
NF_RE = re.compile(r'\bNF\b|\bnota\s*fiscal\b', re.I)
URL_RE = re.compile(r'(https?://\S+)', re.I)


# Mapa de marcas (expandir conforme necessário)
BRAND_MAP = {
    "victoria's secret": ["victoria's secret", "victorias secret", "vs", "victoria"],
    "adidas": ["adidas"],
    "nike": ["nike", "niké"],
    "puma": ["puma"],
    "bath & body works": ["bath & body works", "bbw", "bbworks", "bathandbody"],
    "gap": ["gap"],
    "carter's": ["carters", "carter's", "carter"],
    "hollister": ["hollister"],
    "old navy": ["old navy", "oldnavy"],
}


def detect_brand(text: str) -> Optional[str]:
    """Detecta marca no texto"""
    low = text.lower()
    for name, aliases in BRAND_MAP.items():
        for alias in aliases:
            if alias in low:
                return name.title()
    return None


def normalize_price(text: str) -> Tuple[Optional[Decimal], Optional[str]]:
    """Extrai preço e moeda do texto"""
    m = PRICE_RE.search(text)
    if not m:
        return None, None
    
    val = m.group("val").replace(",", ".")
    price = Decimal(val)
    
    curr_symbol = m.group("curr").upper()
    if "R$" in curr_symbol or "BRL" in curr_symbol:
        currency = "BRL"
    else:
        currency = "USD"
    
    return price, currency


def extract_discount(text: str) -> Optional[Decimal]:
    """Extrai porcentagem de desconto"""
    m = DISC_RE.search(text)
    if m:
        return Decimal(m.group("pct"))
    return None


def has_invoice_mention(text: str) -> bool:
    """Verifica se menciona nota fiscal"""
    return bool(NF_RE.search(text))


def extract_urls(text: str) -> List[str]:
    """Extrai URLs do texto"""
    return URL_RE.findall(text)


def parse_listing(text: str) -> ParsedListing:
    """
    Parse de mensagem para detectar oferta/produto
    
    Exemplos:
        "VS Body Splash $7.99 - cupom SUDSY"
        "Nike Air Max 42 por R$ 299,90"
        "Hollister BOGO 50% off - último dia!"
    """
    brand = detect_brand(text)
    price, currency = normalize_price(text)
    discount = extract_discount(text)
    urls = extract_urls(text)
    has_nf = has_invoice_mention(text)
    
    # Detecta labels promocionais
    labels = []
    promo_keywords = {
        "bogo": "bogo",
        "last day": "ultimo_dia",
        "último dia": "ultimo_dia",
        "clearance": "clearance",
        "cupom": "cupom",
        "desconto": "desconto",
        "off": "desconto",
        "promoção": "promocao",
        "promo": "promocao",
    }
    
    text_lower = text.lower()
    for keyword, label in promo_keywords.items():
        if keyword in text_lower and label not in labels:
            labels.append(label)
    
    if has_nf:
        labels.append("nota_fiscal")
    
    return ParsedListing(
        title=text[:200].strip(),
        brand=brand,
        price_value=price,
        price_currency=currency,
        promo_labels=labels,
        media_urls=urls,
        discount_pct=discount
    )


def parse_intent(text: str) -> Optional[Intent]:
    """
    Parse de comandos WhatsApp
    
    Comandos suportados:
        /comprar 2x VS Body Splash Love Spell (250ml)
        /entrega keeper | keeper-correio | comprador-traz
        /pagar pix | cartao 6x
        /status | /status PED#1234
        /rastrear PED#1234
        /retirar hoje 16h
        /vincular ABC123
        /sou_shopper TOKEN
        /sou_keeper TOKEN
        /checkin PED#1234 3 volumes
        /slot PED#1234 -> A3-14
        /mail PED#1234 rastreio=USPS123
        /comprado PED#1234 nota=IMG123
    """
    t = text.strip()
    low = t.lower()
    
    # ========== COMANDOS DO CLIENTE ==========
    
    if low.startswith("/comprar"):
        # Extrai quantidade e item
        q = QTY_RE.search(t)
        qty = int(q.group("qty")) if q else 1
        item = QTY_RE.sub("", t.replace("/comprar", "", 1)).strip()
        return Intent("ADD_TO_CART", {"qty": qty, "query": item})
    
    if low.startswith("/entrega"):
        if "keeper-correio" in low or "correio" in low:
            # Tenta extrair CEP
            cep_match = re.search(r'(\d{5}[-\s]?\d{3})', t)
            cep = cep_match.group(1) if cep_match else None
            return Intent("SET_DELIVERY", {"mode": "MAIL_KEEPER", "cep": cep})
        elif "comprador-traz" in low or "traz" in low:
            return Intent("SET_DELIVERY", {"mode": "BRING_BUYER"})
        else:
            return Intent("SET_DELIVERY", {"mode": "PICKUP_KEEPER"})
    
    if low.startswith("/pagar"):
        # Extrai método e parcelas
        installments = 1
        if "x" in low:
            m = re.search(r'(\d+)\s*x', low)
            if m:
                installments = int(m.group(1))
        
        if "pix" in low:
            method = "PIX"
        elif "cart" in low or "créd" in low or "cred" in low:
            method = "CARTAO_CREDITO"
        elif "déb" in low or "deb" in low:
            method = "CARTAO_DEBITO"
        elif "bolet" in low:
            method = "BOLETO"
        else:
            method = "PIX"  # padrão
        
        return Intent("PAY", {"method": method, "installments": installments})
    
    if low.startswith("/status"):
        # Extrai número do pedido se houver
        pedido = None
        m = re.search(r'PED#?(\d+)', t, re.I)
        if m:
            pedido = m.group(1)
        return Intent("STATUS", {"pedido": pedido})
    
    if low.startswith("/rastrear"):
        m = re.search(r'PED#?(\d+)', t, re.I)
        pedido = m.group(1) if m else None
        return Intent("TRACK", {"pedido": pedido})
    
    if low.startswith("/retirar"):
        when = t.replace("/retirar", "", 1).strip()
        return Intent("SCHEDULE_PICKUP", {"when": when})
    
    # ========== VINCULAÇÃO E CADASTRO ==========
    
    if low.startswith("/vincular"):
        parts = t.split()
        token = parts[1].upper() if len(parts) > 1 else None
        return Intent("LINK_GROUP", {"token": token})
    
    if low.startswith("/sou_shopper"):
        parts = t.split()
        token = parts[1].upper() if len(parts) > 1 else None
        return Intent("REGISTER_SHOPPER", {"token": token})
    
    if low.startswith("/sou_keeper"):
        parts = t.split()
        token = parts[1].upper() if len(parts) > 1 else None
        return Intent("REGISTER_KEEPER", {"token": token})
    
    # ========== COMANDOS DO KEEPER ==========
    
    if low.startswith("/checkin"):
        rest = t.split(" ", 1)[1] if " " in t else ""
        # Extrai pedido
        m = re.search(r'PED#?(\d+)', rest, re.I)
        pedido = m.group(1) if m else None
        # Extrai volumes
        m = re.search(r'(\d+)\s*volumes?', rest, re.I)
        volumes = int(m.group(1)) if m else 1
        return Intent("KEEPER_CHECKIN", {"pedido": pedido, "volumes": volumes, "rest": rest})
    
    if low.startswith("/slot"):
        rest = t.split(" ", 1)[1] if " " in t else ""
        m = re.search(r'PED#?(\d+)', rest, re.I)
        pedido = m.group(1) if m else None
        # Extrai código do slot (ex: A3-14)
        m = re.search(r'([A-Z]\d+[-\s]?\d+)', rest, re.I)
        slot = m.group(1) if m else None
        return Intent("KEEPER_SLOT", {"pedido": pedido, "slot": slot})
    
    if low.startswith("/mail"):
        rest = t.split(" ", 1)[1] if " " in t else ""
        m = re.search(r'PED#?(\d+)', rest, re.I)
        pedido = m.group(1) if m else None
        # Extrai rastreio
        m = re.search(r'rastreio[=:\s]+([A-Z0-9\-]+)', rest, re.I)
        tracking = m.group(1) if m else None
        # Extrai custo
        price, currency = normalize_price(rest)
        return Intent("KEEPER_MAIL", {
            "pedido": pedido,
            "tracking": tracking,
            "cost": price,
            "currency": currency
        })
    
    if low.startswith("/entregue"):
        m = re.search(r'PED#?(\d+)', t, re.I)
        pedido = m.group(1) if m else None
        return Intent("KEEPER_DELIVERED", {"pedido": pedido})
    
    # ========== COMANDOS DO COMPRADOR/SHOPPER ==========
    
    if low.startswith("/assumir"):
        m = re.search(r'PED#?(\d+)', t, re.I)
        pedido = m.group(1) if m else None
        return Intent("BUYER_ASSIGN", {"pedido": pedido})
    
    if low.startswith("/comprado"):
        rest = t.split(" ", 1)[1] if " " in t else ""
        m = re.search(r'PED#?(\d+)', rest, re.I)
        pedido = m.group(1) if m else None
        # Extrai valor
        price, currency = normalize_price(rest)
        # Extrai referência da nota
        m = re.search(r'nota[=:\s]+([A-Z0-9\-]+)', rest, re.I)
        nota = m.group(1) if m else None
        return Intent("BUYER_PURCHASED", {
            "pedido": pedido,
            "valor": price,
            "currency": currency,
            "nota": nota
        })
    
    if low.startswith("/entrega-br"):
        rest = t.split(" ", 1)[1] if " " in t else ""
        m = re.search(r'PED#?(\d+)', rest, re.I)
        pedido = m.group(1) if m else None
        # Extrai voo
        m = re.search(r'voo[=:\s]+([A-Z0-9\-]+)', rest, re.I)
        voo = m.group(1) if m else None
        # Extrai data
        m = re.search(r'(\d{1,2}[\/\-]\d{1,2})', rest)
        data = m.group(1) if m else None
        return Intent("BUYER_BRING", {"pedido": pedido, "voo": voo, "data": data})
    
    # Nenhum comando reconhecido
    return None


def calculate_score(parsed: ParsedListing) -> int:
    """
    Calcula score de relevância da oferta
    Usado para priorizar notificações e destaques
    """
    score = 0
    
    # Tem marca conhecida
    if parsed.brand:
        score += 2
    
    # Tem preço
    if parsed.price_value:
        score += 2
    
    # Tem desconto grande
    if parsed.discount_pct:
        if parsed.discount_pct >= 50:
            score += 3
        elif parsed.discount_pct >= 30:
            score += 2
        else:
            score += 1
    
    # Labels importantes
    high_priority = ["ultimo_dia", "clearance", "nota_fiscal"]
    for label in parsed.promo_labels:
        if label in high_priority:
            score += 1
    
    # Tem URL (link direto)
    if parsed.media_urls:
        score += 1
    
    return score


# ============================================================================
# HELPERS DE FORMATAÇÃO
# ============================================================================

def format_currency(value: Decimal, currency: str = "BRL") -> str:
    """Formata valor monetário"""
    if currency == "BRL":
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        return f"US$ {value:,.2f}"


def format_order_number(order_id: int) -> str:
    """Gera número de pedido formatado"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%y%m%d")
    return f"PED#{timestamp}{order_id:04d}"


def extract_order_id(text: str) -> Optional[int]:
    """Extrai ID do pedido de um texto com PED#..."""
    m = re.search(r'PED#?\d{6}(\d{4})', text, re.I)
    if m:
        return int(m.group(1))
    return None






