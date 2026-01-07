"""
Servicio para interactuar con Google Drive API.
Permite subir, eliminar y obtener información de archivos.
"""

import os
import io
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError


env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)


class GoogleDriveService:
    """
    Servicio para manejar operaciones con Google Drive.
    Usa una cuenta de servicio para autenticación.
    """
    
    SCOPES = ['https://www.googleapis.com/auth/drive']
    
    def __init__(self):
        self.credentials = None
        self.service = None
        self.folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        self._initialize_service()
    
    def _initialize_service(self):
        """
        Inicializa el servicio de Google Drive usando OAuth 2.0 con Refresh Token.
        Esto permite usar una cuenta personal (sin límite de Service Account).
        """
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request

        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        refresh_token = os.getenv('GOOGLE_REFRESH_TOKEN')

        if client_id and client_secret and refresh_token:
            try:
                # Crear credenciales usando el Refresh Token
                self.credentials = Credentials(
                    None,  # Access token (se generará automáticamente)
                    refresh_token=refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=client_id,
                    client_secret=client_secret,
                    scopes=self.SCOPES
                )
                
                # Construir el servicio
                self.service = build('drive', 'v3', credentials=self.credentials)
                
                # Forzar refresco, a veces ayuda a validar inicial
                # if self.credentials.expired:
                #     self.credentials.refresh(Request())

            except Exception as e:
                print(f"Error inicializando Google Drive (OAuth): {str(e)}")
        else:
            print("Faltan variables de entorno para Google Drive (CLIENT_ID, SECRET, REFRESH_TOKEN)")
    
    def is_configured(self) -> bool:
        """Verifica si el servicio está correctamente configurado."""
        return self.service is not None and self.folder_id is not None
    
    def upload_file(
        self,
        file_content: bytes,
        filename: str,
        mime_type: str,
        subfolder: Optional[str] = None
    ) -> dict:
        """
        Sube un archivo a Google Drive.
        
        Args:
            file_content: Contenido del archivo en bytes
            filename: Nombre del archivo
            mime_type: Tipo MIME del archivo (ej: 'application/pdf')
            subfolder: Subcarpeta opcional donde guardar (ej: 'planeaciones')
        
        Returns:
            dict con file_id, view_link, embed_link, download_link
        """
        if not self.is_configured():
            raise ValueError("Google Drive no está configurado correctamente")
        
        try:
            # Determinar carpeta destino
            parent_folder_id = self.folder_id
            
            if subfolder:
                # Buscar o crear subcarpeta
                parent_folder_id = self._get_or_create_folder(subfolder, self.folder_id)
            
            # Preparar metadata del archivo
            file_metadata = {
                'name': filename,
                'parents': [parent_folder_id]
            }
            
            # Preparar contenido
            media = MediaIoBaseUpload(
                io.BytesIO(file_content),
                mimetype=mime_type,
                resumable=True
            )
            
            # Subir archivo
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, webContentLink, size',
                supportsAllDrives=True,
            ).execute()
            
            file_id = file.get('id')
            
            # Intentar hacer el archivo público para lectura (necesario para embeds)
            # Si falla (ej: restricciones de dominio), continuamos igual
            try:
                self._make_public(file_id)
            except Exception as e:
                print(f"ADVERTENCIA: No se pudo hacer público el archivo {file_id}: {e}")
            
            return {
                'file_id': file_id,
                'filename': file.get('name'),
                'view_link': file.get('webViewLink'),
                'embed_link': f"https://drive.google.com/file/d/{file_id}/preview",
                'download_link': f"https://drive.google.com/uc?export=download&id={file_id}",
                'size_bytes': int(file.get('size', 0))
            }
            
        except HttpError as error:
            raise Exception(f"Error al subir archivo a Google Drive: {error}")
    
    def delete_file(self, file_id: str) -> bool:
        """
        Elimina un archivo de Google Drive.
        
        Args:
            file_id: ID del archivo en Google Drive
        
        Returns:
            True si se eliminó correctamente
        """
        if not self.is_configured():
            raise ValueError("Google Drive no está configurado correctamente")
        
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True
        except HttpError as error:
            if error.resp.status == 404:
                # El archivo ya no existe
                return True
            raise Exception(f"Error al eliminar archivo de Google Drive: {error}")
    
    def get_file_info(self, file_id: str) -> Optional[dict]:
        """
        Obtiene información de un archivo.
        
        Args:
            file_id: ID del archivo en Google Drive
        
        Returns:
            dict con información del archivo o None si no existe
        """
        if not self.is_configured():
            raise ValueError("Google Drive no está configurado correctamente")
        
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, createdTime, modifiedTime, webViewLink'
            ).execute()
            
            return {
                'file_id': file.get('id'),
                'filename': file.get('name'),
                'mime_type': file.get('mimeType'),
                'size_bytes': int(file.get('size', 0)),
                'created_at': file.get('createdTime'),
                'modified_at': file.get('modifiedTime'),
                'view_link': file.get('webViewLink')
            }
        except HttpError as error:
            if error.resp.status == 404:
                return None
            raise Exception(f"Error al obtener información del archivo: {error}")
    
    def _make_public(self, file_id: str):
        """Hace un archivo público para lectura."""
        try:
            self.service.permissions().create(
                fileId=file_id,
                body={
                    'type': 'anyone',
                    'role': 'reader'
                }
            ).execute()
        except HttpError:
            # Si falla, el archivo seguirá siendo privado pero funcional
            pass
    
    def _get_or_create_folder(self, folder_name: str, parent_id: str) -> str:
        """
        Busca una carpeta por nombre, o la crea si no existe.
        
        Returns:
            ID de la carpeta
        """
        # Buscar carpeta existente
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false"
        
        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        files = results.get('files', [])
        
        if files:
            return files[0]['id']
        
        # Crear carpeta
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }
        
        folder = self.service.files().create(
            body=folder_metadata,
            fields='id'
        ).execute()
        
        return folder['id']


# Instancia global del servicio
drive_service = GoogleDriveService()
