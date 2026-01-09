#!/usr/bin/env python3
"""
Script de surveillance de token Solana avec alertes Telegram
Utilise l'API DexScreener pour vérifier le prix et envoie des alertes aux paliers x10, x20... x100
"""

import requests
import time
from typing import Optional, Dict

# ==================== CONFIGURATION ====================
# Liste des tokens à surveiller
# Chaque token est un dictionnaire avec :
#   - "name": Nom/symbole du token (pour les alertes)
#   - "address": Adresse du contrat Solana
#   - "buy_price": Votre prix d'achat en USD
#   - "amount_invested": Montant investi en USD
# Liste des tokens à surveiller
TOKENS = [
    {
        "name": "MMGA",
        "address": "87B6mb9KBjaF5NHrB3H33f7grdUHi4oWmMErjhZ5bonk",
        "buy_price": 0.000834,
        "amount_invested": 37.0
    },
    {
        "name": "Hungry",
        "address": "DkrrbsbxPaTt6Nt1nF1JvRmCLU4K6n3ZWVavvjvWpump",
        "buy_price": 0.0000255,
        "amount_invested": 2.964
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


def get_token_price(token_address: str) -> Optional[float]:
    """
    Récupère le prix actuel du token Solana via l'API DexScreener
    
    Args:
        token_address: Adresse du contrat Solana
        
    Returns:
        Prix actuel en USD ou None en cas d'erreur
    """
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # L'API retourne une liste de pairs, on prend la première (la plus liquide généralement)
        if data.get("pairs") and len(data["pairs"]) > 0:
            pair = data["pairs"][0]
            price_usd = pair.get("priceUsd")
            
            if price_usd:
                return float(price_usd)
        
        print(f"⚠️  Aucune paire trouvée pour le token {token_address}")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la récupération du prix: {e}")
        return None
    except (KeyError, ValueError, IndexError) as e:
        print(f"❌ Erreur lors du parsing des données: {e}")
        return None


def send_telegram_alert(token_name: str, multiplier: int, current_price: float, 
                       buy_price: float, amount_invested: float) -> bool:
    """
    Envoie une alerte Telegram avec les informations du gain
    
    Args:
        token_name: Nom/symbole du token
        multiplier: Le multiplicateur atteint (x10, x20, etc.)
        current_price: Prix actuel du token
        buy_price: Prix d'achat
        amount_invested: Montant investi en USD
        
    Returns:
        True si l'alerte a été envoyée avec succès, False sinon
    """
    try:
        # Calcul du PNL
        tokens_owned = amount_invested / buy_price
        current_value = tokens_owned * current_price
        pnl = current_value - amount_invested
        
        # Calcul du pourcentage de gain
        gain_percentage = ((current_price / buy_price) - 1) * 100
        
        # Formatage du message
        message = (
            f"🚀 **ALERTE TOKEN SOLANA**\n\n"
            f"🪙 **Token: {token_name}**\n\n"
            f"🎯 **Multiplicateur atteint: x{multiplier}**\n\n"
            f"💰 **PNL: ${pnl:,.2f}**\n"
            f"📈 **Gain: {gain_percentage:+.2f}%**\n\n"
            f"📊 Prix d'achat: ${buy_price:.8f}\n"
            f"📊 Prix actuel: ${current_price:.8f}\n"
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
    Fonction principale - Surveille le prix et envoie des alertes pour tous les tokens
    """
    print("=" * 60)
    print("🚀 Script de surveillance de tokens Solana")
    print("=" * 60)
    print(f"📊 Nombre de tokens surveillés: {len(TOKENS)}")
    print(f"⏱️  Vérification toutes les {CHECK_INTERVAL // 60} minutes")
    print(f"🎯 Paliers surveillés: {', '.join([f'x{m}' for m in MULTIPLIERS])}")
    print("=" * 60)
    print("\n📋 Tokens configurés:")
    for i, token in enumerate(TOKENS, 1):
        print(f"  {i}. {token['name']} - Prix d'achat: ${token['buy_price']:.8f} - Investi: ${token['amount_invested']:,.2f}")
    print("=" * 60)
    print()
    
    # Dictionnaire pour tracker les alertes déjà envoyées par token
    # Structure: {token_name: {multiplier: bool}}
    alerts_sent: Dict[str, Dict[int, bool]] = {
        token["name"]: {multiplier: False for multiplier in MULTIPLIERS}
        for token in TOKENS
    }
    
    iteration = 0
    
    while True:
        iteration += 1
        print(f"\n{'='*60}")
        print(f"[{iteration}] Vérification des prix...")
        print(f"{'='*60}")
        
        # Vérifier chaque token
        for token in TOKENS:
            token_name = token["name"]
            token_address = token["address"]
            buy_price = token["buy_price"]
            amount_invested = token["amount_invested"]
            
            print(f"\n🪙 Token: {token_name}")
            print(f"   📍 Adresse: {token_address[:8]}...{token_address[-8:]}")
            
            # Récupération du prix actuel
            current_price = get_token_price(token_address)
            
            if current_price is None:
                print(f"   ⚠️  Impossible de récupérer le prix")
                continue
            
            print(f"   💹 Prix actuel: ${current_price:.8f}")
            
            # Calcul du multiplicateur actuel
            current_multiplier = current_price / buy_price
            print(f"   📊 Multiplicateur actuel: x{current_multiplier:.2f}")
            
            # Vérification de chaque palier
            for multiplier in MULTIPLIERS:
                target_price = buy_price * multiplier
                
                # Si le prix a atteint ou dépassé le palier et qu'on n'a pas encore alerté
                if current_price >= target_price and not alerts_sent[token_name][multiplier]:
                    print(f"\n   🎉 Palier x{multiplier} atteint pour {token_name}!")
                    print(f"      Envoi de l'alerte Telegram...")
                    
                    if send_telegram_alert(token_name, multiplier, current_price, buy_price, amount_invested):
                        alerts_sent[token_name][multiplier] = True
                        print(f"      ✅ Alerte envoyée avec succès!")
                    else:
                        print(f"      ❌ Échec de l'envoi de l'alerte")
            
            # Afficher les paliers déjà atteints pour ce token
            reached = [m for m, sent in alerts_sent[token_name].items() if sent]
            if reached:
                print(f"   ✅ Paliers déjà alertés: {', '.join([f'x{m}' for m in reached])}")
        
        # Attendre avant la prochaine vérification
        print(f"\n{'='*60}")
        print(f"⏳ Prochaine vérification dans {CHECK_INTERVAL // 60} minutes...")
        print(f"{'='*60}")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        # Vérification de la configuration
        if not TOKENS:
            print("❌ Erreur: Aucun token configuré dans la liste TOKENS")
            print("   Veuillez ajouter au moins un token dans la configuration.")
            exit(1)
        
        # Vérification que tous les tokens ont les champs requis
        required_fields = ["name", "address", "buy_price", "amount_invested"]
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
