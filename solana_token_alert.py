#!/usr/bin/env python3
"""
Script de surveillance de token Solana avec alertes Telegram
Utilise l'API DexScreener pour vérifier le market cap et envoie des alertes aux paliers x10, x20... x100
"""

import requests
import time
from typing import Optional, Dict, Tuple

# ==================== CONFIGURATION ====================
# Liste des tokens à surveiller
# Chaque token est un dictionnaire avec :
#   - "name": Nom/symbole du token (pour les alertes)
#   - "address": Adresse du contrat Solana
#   - "buy_market_cap": Market cap en $ au moment de l'achat
#   - "amount_invested": Montant investi en USD
TOKENS = [
    {
        "name": "MMGA",
        "address": "87B6mb9KBjaF5NHrB3H33f7grdUHi4oWmMErjhZ5bonk",
        "buy_market_cap": 643000,
        "amount_invested": 37.0
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
]

# Configuration Telegram
TELEGRAM_TOKEN = "8554678342:AAHmD1OB3OHwgkFwisqlUv2y5VC7HTwlOnI"
TELEGRAM_CHAT_ID = "1764001989"

# Intervalle de vérification en secondes (5 minutes = 300 secondes)
CHECK_INTERVAL = 300

# Multiplicateurs à surveiller
MULTIPLIERS = [1.05, 1.1, 1.5, 2, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
# =======================================================


def get_token_data(token_address: str) -> Optional[Tuple[float, float]]:
    """
    Récupère le prix et market cap actuels du token Solana via l'API DexScreener
    
    Args:
        token_address: Adresse du contrat Solana
        
    Returns:
        Tuple (prix_usd, market_cap) ou None en cas d'erreur
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


def send_telegram_alert(token_name: str, multiplier: float, current_market_cap: float,
                       buy_market_cap: float, amount_invested: float, current_price: float) -> bool:
    """
    Envoie une alerte Telegram avec les informations du gain
    """
    try:
        # Calcul du PNL basé sur le multiplicateur du market cap
        current_value = amount_invested * multiplier
        pnl = current_value - amount_invested
        gain_percentage = (multiplier - 1) * 100
        
        # Formatage du multiplicateur
        if multiplier >= 10:
            mult_display = f"x{int(multiplier)}"
        else:
            mult_display = f"x{multiplier:.2f}"
        
        # Formatage du message
        message = (
            f"🚀 **ALERTE TOKEN SOLANA**\n\n"
            f"🪙 **Token: {token_name}**\n\n"
            f"🎯 **Multiplicateur atteint: {mult_display}**\n\n"
            f"💰 **PNL: ${pnl:,.2f}**\n"
            f"📈 **Gain: {gain_percentage:+.2f}%**\n\n"
            f"📊 Market Cap achat: ${buy_market_cap:,.0f}\n"
            f"📊 Market Cap actuel: ${current_market_cap:,.0f}\n"
            f"💵 Prix actuel: ${current_price:.8f}\n"
            f"💵 Investissement initial: ${amount_invested:,.2f}\n"
            f"💵 Valeur actuelle: ${current_value:,.2f}"
        )
        
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
        print(f"❌ Erreur lors de l'envoi de l'alerte Telegram: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue lors de l'envoi de l'alerte: {e}")
        return False


def main():
    """
    Fonction principale - Surveille le market cap et envoie des alertes pour tous les tokens
    """
    print("=" * 60)
    print("🚀 Script de surveillance de tokens Solana (Market Cap)")
    print("=" * 60)
    print(f"📊 Nombre de tokens surveillés: {len(TOKENS)}")
    print(f"⏱️  Vérification toutes les {CHECK_INTERVAL // 60} minutes")
    print(f"🎯 Paliers surveillés: {', '.join([f'x{m}' if m >= 10 else f'x{m:.2f}' for m in MULTIPLIERS])}")
    print("=" * 60)
    print("\n📋 Tokens configurés:")
    for i, token in enumerate(TOKENS, 1):
        print(f"  {i}. {token['name']} - MC achat: ${token['buy_market_cap']:,.0f} - Investi: ${token['amount_invested']:,.2f}")
    print("=" * 60)
    print()
    
    # Dictionnaire pour tracker les alertes déjà envoyées par token
    alerts_sent: Dict[str, Dict[float, bool]] = {
        token["name"]: {multiplier: False for multiplier in MULTIPLIERS}
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
            
            # Calcul du multiplicateur basé sur le market cap
            current_multiplier = current_market_cap / buy_market_cap
            print(f"   📈 Multiplicateur actuel: x{current_multiplier:.2f}")
            
            # Calcul du PNL actuel
            current_value = amount_invested * current_multiplier
            current_pnl = current_value - amount_invested
            pnl_percent = (current_multiplier - 1) * 100
            print(f"   💰 PNL actuel: ${current_pnl:,.2f} ({pnl_percent:+.2f}%)")
            
            # Vérification de chaque palier
            for multiplier in MULTIPLIERS:
                target_market_cap = buy_market_cap * multiplier
                
                if current_market_cap >= target_market_cap and not alerts_sent[token_name][multiplier]:
                    mult_display = f"x{int(multiplier)}" if multiplier >= 10 else f"x{multiplier:.2f}"
                    print(f"\n   🎉 Palier {mult_display} atteint pour {token_name}!")
                    print(f"      Envoi de l'alerte Telegram...")
                    
                    if send_telegram_alert(token_name, multiplier, current_market_cap, 
                                          buy_market_cap, amount_invested, current_price):
                        alerts_sent[token_name][multiplier] = True
                        print(f"      ✅ Alerte envoyée avec succès!")
                    else:
                        print(f"      ❌ Échec de l'envoi de l'alerte")
            
            # Afficher les paliers déjà atteints
            reached = [m for m, sent in alerts_sent[token_name].items() if sent]
            if reached:
                reached_display = [f"x{int(m)}" if m >= 10 else f"x{m:.2f}" for m in reached]
                print(f"   ✅ Paliers déjà alertés: {', '.join(reached_display)}")
        
        print(f"\n{'='*60}")
        print(f"⏳ Prochaine vérification dans {CHECK_INTERVAL // 60} minutes...")
        print(f"{'='*60}")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        if not TOKENS:
            print("❌ Erreur: Aucun token configuré dans la liste TOKENS")
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