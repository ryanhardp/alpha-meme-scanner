import os
import requests
from supabase import create_client, Client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def get_and_score_coins():
    print("[*] Mencari data koin terbaru...")
    api_url = "https://api.dexscreener.com/latest/dex/search?q=solana"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code != 200:
            return []
        data = response.json()
        pairs = data.get('pairs', [])
    except Exception as e:
        return []

    scored_coins = []
    seen_addresses = set() # GUDANG PENYIMPANAN CA SEMENTARA (Anti-Duplikat)

    for pair in pairs:
        if pair.get('chainId') != 'solana':
            continue

        base = pair.get('baseToken', {})
        quote = pair.get('quoteToken', {})
        
        if base.get('symbol') in ['SOL', 'WSOL', 'USDC', 'USDT']:
            target_token = quote
        else:
            target_token = base
            
        token_name = target_token.get('name', '')
        if token_name.lower() == 'solana' or target_token.get('symbol') == 'SOL':
            continue

        ca = target_token.get('address', '')
        
        # LOGIKA ANTI-DUPLIKAT: Kalau CA udah ada di list, skip aja!
        if ca in seen_addresses:
            continue

        liquidity = pair.get('liquidity', {})
        if not isinstance(liquidity, dict):
            continue
        liquidity_usd = liquidity.get('usd', 0)
        fdv = pair.get('fdv', 0)
        
        if liquidity_usd >= 100 and fdv >= 100:
            score = (liquidity_usd / fdv) * 100 
            scored_coins.append({
                "name": token_name[:15],
                "symbol": target_token.get('symbol', 'UNKNOWN')[:8],
                "contract_address": ca,
                "score": round(score, 2),
                "chain": "solana"
            })
            # Masukin CA ke gudang catatan biar nggak kembar nanti
            seen_addresses.add(ca)

    scored_coins.sort(key=lambda x: x['score'], reverse=True)
    return scored_coins[:5]

def update_database(top_coins):
    if not top_coins:
        print("[-] Hasil screening kosong.")
        return
    try:
        supabase.table("top_coins").delete().gt("score", -1).execute()
        supabase.table("top_coins").insert(top_coins).execute()
        print("[+] SUKSES UPDATE KE SUPABASE! ANTI DUPLIKAT BERHASIL!")
    except Exception as e:
        print(f"[-] Error Supabase: {e}")

if __name__ == "__main__":
    top_5 = get_and_score_coins()
    update_database(top_5)