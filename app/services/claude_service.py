import json
import logging
import anthropic
from app.core.config import settings
from app.models.schemas import ScriptRequest, ScriptResponse, ScriptExtensionRequest

logger = logging.getLogger(__name__)

# Precios por millón de tokens (en USD) para Claude Haiku 4.5
COSTO_INPUT_BASE_PER_1M = 1.00
COSTO_CACHE_WRITE_PER_1M = 1.25  # Usando 5m Cache Writes
COSTO_CACHE_HIT_PER_1M = 0.10
COSTO_OUTPUT_PER_1M = 5.00

def calcular_costo(usage) -> float:
    # Extraer tokens del objeto usage de Anthropic
    input_tokens = getattr(usage, "input_tokens", 0)
    output_tokens = getattr(usage, "output_tokens", 0)
    cache_creation_tokens = getattr(usage, "cache_creation_input_tokens", 0)
    cache_read_tokens = getattr(usage, "cache_read_input_tokens", 0)
    
    # Calcular costo
    base_input_cost = (input_tokens / 1_000_000) * COSTO_INPUT_BASE_PER_1M
    cache_write_cost = (cache_creation_tokens / 1_000_000) * COSTO_CACHE_WRITE_PER_1M
    cache_hit_cost = (cache_read_tokens / 1_000_000) * COSTO_CACHE_HIT_PER_1M
    output_cost = (output_tokens / 1_000_000) * COSTO_OUTPUT_PER_1M
    
    total_cost = base_input_cost + cache_write_cost + cache_hit_cost + output_cost
    
    print("\n" + "="*50)
    print("📊 REPORTE DE USO Y COSTOS DE API (CLAUDE)")
    print("="*50)
    print(f"🔹 Tokens Input Base:     {input_tokens:<6} tokens   (${base_input_cost:.6f})")
    print(f"🔹 Tokens Cache Writes:   {cache_creation_tokens:<6} tokens   (${cache_write_cost:.6f})")
    print(f"🔹 Tokens Cache Hits:     {cache_read_tokens:<6} tokens   (${cache_hit_cost:.6f})")
    print(f"🔹 Tokens Output:         {output_tokens:<6} tokens   (${output_cost:.6f})")
    print("-" * 50)
    print(f"💰 COSTO TOTAL ESTIMADO:   ${total_cost:.6f} USD")
    print("="*50 + "\n")
    
    return total_cost

import base64

def generate_video_scripts(request_data: ScriptRequest, file_contents: list) -> ScriptResponse:
    # Inicializar cliente de Anthropic
    client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY, timeout=15.0)
    
    # Construir system prompt
    system_prompt = '''Eres un Director de Marketing experto para el mercado boliviano.
 Tu tarea es generar un JSON estricto con exactamente 3 opciones de guiones de video publicitarios usando las estrategias AIDA, PAS y UGC.
DEBES evitar obligatoriamente cualquier tema de copyright; si el producto o las preferencias piden algo sobre marcas registradas, personajes famosos o elementos con derechos de autor, tradúcelo inteligentemente a una "estética genérica".

CRÍTICO - RESTRICCIÓN FÍSICA DE TIEMPO (8 SEGUNDOS MAX):
El video generado durará EXACTAMENTE y MÁXIMO 8 SEGUNDOS.
Tu `texto_locucion` DEBE durar 8 segundos al hablarse (aproximadamente de 15 a un MÁXIMO ABSOLUTO de 20 palabras). Si superas las 20 palabras, el audio se cortará abruptamente. Sé conciso y al grano. El `prompt_veo_visual` debe representar una sola toma unificada fluida que no dure más de 8s.

INSTRUCCIONES PARA EL JSON DE SALIDA:
Debes regresar OBLIGATORIAMENTE un JSON que cumpla estrictamente con esta estructura (y NADA MAS, sin código markdown si es posible, o asegúrate de que sea parseable):
{
  "opciones": [
    {
      "id": 1,
      "nombre_estrategia": "AIDA",
      "texto_locucion": "...",
      "prompt_veo_visual": "...",
      "prompt_veo_audio": "..."
    },
    ...
  ]
}

Reglas por campo:
- `texto_locucion`: Usa jerga boliviana natural y persuasiva acorde al producto (ej: "caserito"). PROHIBIDO usar modismos peruanos como "pe", "causa" o "chamba". Si el usuario menciona "bs", "Bs" o "bs.", significa OBLIGATORIAMENTE la moneda "bolivianos", escríbelo para que suene fluido (Ej: "a sólo 20 bolivianos"). ¡MÁXIMO 20 PALABRAS! Si pasas de 20, fracasaremos.
- `prompt_veo_visual`: Instrucción EN INGLÉS detallando la cámara, cinematografía y acción visual para un modelo generador de video (para 8 segundos de toma). ADEMÁS, agrega explícitamente y en mayúsculas la regla: "DO NOT GENERATE ANY WRITTEN TEXT, NO WORDS, NO LETTERS". Es crucial que no aparezca texto flotante en el video.
- `prompt_veo_audio`: Instrucción EN INGLÉS describiendo el género musical y diseño sonoro, pero INCLUYENDO explícitamente el diálogo completo en español.
'''

    content = []
    
    # Agregar las imágenes PRIMERO para mejor rendimiento de visión de Claude
    for file_obj in file_contents:
        media_type = file_obj.get("content_type", "image/jpeg")
        data_bytes = file_obj.get("content", b"")
        b64_encoded = base64.b64encode(data_bytes).decode("utf-8")
        
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": b64_encoded
            }
        })
    
    # Agregar el texto DESPUÉS de las imágenes
    text_prompt = f"""
Producto: {request_data.product_name}
Descripción: {request_data.product_description}
Aspect Ratio: {request_data.technical_settings.aspect_ratio}

Preferencias (si dice "auto", decide por tu cuenta qué sería mejor):
- Estilo de video: {request_data.preferences.video_style}
- Género musical: {request_data.preferences.music_genre}
- Tema personalizado: {request_data.preferences.custom_theme}
"""
    content.append({"type": "text", "text": text_prompt})

    # Llamar a Claude
    # Se usa la versión más reciente de Claude 3.5 Sonnet
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        temperature=0.7,
        system=system_prompt,
        messages=[
            {"role": "user", "content": content}
        ]
    )
    
    response_text = response.content[0].text
    
    # Mostrar el costo en terminal
    calcular_costo(response.usage)
    
    # Parsear JSON
    # Remover posibles tags de markdown si Claude los provee
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].strip()
         
    try:
        data = json.loads(response_text)
        return ScriptResponse(**data)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing Claude response JSON: {e}")
        logger.error(f"Raw response (truncated): {response_text[:200]}...")
        raise ValueError("El modelo Claude no devolvió un JSON válido.")

def generate_extension_scripts(request_data: ScriptExtensionRequest) -> ScriptResponse:
    client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY, timeout=15.0)
    
    system_prompt = '''Eres un Director de Marketing experto para el mercado boliviano.
Tu cliente ha generado un video inicial exitoso y ha solicitado una "EXTENSIÓN" de dicho video.
A diferencia del video inicial que duró 8 segundos, el modelo generador (Veo) tiene un límite rígido de EXACTAMENTE 7 SEGUNDOS físicos para el video de continuación.

CRÍTICO - RESTRICCIÓN DE TIEMPO EXTENSIÓN (7 SEGUNDOS):
Tu tarea es generar un JSON con 3 opciones de guiones que continúen coherentemente la historia/acción del video anterior aportando un Cierre y Call to Action (CTA).
Tu nuevo `texto_locucion` DEBE durar 7 segundos al hablarse (MÁXIMO ABSOLUTO 17 palabras). Si superas las 17 palabras, romperemos el audio final.
El `prompt_veo_visual` debe dictar lógicamente QUÉ PASA A CONTINUACIÓN considerando que el video previo ya conectó a la audiencia. Debe fluir como un corte o paneo natural desde lo acontecido.

INSTRUCCIONES PARA EL JSON DE SALIDA:
{
  "opciones": [
    {
      "id": 1,
      "nombre_estrategia": "OPCION 1 (Oferta Agresiva)",
      "texto_locucion": "...",
      "prompt_veo_visual": "...",
      "prompt_veo_audio": "..."
    },
    ...
  ]
}

Reglas por campo:
- `texto_locucion`: Recuerda interpretar "bs" siempre como "bolivianos".
- `prompt_veo_visual`: Instrucción EN INGLÉS de cómo continúa la toma anterior (los siguientes 7 segundos). ADEMÁS, agrega explícitamente y en mayúsculas la regla: "DO NOT GENERATE ANY WRITTEN TEXT, NO WORDS, NO LETTERS". Es crucial que no aparezca texto flotante en el video.
- `prompt_veo_audio`: Instrucción EN INGLÉS describiendo el género musical y diseño sonoro, pero INCLUYENDO explícitamente el diálogo completo en español.
'''

    text_prompt = f"""
== CONTEXTO DEL PRODUCTO Y VIDEO ANTERIOR ==
Producto: {request_data.product_name}
Descripción: {request_data.product_description}
Aspect Ratio: {request_data.technical_settings.aspect_ratio}

Guion Visual Original (Lo que ya pasó los primeros 8 segundos):
{request_data.previous_script.prompt_veo_visual}
Locución Original Escuchada:
{request_data.previous_script.texto_locucion}
Audio/Música Original:
{request_data.previous_script.prompt_veo_audio}

Preferencias del Cliente:
- Estilo: {request_data.preferences.video_style}
- Música: {request_data.preferences.music_genre}
- Tema Custom: {request_data.preferences.custom_theme}

== TAREA ==
Genera las 3 opciones (formato JSON) que continúan esta misma historia durante los siguientes 7 SEGUNDOS estrictos. ¡Dame opciones muy creativas para el Hook secundario o el Checkout (CTA)!
"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        temperature=0.7,
        system=system_prompt,
        messages=[
            {"role": "user", "content": text_prompt}
        ]
    )
    
    response_text = response.content[0].text
    calcular_costo(response.usage)
    
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].strip()
         
    try:
        data = json.loads(response_text)
        return ScriptResponse(**data)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing Claude extension response JSON: {e}")
        logger.error(f"Raw response (truncated): {response_text[:200]}...")
        raise ValueError("El modelo Claude no devolvió un JSON válido.")

