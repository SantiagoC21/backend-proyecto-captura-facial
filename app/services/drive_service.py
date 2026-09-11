import os
import io
import json
import base64
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account
from dotenv import load_dotenv

load_dotenv()

SCOPES          = ["https://www.googleapis.com/auth/drive"]
DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")


def _get_drive_service():
    sa_json_b64 = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_BASE64")

    if not sa_json_b64:
        raise Exception(
            "Falta GOOGLE_SERVICE_ACCOUNT_JSON_BASE64. "
            "Genera la clave JSON de la cuenta de servicio y conviértela a base64."
        )

    sa_info = json.loads(base64.b64decode(sa_json_b64))
    creds = service_account.Credentials.from_service_account_info(sa_info, scopes=SCOPES)

    return build("drive", "v3", credentials=creds)


def _get_or_create_folder(service, nombre: str, parent_id: str) -> str:
    query = (
        f"name='{nombre}' and "
        f"mimeType='application/vnd.google-apps.folder' and "
        f"'{parent_id}' in parents and trashed=false"
    )
    results  = service.files().list(q=query, fields="files(id, name)").execute()
    archivos = results.get("files", [])

    if archivos:
        return archivos[0]["id"]

    metadata = {
        "name": nombre,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id]
    }
    folder = service.files().create(body=metadata, fields="id").execute()
    return folder["id"]


def _get_or_create_persona_folder(service, aula: str, carpeta_persona: str) -> str:
    """Crea/obtiene Aula/CarpetaPersona dentro de la raíz, en un solo lugar."""
    aula_folder_id = _get_or_create_folder(service, aula, DRIVE_FOLDER_ID)
    return _get_or_create_folder(service, carpeta_persona, aula_folder_id)


def subir_foto_drive(imagen_bytes: bytes, aula: str, carpeta_persona: str, filename: str) -> str:
    service   = _get_drive_service()
    folder_id = _get_or_create_persona_folder(service, aula, carpeta_persona)

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
    print(f"✅ Foto subida a Drive: {aula}/{carpeta_persona} — {link}")
    return link


def eliminar_carpeta_drive(aula: str, carpeta_persona: str):
    """Elimina la carpeta de la persona (dentro de su aula) en Drive y todo su contenido."""
    try:
        service = _get_drive_service()

        query_aula = (
            f"name='{aula}' and "
            f"mimeType='application/vnd.google-apps.folder' and "
            f"'{DRIVE_FOLDER_ID}' in parents and trashed=false"
        )
        aulas = service.files().list(q=query_aula, fields="files(id, name)").execute().get("files", [])

        if not aulas:
            print(f"⚠️ Carpeta de aula no encontrada en Drive: {aula}")
            return

        aula_folder_id = aulas[0]["id"]

        query_persona = (
            f"name='{carpeta_persona}' and "
            f"mimeType='application/vnd.google-apps.folder' and "
            f"'{aula_folder_id}' in parents and trashed=false"
        )
        archivos = service.files().list(q=query_persona, fields="files(id, name)").execute().get("files", [])

        if not archivos:
            print(f"⚠️ Carpeta no encontrada en Drive: {aula}/{carpeta_persona}")
            return

        for archivo in archivos:
            service.files().delete(fileId=archivo["id"]).execute()
            print(f"✅ Carpeta Drive eliminada: {aula}/{carpeta_persona}")

    except Exception as e:
        print(f"❌ Error eliminando carpeta Drive: {e}")