from google_auth_oauthlib.flow import InstalledAppFlow
import json
import os

# Scopes requeridos
SCOPES = ['https://www.googleapis.com/auth/drive']

def main():
    if not os.path.exists('client_secret.json'):
        print("❌ Error: No se encontró el archivo 'client_secret.json' en la raíz.")
        print("Por favor descarga el JSON de credenciales OAuth (App de escritorio) desde Google Cloud Console.")
        return

    # Iniciar flujo de autorización
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secret.json', SCOPES)
    
    print("Abriendo navegador para autenticación...")
    creds = flow.run_local_server(port=0)

    # Mostrar resultados
    print("\n✅ ¡Autenticación exitosa!\n")
    print("Guarda estos valores en tu archivo .env (y en las variables de Railway):")
    print("-" * 50)
    print(f"GOOGLE_CLIENT_ID={flow.client_config['client_id']}")
    print(f"GOOGLE_CLIENT_SECRET={flow.client_config['client_secret']}")
    print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")
    print("-" * 50)
    
    # También mostrar el access token por si acaso
    # print(f"Access Token (expira en 1h): {creds.token}")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Ocurrió un error: {e}")
