import os
import requests
from supabase import create_client, Client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def get_and_score_coins():
    print("[*] Mencari data koin terbaru...")
    
    # 1. Ganti kata kunci! Kita nyari koin micin (misal keyword 'pump' yang lagi meta)
    api_url = "https://api.dexscreener.com/latest/dex/search?q=pump"
    
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
    for pair in pairs:
        # 2. Pastikan cuma ngambil yang di jaringan Solana
        if pair.get('chainId') != 'solana':
            continue

        base_token = pair.get('baseToken', {})
        quote_token = pair.get('quoteToken', {})
        
        # 3. Logika Pintar: Ambil koin yang BUKAN koin utama (SOL/USDC)
        if base_token.get('symbol') in ['SOL', 'WSOL', 'USDC', 'USDT']:
            target_token = quote_token
        else:
            target_token = base_token
            
        # 4. Anti-Scam: Buang kalau namanya masih 'Solana' murni
        if target_token.get('name') == 'Solana' or target_token.get('symbol') == 'SOL':
            continue

        liquidity = pair.get('liquidity', {})
        if not isinstance(liquidity, dict):
            continue
        liquidity_usd = liquidity.get('usd', 0)
        fdv = pair.get('fdv', 0)
        
        # Filter pengetesan
        if liquidity_usd >= 1000 and fdv >= 1000:
            score = (liquidity_usd / fdv) * 100 
            scored_coins.append({
                "name": target_token.get('name', 'Unknown'),
                "symbol": target_token.get('symbol', 'UNKNOWN'),
                "contract_address": target_token.get('address', ''),
                "score": round(score, 2),
                "chain": "solana"
            })

    scored_coins.sort(key=lambda x: x['score'], reverse=True)
    return scored_coins[:5]

def update_database(top_coins):
    if not top_coins:
        print("[-] Hasil screening kosong.")
        return
    try:
        supabase.table("top_coins").delete().gt("score", -1).execute()
        supabase.table("top_coins").insert(top_coins).execute()
        print("[+] SUKSES UPDATE KE SUPABASE!")
    except Exception as e:
        print(f"[-] Error Supabase: {e}")

if __name__ == "__main__":
    top_5 = get_and_score_coins()
    update_database(top_5)