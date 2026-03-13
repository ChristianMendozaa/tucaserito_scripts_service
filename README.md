# Script Service API

Este microservicio se encarga de generar y extender guiones publicitarios utilizando la inteligencia artificial de Anthropic (Claude 3.5 Sonnet), adaptados específicamente para las restricciones de Google Vertex AI Veo 3.1.

## Restricciones Core (Veo 3.1)
El generador está programado matemáticamente para devolver guiones con locuciones limitadas a:
- **Video Base:** Exactamente 8 segundos (Max ~20 palabras).
- **Video Extensión:** Exactamente 7 segundos (Max ~17 palabras).

---

## 1. Generar Guiones Base

Genera 3 opciones de guiones publicitarios iniciales basados en fórmulas de copywriting (AIDA, PAS, UGC).

* **Endpoint:** `POST /api/v1/scripts/generate-scripts`
* **Content-Type:** `multipart/form-data`

### Input (Request)
El request debe enviar un campo form llamado `data` conteniendo un JSON en forma de string, y opcionalmente un array de archivos llamado `images`.

**Campo `data` (Stringificado):**
```json
{
  "product_name": "Nombre del producto",
  "product_description": "Descripción detallada",
  "technical_settings": {
    "aspect_ratio": "16:9" // o "9:16", "1:1"
  },
  "preferences": {
    "video_style": "Realista, animado, etc.",
    "music_genre": "Pop, Rock, Electrónica",
    "custom_theme": "Tema específico (opcional)"
  }
}
```
**Campo `images`:** Lista de hasta un máximo de **3 imágenes** (`UploadFile`). Si se mandan más de 3, la API devolverá error 400.

### Output (Response)
Retorna un objeto JSON con 3 opciones de guiones:
```json
{
  "opciones": [
    {
      "id": 1,
      "nombre_estrategia": "AIDA",
      "texto_locucion": "¡Hola! Este es el guion de 8 segundos.",
      "prompt_veo_visual": "Camera pans across the product...",
      "prompt_veo_audio": "Pop background music. Voiceover: ¡Hola!..."
    }
  ]
}
```

---

## 2. Extender Guiones (Continuación)

Genera 3 opciones de guiones de 7 segundos que continúan lógicamente la historia del guion anterior.

* **Endpoint:** `POST /api/v1/scripts/extend-scripts`
* **Content-Type:** `multipart/form-data`

### Input (Request)
El request no recibe imágenes. Debe enviar un campo form llamado `data` conteniendo un JSON en forma de string con el contexto previo.

**Campo `data` (Stringificado):**
```json
{
  "product_name": "Nombre del producto",
  "product_description": "Descripción detallada",
  "previous_script": {
    "id": 1,
    "nombre_estrategia": "AIDA",
    "texto_locucion": "Locución del video previo.",
    "prompt_veo_visual": "Prompt visual anterior...",
    "prompt_veo_audio": "Prompt audio anterior..."
  },
  "technical_settings": {
    "aspect_ratio": "16:9"
  },
  "preferences": {
    "video_style": "Realista",
    "music_genre": "Pop",
    "custom_theme": "Cierre de ventas"
  }
}
```

### Output (Response)
Idéntico al endpoint base, pero enfocado a 7 segundos de continuación y cierre:
```json
{
  "opciones": [ 
    {
      "id": 1,
      "nombre_estrategia": "OPCION 1 (Oferta Agresiva)",
      "texto_locucion": "¡Compra ahora con descuento!",
      "prompt_veo_visual": "Camera zooms into the buy button...",
      "prompt_veo_audio": "Exciting pop climax. Voiceover: ¡Compra ahora..."
    }
  ]
}
```
