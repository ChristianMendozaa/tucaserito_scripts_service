import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request
from app.models.schemas import ScriptRequest, ScriptResponse, ScriptExtensionRequest
from app.services.claude_service import generate_video_scripts, generate_extension_scripts
from app.api.auth_deps import get_current_user_id
from app.core.rate_limit import limiter
import json
from typing import List

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate-scripts", response_model=ScriptResponse)
@limiter.limit("5/minute")
async def create_video_scripts(
    request: Request,
    data: str = Form(..., description="JSON string con product_name, product_description, technical_settings y preferences"),
    images: List[UploadFile] = File([], description="Lista de imágenes (opcional)"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Endpoint para generar guiones publicitarios utilizando Claude 3.5 Sonnet.
    Acepta 'multipart/form-data' con un campo 'data' (JSON) y múltiples archivos 'images'.
    Responde estrictamente con 3 opciones (AIDA, PAS, UGC).
    """
    try:
        if len(images) > 3:
            raise ValueError("No se permiten más de 3 imágenes por solicitud para generar guiones.")
            
        # Parse data JSON
        try:
            parsed_data = json.loads(data)
            request_data = ScriptRequest(**parsed_data)
        except json.JSONDecodeError:
            raise ValueError("El campo 'data' debe ser un JSON válido")
        except Exception as e:
            raise ValueError("Estructura JSON inválida")

        # Configurar límites de subida de archivos (MIME Types y Max 5MB)
        ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"]
        MAX_FILE_SIZE = 5 * 1024 * 1024 # 5 MB

        file_contents = []
        for img in images:
            if img.content_type not in ALLOWED_MIME_TYPES:
                raise ValueError(f"Tipo de archivo no permitido: {img.content_type}. Solo JPG/PNG/WEBP.")
            
            content = await img.read()
            if len(content) > MAX_FILE_SIZE:
                raise ValueError(f"La imagen excede el límite de 5MB: {img.filename}")
                
            file_contents.append({
                "content": content,
                "content_type": img.content_type or "image/jpeg"
            })

        result = generate_video_scripts(request_data, file_contents)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error generating scripts: {e}")
        raise HTTPException(status_code=500, detail="Error interno de comunicación con la IA.")

@router.post("/extend-scripts", response_model=ScriptResponse)
@limiter.limit("5/minute")
async def extend_video_scripts(
    request: Request,
    data: str = Form(..., description="JSON string con product_name, description, previous_script, technical_settings y preferences"),
    user_id: str = Depends(get_current_user_id)
):
    """
    Endpoint para generar extensiones lógicas de 7 segundos para guiones existentes.
    """
    try:
        try:
            parsed_data = json.loads(data)
            request_data = ScriptExtensionRequest(**parsed_data)
        except json.JSONDecodeError:
            raise ValueError("El campo 'data' debe ser un JSON válido")
        except Exception as e:
            raise ValueError("Estructura JSON inválida para la extensión")

        result = generate_extension_scripts(request_data)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error extending scripts: {e}")
        raise HTTPException(status_code=500, detail="Error interno de comunicación con la IA al extender guion.")
