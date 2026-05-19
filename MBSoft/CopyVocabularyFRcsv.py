import os
import shutil

def aktualizuj_data():
    # 1. Definice cest
    # Pythonista ukládá lokální soubory v ~/Documents
    local_dir = os.path.expanduser('~/Documents/FrancouzstinaApp')
    
    # Cesta k iCloudu (Plocha/PythonMF)
    # POZOR: iCloud cesta může vyžadovat, aby byla složka v Pythonistě "otevřená" přes External Files
    icloud_base = os.path.expanduser('~/Documents/../Shared/AppGroup/com.apple.FileProvider.Storage/File Provider Storage/Desktop/PythonMF')
    
    soubory_k_aktualizaci = ['VocabularyFR.csv', 'VerbeFR.csv']
    
    print("🔄 Zahajuji synchronizaci z iCloud Drive...")
    
    for soubor in soubory_k_aktualizaci:
        src = os.path.join(icloud_base, soubor)
        dst = os.path.join(local_dir, soubor)
        
        try:
            if os.path.exists(src):
                shutil.copy2(src, dst)
                print(f"✅ Soubor {soubor} byl úspěšně aktualizován.")
            else:
                print(f"⚠️ Soubor {soubor} nebyl na iCloudu nalezen.")
        except Exception as e:
            print(f"❌ Chyba při kopírování {soubor}: {e}")

# Spuštění aktualizace před hlavním logikou aplikace
if __name__ == "__main__":
    aktualizuj_data()
    # Zde pokračuje tvůj původní kód AppFR.py
    print("🚀 Spouštím aplikaci...")
