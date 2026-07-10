import os
import requests
from supabase import create_client, Client

# Mengambil kunci dari brankas rahasia yang udah lu isi di GitHub
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def get_and_score_coins():
    print("[*] Mencari data koin terbaru di DexScreener...")
    api_url = "https://api.dexscreener.com/latest/dex/search?q=solana"
    try:
        response = requests.get(api_url).json()
        pairs = response.get('pairs', [])
    except Exception as e:
        print(f"[-] Gagal narik data: {e}")
        return []

    scored_coins = []
    for pair in pairs:
        liquidity = pair.get('liquidity', {}).get('usd', 0)
        fdv = pair.get('fdv', 0)
        
        # FILTER BARU: Diubah jadi lebih longgar biar koinnya pasti dapet buat ngetes web
        if liquidity >= 1000 and fdv >= 1000:
            score = (liquidity / fdv) * 100 
            scored_coins.append({
                "name": pair['baseToken']['name'],
                "symbol": pair['baseToken']['symbol'],
                "contract_address": pair['baseToken']['address'],
                "score": round(score, 2),
                "chain": "solana"
            })

    # Urutkan dari skor tertinggi, ambil 5 terbaik
    scored_coins.sort(key=lambda x: x['score'], reverse=True)
    return scored_coins[:5]

def update_database(top_coins):
    if not top_coins:
        print("[-] Tidak ada koin yang lolos filter.")
        return
    # Hapus data lama, masukkan 5 data koin paling baru
    supabase.table("top_coins").delete().gt("score", -1).execute()
    supabase.table("top_coins").insert(top_coins).execute()
    print("[+] Sukses update koin ke Supabase!")

if __name__ == "__main__":
    top_5 = get_and_score_coins()
    update_database(top_5)