#!/usr/bin/env python3
"""
Script de surveillance de token Solana avec alertes Telegram + Pushover
Utilise l'API DexScreener pour vérifier le market cap et envoie des alertes aux paliers
"""

import requests
import time
from typing import Optional, Dict, Tuple

# ==================== CONFIGURATION ====================
# Liste des tokens à surveiller
TOKENS = [
    {
        "name": "MMGA",
        "address": "87B6mb9KBjaF5NHrB3H33f7grdUHi4oWmMErjhZ5bonk",
        "buy_market_cap": 1000000,
        "amount_invested": 35.40
    },
    {
        "name": "Hungry",
        "address": "DkrrbsbxPaTt6Nt1nF1JvRmCLU4K6n3ZWVavvjvWpump",
        "buy_market_cap": 23300,
        "amount_invested": 2.96
    },
    {
        "name": "Alone",
        "address": "4jorbNYWamEJQd8DajmFxbqk9ugVr9DHyPTAUyT6pump",
        "buy_market_cap": 208000,
        "amount_invested": 3.99
    },
    {
        "name": "experiment",
        "address": "GiC36DeL5wi7gMjHmyKiM3niNdP9My8g4MocZWdJBPGk",
        "buy_market_cap": 86100,
        "amount_invested": 7.26
    },
    {
        "name": "CHUD",
        "address": "CowfNwWv6sT16K1hJCrqjvf4jaUvBDqsEa5HvdPpump",
        "buy_market_cap": 246000,
        "amount_invested": 15.48
    },
    {
        "name": "AMELIA",
        "address": "63mtzLvGzRwfkFdWNGrMgKPD9rCHEHvCsqz5KPVBpump",
        "buy_market_cap": 401000,
        "amount_invested": 7.00
    },
    {
        "name": "MAGIKARP",
        "address": "8PxtLPZqhkdqXgGvCPVcvvJqMxjzGLpHpxVfpTTZpump",
        "buy_market_cap": 137000,
        "amount_invested": 4.30
    },
]

# Configuration Telegram
TELEGRAM_TOKEN = "8554678342:AAHmD1OB3OHwgkFwisqlUv2y5VC7HTwlOnI"
TELEGRAM_CHAT_ID = "1764001989"

# Configuration Pushover
PUSHOVER_USER_KEY = "u7e73r7bdjaj24usb2qns9kw7biw1z"
PUSHOVER_API_TOKEN = "ar6opmfea5bowkn1g6bf9d2ve19pnm"

# Intervalle de vérification en secondes (5 minutes = 300 secondes)
CHECK_INTERVAL = 300

# Multiplicateurs à surveiller (gains)
MULTIPLIERS = [1.5, 2, 3, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

# Seuils de perte à surveiller (en pourcentage négatif)
LOSS_THRESHOLDS = [-10, -25, -50, -75]
# =======================================================


def get_token_data(token_address: str) -> Optional[Tuple[float, float]]:
    """
    Récupère le prix et market cap actuels du token Solana via l'API DexScreener
    """
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("pairs") and len(data["pairs"]) > 0:
            pair = data["pairs"][0]
            price_usd = pair.get("priceUsd")
            market_cap = pair.get("marketCap") or pair.get("fdv")
            
            if price_usd and market_cap:
                return float(price_usd), float(market_cap)
        
        print(f"⚠️  Aucune paire trouvée pour le token {token_address}")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la récupération des données: {e}")
        return None
    except (KeyError, ValueError, IndexError) as e:
        print(f"❌ Erreur lors du parsing des données: {e}")
        return None


def send_telegram_alert(message: str) -> bool:
    """
    Envoie une alerte via Telegram
    """
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur Telegram: {e}")
        return False


def send_pushover_alert(title: str, message: str, priority: int = 0) -> bool:
    """
    Envoie une alerte via Pushover
    """
    try:
        url = "https://api.pushover.net/1/messages.json"
        payload = {
            "token": PUSHOVER_API_TOKEN,
            "user": PUSHOVER_USER_KEY,
            "title": title,
            "message": message,
            "priority": priority,
        }
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur Pushover: {e}")
        return False


def send_alert(token_name: str, alert_type: str, threshold: float, current_market_cap: float,
               buy_market_cap: float, amount_invested: float, current_price: float) -> None:
    """
    Envoie une alerte via Telegram ET Pushover
    """
    current_multiplier = current_market_cap / buy_market_cap
    current_value = amount_invested * current_multiplier
    pnl = current_value - amount_invested
    gain_percentage = (current_multiplier - 1) * 100
    
    if alert_type == "gain":
        emoji = "🚀"
        if threshold >= 10:
            mult_display = f"x{int(threshold)}"
        else:
            mult_display = f"x{threshold:.1f}"
        title = f"📈 {token_name} {mult_display}"
    else:
        emoji = "🔻"
        title = f"📉 {token_name} {int(threshold)}%"
    
    # Message Telegram
    telegram_message = (
        f"{emoji} **ALERTE TOKEN SOLANA**\n\n"
        f"🪙 **Token: {token_name}**\n\n"
        f"💰 **PNL: ${pnl:,.2f}** ({gain_percentage:+.1f}%)\n\n"
        f"📊 MC achat: ${buy_market_cap:,.0f}\n"
        f"📊 MC actuel: ${current_market_cap:,.0f}\n"
        f"💵 Investi: ${amount_invested:,.2f}\n"
        f"💵 Valeur: ${current_value:,.2f}"
    )
    
    # Message Pushover (plus court)
    pushover_message = (
        f"PNL: ${pnl:,.2f} ({gain_percentage:+.1f}%)\n"
        f"MC: ${current_market_cap:,.0f}\n"
        f"Valeur: ${current_value:,.2f}"
    )
    
    priority = 1 if alert_type == "gain" else 0
    
    telegram_ok = send_telegram_alert(telegram_message)
    pushover_ok = send_pushover_alert(title, pushover_message, priority)
    
    print(f"      Telegram: {'✅' if telegram_ok else '❌'} | Pushover: {'✅' if pushover_ok else '❌'}")


def main():
    print("=" * 60)
    print("🚀 Script de surveillance de tokens Solana")
    print("   Alertes: Telegram + Pushover")
    print("=" * 60)
    print(f"📊 Tokens surveillés: {len(TOKENS)}")
    print(f"⏱️  Vérification toutes les {CHECK_INTERVAL // 60} minutes")
    print(f"📈 Gains: {', '.join([f'x{m}' if m >= 10 else f'x{m:.1f}' for m in MULTIPLIERS])}")
    print(f"📉 Pertes: {', '.join([f'{l}%' for l in LOSS_THRESHOLDS])}")
    print("=" * 60)
    
    # Tracker les seuils déjà alertés
    # Pour chaque token, on stocke le dernier seuil alerté
    last_gain_alerted: Dict[str, float] = {token["name"]: 0 for token in TOKENS}
    last_loss_alerted: Dict[str, float] = {token["name"]: 0 for token in TOKENS}
    
    # Premier passage : initialiser les seuils sans envoyer d'alertes
    print("\n🔄 Initialisation - Détection des seuils actuels...")
    for token in TOKENS:
        token_name = token["name"]
        token_address = token["address"]
        buy_market_cap = token["buy_market_cap"]
        
        token_data = get_token_data(token_address)
        if token_data is None:
            continue
        
        _, current_market_cap = token_data
        current_multiplier = current_market_cap / buy_market_cap
        pnl_percent = (current_multiplier - 1) * 100
        
        # Trouver le dernier seuil de gain dépassé
        for mult in MULTIPLIERS:
            if current_multiplier >= mult:
                last_gain_alerted[token_name] = mult
        
        # Trouver le dernier seuil de perte dépassé
        for loss in LOSS_THRESHOLDS:
            if pnl_percent <= loss:
                last_loss_alerted[token_name] = loss
        
        print(f"   {token_name}: x{current_multiplier:.2f} ({pnl_percent:+.1f}%)")
        if last_gain_alerted[token_name] > 0:
            print(f"      → Dernier gain alerté: x{last_gain_alerted[token_name]}")
        if last_loss_alerted[token_name] < 0:
            print(f"      → Dernière perte alertée: {int(last_loss_alerted[token_name])}%")
    
    print("\n✅ Initialisation terminée - Début de la surveillance\n")
    
    iteration = 0
    
    while True:
        iteration += 1
        print(f"\n{'='*60}")
        print(f"[{iteration}] Vérification...")
        print(f"{'='*60}")
        
        for token in TOKENS:
            token_name = token["name"]
            token_address = token["address"]
            buy_market_cap = token["buy_market_cap"]
            amount_invested = token["amount_invested"]
            
            token_data = get_token_data(token_address)
            if token_data is None:
                print(f"🪙 {token_name}: ⚠️ Erreur API")
                continue
            
            current_price, current_market_cap = token_data
            current_multiplier = current_market_cap / buy_market_cap
            pnl_percent = (current_multiplier - 1) * 100
            current_value = amount_invested * current_multiplier
            pnl = current_value - amount_invested
            
            print(f"🪙 {token_name}: x{current_multiplier:.2f} | PNL: ${pnl:,.2f} ({pnl_percent:+.1f}%)")
            
            # Vérifier les GAINS (seulement si nouveau seuil franchi)
            for mult in MULTIPLIERS:
                if current_multiplier >= mult and mult > last_gain_alerted[token_name]:
                    print(f"   🎉 Nouveau palier x{mult} atteint!")
                    send_alert(token_name, "gain", mult, current_market_cap,
                              buy_market_cap, amount_invested, current_price)
                    last_gain_alerted[token_name] = mult
            
            # Vérifier les PERTES (seulement si nouveau seuil franchi)
            for loss in LOSS_THRESHOLDS:
                if pnl_percent <= loss and loss < last_loss_alerted[token_name]:
                    print(f"   ⚠️ Seuil de perte {loss}% atteint!")
                    send_alert(token_name, "loss", loss, current_market_cap,
                              buy_market_cap, amount_invested, current_price)
                    last_loss_alerted[token_name] = loss
        
        print(f"\n⏳ Prochaine vérification dans {CHECK_INTERVAL // 60} minutes...")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        if not TOKENS:
            print("❌ Erreur: Aucun token configuré")
            exit(1)
        
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Script arrêté")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        raise