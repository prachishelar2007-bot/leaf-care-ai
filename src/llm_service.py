import json
import requests
import logging

logger = logging.getLogger(__name__)

from src.config import (
    LLM_PROVIDER,
    OLLAMA_URL,
    OLLAMA_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL,
)
from pathlib import Path


# ============================================================
# MULTIMODAL GEMINI CLASSIFICATION
# ============================================================

def classify_and_explain_with_gemini(image_path: Path):
    """
    Direct multimodal leaf diagnosis via raw HTTP REST call to Google's Gemini API.
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
        
    from PIL import Image
    import io
    import base64
    import requests
    
    img = Image.open(image_path)
    base64_image = ""
    try:
        # Resize image to max 600px width/height while maintaining aspect ratio
        img.thumbnail((600, 600))
        # Convert to RGB if in RGBA mode (PNG) before saving as JPEG
        if img.mode != 'RGB':
            img = img.convert('RGB')
        # Compress to JPEG with 70% quality (typically shrinks image to ~30KB)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=70)
        base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        logger.warning(f"Failed to compress image for Gemini API call: {e}")
        # Fall back to reading raw file bytes
        try:
            with open(image_path, "rb") as f:
                base64_image = base64.b64encode(f.read()).decode('utf-8')
        except Exception as read_err:
            logger.error(f"Failed to read raw image file: {read_err}")
            raise read_err
    
    # Check for plant clues in the filename (e.g. peace_lily, monstera, etc.)
    filename_lower = Path(image_path).name.lower()
    clue_plant = None
    for p in ["peace lily", "peace_lily", "monstera", "snake plant", "snake_plant", "rose", "grape", "tomato", "potato", "apple"]:
        if p in filename_lower:
            clue_plant = p.replace("_", " ").title()
            break
            
    hint_str = ""
    if clue_plant:
        hint_str = f"\n    Hint: The user has indicated this plant is a {clue_plant}. Please verify if this leaf matches that plant and use it as your primary diagnostic reference."
        
    prompt = """
    You are Leaf-Care AI, a professional multimodal agricultural botanist.
    Analyze this leaf photo and output a JSON object containing the plant identification and disease diagnostic results.""" + hint_str + """
    
    The JSON object must have EXACTLY the following keys:
    {
        "plant": "Plant Name (e.g. Grape, Rose, Tomato, Monstera)",
        "disease": "Disease Name (e.g. Black rot, Rust, Healthy, Leaf spot)",
        "confidence": 0.95,
        "description": "Short explanation of the diagnosis...",
        "symptoms": ["Symptom 1", "Symptom 2"],
        "causes": ["Cause 1", "Cause 2"],
        "treatment": ["Immediate treatment step 1", "Treatment step 2"],
        "prevention": ["Prevention step 1", "Prevention step 2"],
        "watering": [
            "Watering frequency guidance (e.g. Every 3 days)",
            "Watering method instruction (e.g. Soil level)",
            "Recommended watering time (e.g. Early morning)",
            "Adjustment details based on disease (e.g. Frequency decreased to dry out foliage)"
        ]
    }
    
    Rules:
    - Return ONLY the raw JSON string. Do not include markdown code fences (such as ```json) or any other text.
    - Be realistic. If the leaf is healthy, identify the plant and set disease to 'Healthy'.
    - If the image does not show a plant leaf, set plant to 'Unknown', disease to 'Invalid', and explain the issue in the description.
    """
    
    # --------------------------------------------------------
    # SEND RAW HTTP POST REQUEST TO GEMINI API WITH MULTI-MODEL FALLBACK
    # --------------------------------------------------------
    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": base64_image
                        }
                    }
                ]
            }
        ]
    }
    
    candidate_models = [GEMINI_MODEL, 'gemini-flash-latest']
    last_err = None
    data = None
    
    for model_name in candidate_models:
        if not model_name:
            continue
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
            response = requests.post(url, headers=headers, json=payload, timeout=3.5)
            if response.status_code == 200:
                data = response.json()
                break
            else:
                logger.warning(f"Model {model_name} returned status {response.status_code}: {response.text[:100]}")
                last_err = f"HTTP {response.status_code}"
        except Exception as conn_err:
            logger.warning(f"Connection to {model_name} failed: {conn_err}")
            last_err = conn_err
            
    if not data:
        logger.warning(f"All Gemini models failed ({last_err}). Seamlessly invoking botanical knowledge engine.")
        from src.knowledge import get_offline_diagnosis
        return get_offline_diagnosis(image_path)

    
    # Extract text from response structure
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    parsed = _parse_json(text)
    
    # Adapt keys so it maps to the UI dictionary keys seamlessly
    adapted = {
        "provider": "Google Gemini (Multimodal Classifier)",
        "notice": "Universal diagnosis generated by Google Gemini using the uploaded leaf photograph directly.",
        "summary": parsed.get("description", ""),
        "symptoms": parsed.get("symptoms", []),
        "causes": parsed.get("causes", []),
        "treatment": parsed.get("treatment", []),
        "prevention": parsed.get("prevention", []),
        "watering": parsed.get("watering", []),
        # Keep classification attributes
        "plant": parsed.get("plant", "Unknown Plant").strip(),
        "disease": parsed.get("disease", "Unknown Disease").strip(),
        "confidence": float(parsed.get("confidence", 0.90))
    }
    return adapted


# ============================================================
# CREATE GENAI PROMPT
# ============================================================

def _prompt(
    plant,
    disease,
    confidence,
    knowledge,
    watering
):

    return f"""
You are Leaf Care AI, a plant-disease
decision-support assistant.

Predicted plant:
{plant}

Predicted disease:
{disease}

Model confidence:
{confidence:.2%}

Use the verified knowledge below as the
primary factual basis.

Disease knowledge:
{json.dumps(
    knowledge,
    ensure_ascii=False
)}

Watering guidance:
{json.dumps(
    watering,
    ensure_ascii=False
)}

Return concise, farmer-friendly advice in
exactly these sections:

1. Summary
2. Symptoms
3. Possible Causes
4. Treatment / Care
5. Prevention
6. Smart Watering

Important rules:

- Do not invent pesticide names.
- Do not invent pesticide dosages.
- Do not promise a guaranteed cure.
- Do not provide unsafe chemical instructions.
- Use simple language.
- Mention that the result is AI-assisted.
- Recommend confirmation with a qualified
  agricultural expert when important.
"""


# ============================================================
# FALLBACK RESPONSE
# ============================================================

def _fallback(
    plant,
    disease,
    knowledge,
    watering,
    reason=""
):

    return {

        "provider": "knowledge-base",

        "summary": knowledge[
            "description"
        ],

        "symptoms": knowledge[
            "symptoms"
        ],

        "causes": knowledge[
            "causes"
        ],

        "treatment": knowledge[
            "treatment"
        ],

        "prevention": knowledge[
            "prevention"
        ],

        "watering": [
            watering[
                "frequency"
            ],

            watering[
                "method"
            ],

            watering[
                "best_time"
            ],

            watering[
                "disease_adjustment"
            ]
        ],

        "notice": (
            "AI explanation service is unavailable, "
            "so the application is showing the "
            "built-in knowledge and care guidance."
            if reason
            else
            "Using the built-in knowledge and "
            "care guidance."
        )
    }


# ============================================================
# PARSE JSON RESPONSE
# ============================================================

def _parse_json(text):

    text = text.strip()

    # --------------------------------------------------------
    # REMOVE MARKDOWN CODE FENCES
    # --------------------------------------------------------

    if text.startswith("```"):

        text = (
            text
            .replace(
                "```json",
                ""
            )
            .replace(
                "```",
                ""
            )
            .strip()
        )

    return json.loads(
        text
    )


# ============================================================
# OLLAMA REQUEST
# ============================================================

def _call_ollama(
    prompt
):

    response = requests.post(

        f"{OLLAMA_URL.rstrip('/')}"
        "/api/generate",

        json={
            "model": OLLAMA_MODEL,

            "prompt": prompt,

            "stream": False
        },

        timeout=60
    )

    response.raise_for_status()

    data = response.json()

    return data[
        "response"
    ]


# ============================================================
# GOOGLE GEMINI REQUEST
# ============================================================

def _call_gemini(
    prompt
):

    if not GEMINI_API_KEY:

        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    # --------------------------------------------------------
    # GEMINI API ENDPOINT
    # --------------------------------------------------------
    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/{GEMINI_MODEL}:generateContent"
    )

    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json"
    }

    # --------------------------------------------------------
    # SEND REQUEST
    # --------------------------------------------------------
    response = requests.post(
        url,
        headers=headers,
        json={
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        },
        timeout=60
    )

    response.raise_for_status()
    data = response.json()

    # --------------------------------------------------------
    # EXTRACT GENERATED TEXT
    # --------------------------------------------------------
    return (
        data[
            "candidates"
        ][0][
            "content"
        ][
            "parts"
        ][0][
            "text"
        ]
    )


# ============================================================
# MAIN EXPLANATION FUNCTION
# ============================================================

def generate_explanation(
    plant,
    disease,
    confidence,
    knowledge,
    watering
):

    prompt = _prompt(
        plant,
        disease,
        confidence,
        knowledge,
        watering
    )

    # ========================================================
    # OLLAMA
    # ========================================================

    if LLM_PROVIDER == "ollama":

        try:

            response = _call_ollama(
                prompt
            )

            parsed = _parse_json(
                response
            )

            parsed[
                "provider"
            ] = "Ollama/local LLM"

            parsed[
                "notice"
            ] = (
                "Explanation generated by a "
                "local LLM using the application's "
                "knowledge context."
            )

            return parsed

        except Exception:

            return _fallback(
                plant,
                disease,
                knowledge,
                watering,
                reason="ollama"
            )

    # ========================================================
    # GOOGLE GEMINI
    # ========================================================

    if LLM_PROVIDER == "gemini":

        try:

            response = _call_gemini(
                prompt
            )

            parsed = _parse_json(
                response
            )

            parsed[
                "provider"
            ] = "Google Gemini"

            parsed[
                "notice"
            ] = (
                "Explanation generated by Google "
                "Gemini using the application's "
                "knowledge context."
            )

            return parsed

        except Exception:

            return _fallback(
                plant,
                disease,
                knowledge,
                watering,
                reason="gemini"
            )

    # ========================================================
    # BUILT-IN KNOWLEDGE MODE
    # ========================================================

    return _fallback(
        plant,
        disease,
        knowledge,
        watering
    )


# ============================================================
# CHATBOT SYSTEM FOR INTERACTIVE QUESTIONS
# ============================================================

def chat_response(history, user_message, plant, disease):
    """
    Get a chatbot response to follow-up questions, preserving history.
    """
    system_instruction = (
        f"You are Leaf-Care AI, a professional agronomist chatbot. The user is asking questions about "
        f"their {plant} which was diagnosed with {disease}.\n"
        f"Be encouraging, scientific, and clear. Limit your response to 2-3 short paragraphs, "
        f"using bullet points if listing steps. Stick to gardening, botany, and plant care advice."
    )

    if LLM_PROVIDER == 'gemini' and GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY, transport='rest')
            contents = []
            for msg in history:
                role = 'user' if msg['role'] == 'user' else 'model'
                contents.append({'role': role, 'parts': [msg['content']]})
            
            contents.append({'role': 'user', 'parts': [f"[System Note: {system_instruction}]\nUser Message: {user_message}"]})
            
            model = genai.GenerativeModel(GEMINI_MODEL)
            response = model.generate_content(contents)
            return response.text
        except Exception as e:
            logger.error(f"Gemini chat error: {e}")
            return f"I'm sorry, I encountered an error connecting to my AI brain: {str(e)}"

    elif LLM_PROVIDER == 'ollama':
        try:
            messages = [{"role": "system", "content": system_instruction}]
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": user_message})

            chat_url = f"{OLLAMA_URL.rstrip('/')}/api/chat"
            payload = {
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False
            }
            response = requests.post(chat_url, json=payload, timeout=20)
            if response.status_code == 200:
                result = response.json()
                return result.get('message', {}).get('content', '')
            else:
                return f"Ollama error: Returned status code {response.status_code}"
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            return f"Ollama is currently unreachable. Error: {str(e)}"

    else:
        return get_fallback_chat_reply(user_message, plant, disease)

def get_fallback_chat_reply(message, plant, disease):
    """
    Provides a simple rule-based response when offline.
    """
    msg = message.lower()
    if "water" in msg or "watering" in msg:
        if "healthy" in disease.lower():
            return f"Since your {plant} is healthy, water it when the top inch of soil is dry. Avoid keeping the soil soggy."
        else:
            return f"For your {plant} affected by {disease}, it is critical to water only at the soil level. Keep the foliage dry to prevent spreading spores, and let the soil surface dry out slightly between waterings."
    elif "fertilize" in msg or "fertilizer" in msg or "feed" in msg:
        return f"Generally, avoid heavily fertilizing diseased plants (like your {plant} with {disease}) as this can force new, tender growth that is highly vulnerable to the pathogen. Focus on curing the disease first."
    elif "cut" in msg or "prune" in msg or "trim" in msg:
        return f"Yes, you should prune off the leaves of your {plant} showing symptoms of {disease}. Use clean shears and disinfect them with alcohol or bleach between cuts so you don't spread the disease to other branches."
    else:
        return (
            f"I am operating in offline fallback mode because no AI LLM is configured. "
            f"To get custom answers for your {plant} ({disease}), please configure Gemini or Ollama in your `.env` file! "
            f"Currently, I can only give predefined advice about 'watering', 'fertilizer', or 'pruning'."
        )
