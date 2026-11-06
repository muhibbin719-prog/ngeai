import os
from dotenv import load_dotenv
from google import genai

# Muat API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("Mencari daftar model yang tersedia untuk Anda...\n")

# Menampilkan semua model yang mendukung function calling (generateContent)
for model in client.models.list():
    if "generateContent" in model.supported_actions:
        # Menghapus kata 'models/' di depan agar tinggal nama aslinya saja
        nama_bersih = model.name.replace("models/", "")
        print(f'- "{nama_bersih}"')