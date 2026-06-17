import os
import io
import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dotenv import load_dotenv

load_dotenv()

SCOPES          = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "./credentials.json")
DRIVE_FOLDER_ID  = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
TOKEN_PATH       = "./token.pickle"


def _get_drive_service():
    creds = None

    # Cargar token guardado
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)

    # Si no hay token o expiró, autenticar
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)

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