import os
import io
import json
import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dotenv import load_dotenv

load_dotenv()

SCOPES           = ["https://www.googleapis.com/auth/drive"]
DRIVE_FOLDER_ID  = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "./credentials.json")
TOKEN_PATH       = "./token.pickle"


def _get_drive_service():
    creds = None
    token_b64 = os.getenv("GOOGLE_TOKEN_BASE64")

    # Cargar token desde variable de entorno (Railway)
    if token_b64:
        import base64
        token_bytes = base64.b64decode(token_b64)
        creds = pickle.loads(token_bytes)

    # Cargar token desde archivo (local)
    elif os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)

    # Refrescar si expiró
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

        # Actualizar token guardado
        if not token_b64:
            with open(TOKEN_PATH, "wb") as token:
                pickle.dump(creds, token)

    if not creds:
        raise Exception("No hay token de autenticación. Genera token.pickle localmente primero.")

    return build("drive", "v3", credentials=creds)


def _get_or_create_folder(service, nombre: str, parent_id: str) -> str:
    query = (
        f"name='{nombre}' and "
        f"mimeType='application/vnd.google-apps.folder' and "
        f"'{parent_id}' in parents and trashed=false"
    )
    results = service.files().list(
        q=query,
        fields="files(id, name)"
    ).execute()
    archivos = results.get("files", [])

    if archivos:
        return archivos[0]["id"]

    metadata = {
        "name": nombre,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id]
    }
    folder = service.files().create(
        body=metadata,
        fields="id"
    ).execute()
    return folder["id"]


def subir_foto_drive(imagen_bytes: bytes, nombre_persona: str, filename: str) -> str:
    service   = _get_drive_service()
    folder_id = _get_or_create_folder(service, nombre_persona, DRIVE_FOLDER_ID)

    media = MediaIoBaseUpload(
        io.BytesIO(imagen_bytes),
        mimetype="image/jpeg",
        resumable=False
    )

    metadata = {
        "name": filename,
        "parents": [folder_id]
    }

    archivo = service.files().create(
        body=metadata,
        media_body=media,
        fields="id"
    ).execute()

    link = f"https://drive.google.com/file/d/{archivo['id']}/view"
    print(f"✅ Foto subida a Drive: {link}")
    return link