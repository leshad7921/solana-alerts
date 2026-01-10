#!/usr/bin/env python3
"""
Script de surveillance de token Solana avec alertes Telegram + Pushover
Utilise l'API DexScreener pour vérifier le market cap et envoie des alertes aux paliers x10, x20... x100
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
        "amount_invested": 35.4
    },
    {
        "name": "Hungry",
        "address": "DkrrbsbxPaTt6Nt1nF1JvRmCLU4K6n3ZWVavvjvWpump",
        "buy_market_cap": 23300,
        "amount_invested": 2.964
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
        "address": "EjNcJDRCASkxyPkiY6nbcGFqpu4frDE6qAupzaq1bonk",
        "buy_market_cap": 246000,
        "amount_invested": 15.48
    },
    {
        "name": "AMELIA",
        "address": "8TuHAfTBTMW1fJNq5bNoeX4zhk2492DNsCgVSYzApump",
        "buy_market_cap": 401000,
        "amount_invested": 7.00
    },
    {
        "name": "MAGIKARP",
        "address": "CYwajBHYQn9oPa9fJrhPuWziczSAbgg4mnssJZ6SBAGS",
        "buy_market_cap": 137000,
        "amount_invested": 4.3
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
MULTIPLIERS = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

# Seuils de perte à surveiller
LOSS_THRESHOLDS = [-0.10, -0.25]  # -10% et -25%
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
    priority: -2 (silent) to 2 (emergency)
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


def send_alert(token_name: str, alert_type: str, multiplier: float, current_market_cap: float,
               buy_market_cap: float, amount_invested: float, current_price: float) -> None:
    """
    Envoie une alerte via Telegram ET Pushover
    """
    # Calcul du PNL
    current_value = amount_invested * (current_market_cap / buy_market_cap)
    pnl = current_value - amount_invested
    gain_percentage = ((current_market_cap / buy_market_cap) - 1) * 100
    
    # Formatage du multiplicateur
    if abs(multiplier) >= 10:
        mult_display = f"x{int(multiplier)}"
    else:
        mult_display = f"x{multiplier:.2f}"
    
    # Emoji selon le type d'alerte
    if alert_type == "gain":
        emoji = "🚀"
        title = f"📈 {token_name} +{gain_percentage:.0f}%"
    else:
        emoji = "🔻"
        title = f"📉 {token_name} {gain_percentage:.0f}%"
    
    # Message Telegram (format Markdown)
    telegram_message = (
        f"{emoji} **ALERTE TOKEN SOLANA**\n\n"
        f"🪙 **Token: {token_name}**\n\n"
        f"🎯 **Multiplicateur: {mult_display}**\n\n"
        f"💰 **PNL: ${pnl:,.2f}**\n"
        f"📈 **Gain: {gain_percentage:+.2f}%**\n\n"
        f"📊 Market Cap achat: ${buy_market_cap:,.0f}\n"
        f"📊 Market Cap actuel: ${current_market_cap:,.0f}\n"
        f"💵 Prix actuel: ${current_price:.8f}\n"
        f"💵 Investissement: ${amount_invested:,.2f}\n"
        f"💵 Valeur actuelle: ${current_value:,.2f}"
    )
    
    # Message Pushover (format simple)
    pushover_message = (
        f"Multiplicateur: {mult_display}\n"
        f"PNL: ${pnl:,.2f} ({gain_percentage:+.1f}%)\n"
        f"MC: ${current_market_cap:,.0f}\n"
        f"Valeur: ${current_value:,.2f}"
    )
    
    # Priorité Pushover (1 = high pour les gains, 0 = normal pour les pertes)
    priority = 1 if alert_type == "gain" else 0
    
    # Envoi sur les deux canaux
    if send_telegram_alert(telegram_message):
        print(f"      ✅ Telegram OK")
    else:
        print(f"      ❌ Telegram FAIL")
    
    if send_pushover_alert(title, pushover_message, priority):
        print(f"      ✅ Pushover OK")
    else:
        print(f"      ❌ Pushover FAIL")


def main():
    """
    Fonction principale - Surveille le market cap et envoie des alertes
    """
    print("=" * 60)
    print("🚀 Script de surveillance de tokens Solana")
    print("   Alertes: Telegram + Pushover")
    print("=" * 60)
    print(f"📊 Nombre de tokens surveillés: {len(TOKENS)}")
    print(f"⏱️  Vérification toutes les {CHECK_INTERVAL // 60} minutes")
    print(f"📈 Paliers de gain: {', '.join([f'x{m}' if m >= 10 else f'x{m:.2f}' for m in MULTIPLIERS])}")
    print(f"📉 Seuils de perte: {', '.join([f'{int(l*100)}%' for l in LOSS_THRESHOLDS])}")
    print("=" * 60)
    print("\n📋 Tokens configurés:")
    for i, token in enumerate(TOKENS, 1):
        print(f"  {i}. {token['name']} - MC achat: ${token['buy_market_cap']:,.0f} - Investi: ${token['amount_invested']:,.2f}")
    print("=" * 60)
    print()
    
    # Dictionnaire pour tracker les alertes déjà envoyées
    alerts_sent: Dict[str, Dict[str, bool]] = {
        token["name"]: {
            **{f"gain_{m}": False for m in MULTIPLIERS},
            **{f"loss_{l}": False for l in LOSS_THRESHOLDS}
        }
        for token in TOKENS
    }
    
    iteration = 0
    
    while True:
        iteration += 1
        print(f"\n{'='*60}")
        print(f"[{iteration}] Vérification des market caps...")
        print(f"{'='*60}")
        
        for token in TOKENS:
            token_name = token["name"]
            token_address = token["address"]
            buy_market_cap = token["buy_market_cap"]
            amount_invested = token["amount_invested"]
            
            print(f"\n🪙 Token: {token_name}")
            print(f"   📍 Adresse: {token_address[:8]}...{token_address[-8:]}")
            
            token_data = get_token_data(token_address)
            
            if token_data is None:
                print(f"   ⚠️  Impossible de récupérer les données")
                continue
            
            current_price, current_market_cap = token_data
            
            print(f"   💹 Prix actuel: ${current_price:.8f}")
            print(f"   📊 Market Cap actuel: ${current_market_cap:,.0f}")
            
            # Calcul du multiplicateur
            current_multiplier = current_market_cap / buy_market_cap
            print(f"   📈 Multiplicateur actuel: x{current_multiplier:.2f}")
            
            # Calcul du PNL
            current_value = amount_invested * current_multiplier
            current_pnl = current_value - amount_invested
            pnl_percent = (current_multiplier - 1) * 100
            print(f"   💰 PNL actuel: ${current_pnl:,.2f} ({pnl_percent:+.2f}%)")
            
            # Vérification des paliers de GAIN
            for multiplier in MULTIPLIERS:
                alert_key = f"gain_{multiplier}"
                target_market_cap = buy_market_cap * multiplier
                
                if current_market_cap >= target_market_cap and not alerts_sent[token_name][alert_key]:
                    mult_display = f"x{int(multiplier)}" if multiplier >= 10 else f"x{multiplier:.2f}"
                    print(f"\n   🎉 Palier {mult_display} atteint pour {token_name}!")
                    print(f"      Envoi des alertes...")
                    
                    send_alert(token_name, "gain", multiplier, current_market_cap,
                              buy_market_cap, amount_invested, current_price)
                    alerts_sent[token_name][alert_key] = True
            
            # Vérification des seuils de PERTE
            for loss_threshold in LOSS_THRESHOLDS:
                alert_key = f"loss_{loss_threshold}"
                # Si on est en dessous du seuil de perte
                if pnl_percent / 100 <= loss_threshold and not alerts_sent[token_name][alert_key]:
                    print(f"\n   ⚠️ Seuil de perte {int(loss_threshold*100)}% atteint pour {token_name}!")
                    print(f"      Envoi des alertes...")
                    
                    send_alert(token_name, "loss", current_multiplier, current_market_cap,
                              buy_market_cap, amount_invested, current_price)
                    alerts_sent[token_name][alert_key] = True
            
            # Afficher les alertes déjà envoyées
            gains_reached = [k.replace("gain_", "x") for k, v in alerts_sent[token_name].items() if v and k.startswith("gain_")]
            losses_reached = [k.replace("loss_", "") for k, v in alerts_sent[token_name].items() if v and k.startswith("loss_")]
            if gains_reached:
                print(f"   ✅ Gains alertés: {', '.join(gains_reached)}")
            if losses_reached:
                print(f"   🔻 Pertes alertées: {', '.join(losses_reached)}")
        
        print(f"\n{'='*60}")
        print(f"⏳ Prochaine vérification dans {CHECK_INTERVAL // 60} minutes...")
        print(f"{'='*60}")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        if not TOKENS:
            print("❌ Erreur: Aucun token configuré")
            exit(1)
        
        required_fields = ["name", "address", "buy_market_cap", "amount_invested"]
        for i, token in enumerate(TOKENS, 1):
            for field in required_fields:
                if field not in token:
                    print(f"❌ Erreur: Token #{i} manque le champ '{field}'")
                    exit(1)
        
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrompu par l'utilisateur")
        print("👋 Au revoir!")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        raise