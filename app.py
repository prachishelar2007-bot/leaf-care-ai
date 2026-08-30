import os
import uuid
import sqlite3
import json
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
    jsonify,
)
from werkzeug.utils import secure_filename

from src.config import (
    UPLOAD_DIR,
    ALLOWED_EXTENSIONS,
    MAX_UPLOAD_MB,
    MODEL_PATH,
    LABELS_PATH,
)

from src.image_utils import validate_image
from src.predictor import DiseasePredictor
from src.llm_service import generate_explanation
from src.knowledge import (
    get_disease_knowledge,
    get_watering_routine,
)


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "leaf-care-ai-development-key"
)

app.config["MAX_CONTENT_LENGTH"] = (
    MAX_UPLOAD_MB * 1024 * 1024
)


# ============================================================
# CREATE REQUIRED DIRECTORIES
# ============================================================

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)

Path("data").mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# LOAD DISEASE PREDICTION MODEL
# ============================================================

predictor = DiseasePredictor(
    MODEL_PATH,
    LABELS_PATH
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():
    """
    Creates the SQLite database and prediction-history table.
    """

    with sqlite3.connect("data/history.db") as connection:

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_name TEXT NOT NULL,
                plant TEXT,
                disease TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        try:
            connection.execute("ALTER TABLE predictions ADD COLUMN ai_result TEXT")
        except sqlite3.OperationalError:
            # Column already exists
            pass

        connection.commit()

# Always initialize database table on import (local & production)
init_db()

# ============================================================
# FILE EXTENSION VALIDATION
# ============================================================

def allowed_file(filename):
    """
    Checks whether the uploaded filename has a supported extension.
    """
    return (
        "." in filename
        and
        filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def index():
    """
    Displays the Leaf Care AI home page.
    """
    return render_template(
        "index.html",
        max_upload_mb=MAX_UPLOAD_MB
    )


# ============================================================
# ANALYZE LEAF IMAGE
# ============================================================

@app.route(
    "/analyze",
    methods=["POST"]
)
def analyze():

    # --------------------------------------------------------
    # GET UPLOADED FILE
    # --------------------------------------------------------

    file = request.files.get(
        "leaf_image"
    )

    # --------------------------------------------------------
    # CHECK WHETHER FILE WAS SELECTED
    # --------------------------------------------------------

    if not file or not file.filename:

        flash(
            "Please select a leaf image.",
            "error"
        )

        return redirect(
            url_for("index")
        )

    # --------------------------------------------------------
    # CHECK FILE EXTENSION
    # --------------------------------------------------------

    if not allowed_file(file.filename):

        flash(
            "Please upload a valid JPG, JPEG or PNG image.",
            "error"
        )

        return redirect(
            url_for("index")
        )

    image_path = None

    try:

        # ----------------------------------------------------
        # SECURE ORIGINAL FILE NAME
        # ----------------------------------------------------

        safe_name = secure_filename(
            file.filename
        )

        # ----------------------------------------------------
        # CREATE UNIQUE FILE NAME
        # ----------------------------------------------------

        unique_name = (
            f"{uuid.uuid4().hex}_"
            f"{safe_name}"
        )

        image_path = (
            UPLOAD_DIR /
            unique_name
        )

        # ----------------------------------------------------
        # SAVE UPLOADED IMAGE
        # ----------------------------------------------------

        file.save(
            image_path
        )

        # ----------------------------------------------------
        # VALIDATE IMAGE
        # ----------------------------------------------------

        validation = validate_image(
            image_path
        )

        if not validation["valid"]:

            image_path.unlink(
                missing_ok=True
            )

            flash(
                validation["message"],
                "error"
            )

            return redirect(
                url_for("index")
            )

        # ----------------------------------------------------
        # CHECK WHETHER MODEL IS AVAILABLE
        # ----------------------------------------------------
        from src.llm_service import classify_and_explain_with_gemini
        from src.config import LLM_PROVIDER, GEMINI_API_KEY

        using_gemini = (LLM_PROVIDER == "gemini" and GEMINI_API_KEY)

        if not using_gemini and not predictor.ready:

            image_path.unlink(
                missing_ok=True
            )

            flash(
                (
                    "The trained model is not installed yet. "
                    "Run train.py first and place the generated "
                    "model and class labels inside the models folder."
                ),
                "error"
            )

            return redirect(
                url_for("index")
            )

        # ----------------------------------------------------
        # PREDICT DISEASE
        # ----------------------------------------------------
        ai_result_json = None
        if using_gemini:
            try:
                # Direct multimodal classification via Gemini
                ai_result = classify_and_explain_with_gemini(image_path)
                plant = ai_result["plant"]
                disease = ai_result["disease"]
                confidence = ai_result["confidence"]
                ai_result_json = json.dumps(ai_result)
            except Exception as e:
                app.logger.warning(f"Multimodal classification failed: {e}. Falling back to MobileNetV2.")
                # Fallback to local model
                prediction = predictor.predict(image_path)
                disease = prediction["disease"]
                plant = prediction["plant"]
                confidence = prediction["confidence"]
        else:
            # Use local ML predictor
            prediction = predictor.predict(image_path)
            disease = prediction["disease"]
            plant = prediction["plant"]
            confidence = prediction["confidence"]

        # ----------------------------------------------------
        # SAVE PREDICTION HISTORY
        # ----------------------------------------------------
        with sqlite3.connect("data/history.db") as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO predictions
                (
                    image_name,
                    plant,
                    disease,
                    confidence,
                    created_at,
                    ai_result
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    unique_name,  # Log unique name to correctly display thumbnail preview
                    plant,
                    disease,
                    confidence,
                    datetime.now().isoformat(timespec="seconds"),
                    ai_result_json,
                ),
            )
            connection.commit()
            prediction_id = cursor.lastrowid

        # ----------------------------------------------------
        # REDIRECT TO RESULT DETAILS
        # ----------------------------------------------------

        return redirect(
            url_for("result_details", prediction_id=prediction_id)
        )

    # ========================================================
    # HANDLE VALIDATION ERRORS
    # ========================================================

    except ValueError as error:

        if image_path:
            image_path.unlink(missing_ok=True)

        flash(
            str(error),
            "error"
        )

        return redirect(
            url_for("index")
        )

    # ========================================================
    # HANDLE UNEXPECTED ERRORS
    # ========================================================

    except Exception:

        if image_path:
            image_path.unlink(missing_ok=True)

        app.logger.exception(
            "Leaf analysis failed"
        )

        flash(
            (
                "Prediction failed. "
                "Please try again with a clear leaf image."
            ),
            "error"
        )

        return redirect(
            url_for("index")
        )


# ============================================================
# DIAGNOSIS DETAILS
# ============================================================

@app.route("/result/<int:prediction_id>")
def result_details(prediction_id):
    """
    Displays the result details for a prediction, loading from database.
    """
    with sqlite3.connect("data/history.db") as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT * FROM predictions WHERE id = ?", (prediction_id,)
        ).fetchone()

    if not row:
        flash("Prediction record not found.", "error")
        return redirect(url_for("index"))

    plant = row["plant"]
    disease = row["disease"]
    confidence = row["confidence"]
    cached_ai_result = row["ai_result"]

    # Decode cached GenAI result or generate on-the-fly
    if cached_ai_result:
        try:
            ai_result = json.loads(cached_ai_result)
            knowledge = get_disease_knowledge(disease, plant)
            # Make sure watering guidance is filled
            watering_list = ai_result.get("watering", [])
            watering = {
                "frequency": watering_list[0] if len(watering_list) > 0 else "Check soil",
                "method": watering_list[1] if len(watering_list) > 1 else "Soil level",
                "best_time": watering_list[2] if len(watering_list) > 2 else "Morning",
                "disease_adjustment": watering_list[3] if len(watering_list) > 3 else "None",
                "note": ai_result.get("notice", "GenAI generated care plan.")
            }
        except Exception:
            knowledge = get_disease_knowledge(disease, plant)
            watering = get_watering_routine(plant, disease)
            ai_result = generate_explanation(
                plant=plant,
                disease=disease,
                confidence=confidence,
                knowledge=knowledge,
                watering=watering,
            )
    else:
        knowledge = get_disease_knowledge(disease, plant)
        watering = get_watering_routine(plant, disease)
        ai_result = generate_explanation(
            plant=plant,
            disease=disease,
            confidence=confidence,
            knowledge=knowledge,
            watering=watering,
        )

    return render_template(
        "result.html",
        image_url=url_for("uploaded_file", filename=row["image_name"]),
        prediction={
            "plant": plant,
            "disease": disease,
            "confidence": confidence,
            "id": row["id"]
        },
        knowledge=knowledge,
        watering=watering,
        ai_result=ai_result,
    )


# ============================================================
# INTERACTIVE BOTANICAL CHATBOT
# ============================================================

@app.route("/api/chat", methods=["POST"])
def api_chat():
    from src.llm_service import chat_response
    
    data = request.get_json() or {}
    prediction_id = data.get("prediction_id")
    user_message = data.get("message", "").strip()
    chat_history = data.get("history", [])

    if not prediction_id or not user_message:
        return jsonify({"response": "Invalid request parameters."}), 400

    with sqlite3.connect("data/history.db") as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT plant, disease FROM predictions WHERE id = ?", (prediction_id,)
        ).fetchone()

    if not row:
        return jsonify({"response": "Prediction record not found."}), 404

    plant = row["plant"]
    disease = row["disease"]

    response_text = chat_response(chat_history, user_message, plant, disease)
    return jsonify({"response": response_text})


# ============================================================
# SERVE UPLOADED IMAGES
# ============================================================

@app.route(
    "/uploads/<filename>"
)
def uploaded_file(filename):

    return send_from_directory(
        UPLOAD_DIR,
        filename
    )


# ============================================================
# PREDICTION HISTORY
# ============================================================

@app.route("/history")
def history():

    with sqlite3.connect(
        "data/history.db"
    ) as connection:

        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT
                *
            FROM predictions
            ORDER BY id DESC
            LIMIT 50
            """
        ).fetchall()

    return render_template(
        "history.html",
        rows=rows
    )


# ============================================================
# FILE SIZE ERROR
# ============================================================

@app.errorhandler(413)
def file_too_large(error):

    flash(
        (
            f"Image is too large. "
            f"Maximum size is {MAX_UPLOAD_MB} MB."
        ),
        "error"
    )

    return redirect(
        url_for("index")
    )


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":

    # Start local development server.
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )
