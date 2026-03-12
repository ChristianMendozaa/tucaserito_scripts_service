from pydantic import BaseModel, Field
from typing import List

class TechnicalSettings(BaseModel):
    aspect_ratio: str

class Preferences(BaseModel):
    video_style: str
    music_genre: str
    custom_theme: str

class ScriptRequest(BaseModel):
    product_name: str
    product_description: str
    technical_settings: TechnicalSettings
    preferences: Preferences

class Opcion(BaseModel):
    id: int
    nombre_estrategia: str
    texto_locucion: str
    prompt_veo_visual: str
    prompt_veo_audio: str

class ScriptResponse(BaseModel):
    opciones: List[Opcion]

class ScriptExtensionRequest(BaseModel):
    product_name: str
    product_description: str
    previous_script: Opcion
    technical_settings: TechnicalSettings
    preferences: Preferences
