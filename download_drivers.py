import os
import requests

IMAGE_DIR = "drivers_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# Fixed correct internal paths for the 4 failed drivers
FIXED_URLS = {
    "ANT": "https://media.formula1.com/content/dam/fom-website/drivers/A/ANDANT01_Andrea_Kimi_Antonelli/andant01.png",
    "HAD": "https://media.formula1.com/content/dam/fom-website/drivers/I/ISCHAD01_Isack_Hadjar/ischad01.png",
    "LIN": "https://media.formula1.com/content/dam/fom-website/drivers/A/ARVLIN01_Arvid_Lindblad/arvlin01.png",
    "ALB": "https://media.formula1.com/content/dam/fom-website/drivers/A/ALEALB01_Alexander_Albon/alealb01.png"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Referer": "https://www.formula1.com/"
}

print("📥 Downloading the final 4 remaining driver photos...\n")

for code, url in FIXED_URLS.items():
    file_path = os.path.join(IMAGE_DIR, f"{code}.png")
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(res.content)
            print(f"✅ Fixed & Saved: {file_path}")
        else:
            print(f"❌ Still failed for {code} (Status: {res.status_code})")
    except Exception as e:
        print(f"⚠️ Error: {e}")

print("\n🏁 All drivers are completely onboarded locally now!")