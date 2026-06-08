import os
import msal
import requests
from dotenv import load_dotenv

# Wczytujemy zmienne z .env w katalogu projektu
load_dotenv()

CLIENT_ID = os.getenv('MS_CLIENT_ID')
TENANT_ID = os.getenv('MS_TENANT_ID', 'common')
# Używamy konkretnego tenantu lub 'common', jeśli to aplikacja multi-tenant
AUTHORITY = f'https://login.microsoftonline.com/{TENANT_ID}'
SCOPES = ['Tasks.Read', 'User.Read']

# Plik na token cache zapisujemy w tym samym folderze (lub można do AppData)
CACHE_FILE = 'token_cache.bin'

class PlannerSync:
    def __init__(self):
        self.cache = msal.SerializableTokenCache()
        if os.path.exists(CACHE_FILE):
            self.cache.deserialize(open(CACHE_FILE, 'r').read())

        self.app = msal.PublicClientApplication(
            CLIENT_ID, authority=AUTHORITY,
            token_cache=self.cache
        )

    def get_token(self):
        if not CLIENT_ID:
            raise ValueError("Brak Client ID (MS_CLIENT_ID) w zmiennych środowiskowych (.env).")

        # 1. Próba uzyskania tokenu z cache (Silent Flow)
        accounts = self.app.get_accounts()
        result = None
        if accounts:
            result = self.app.acquire_token_silent(SCOPES, account=accounts[0])

        if not result:
            # 2. Interactive Flow: Otwiera okno przeglądarki
            # Uwaga: w aplikacji okienkowej wywołanie tego zatrzyma wątek na wpisanie danych
            result = self.app.acquire_token_interactive(scopes=SCOPES)
            if "access_token" in result:
                # Zapisujemy nowy cache na dysku
                open(CACHE_FILE, 'w').write(self.cache.serialize())

        if result and "access_token" in result:
            return result["access_token"]
        else:
            err_msg = result.get("error_description", "Nieznany błąd autoryzacji") if result else "Brak odpowiedzi od Microsoft."
            raise Exception(f"Nie udało się zalogować do konta Microsoft:\n{err_msg}")

    def get_my_planner_tasks(self):
        """Pobiera wszystkie zadania przypisane do zalogowanego użytkownika w Plannerze"""
        token = self.get_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Endpoint na pobranie zadań przypisanych do mnie
        response = requests.get('https://graph.microsoft.com/v1.0/me/planner/tasks', headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('value', [])
        else:
            raise Exception(f"Błąd pobierania zadań z Graph API: {response.status_code}\n{response.text}")
