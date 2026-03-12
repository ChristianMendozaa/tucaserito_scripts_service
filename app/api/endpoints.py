from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.models.schemas import ScriptRequest, ScriptResponse, ScriptExtensionRequest
from app.services.claude_service import generate_video_scripts, generate_extension_scripts
import json
from typing import List

router = APIRouter()

@router.post("/generate-scripts", response_model=ScriptResponse)
async def create_video_scripts(
    data: str = Form(..., description="JSON string con product_name, product_description, technical_settings y preferences"),
    images: List[UploadFile] = File([], description="Lista de imágenes (opcional)")
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
            raise ValueError(f"Estructura JSON inválida: {str(e)}")

        # Await file reading in service or read here. Reading here is safer.
        file_contents = []
        for img in images:
            content = await img.read()
            file_contents.append({
                "content": content,
                "content_type": img.content_type or "image/jpeg"
            })

        result = generate_video_scripts(request_data, file_contents)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/extend-scripts", response_model=ScriptResponse)
async def extend_video_scripts(
    data: str = Form(..., description="JSON string con product_name, description, previous_script, technical_settings y preferences"),
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
            raise ValueError(f"Estructura JSON inválida para la extensión: {str(e)}")

        result = generate_extension_scripts(request_data)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
