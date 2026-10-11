"""Flask blueprints for frontend pages and JSON API endpoints.

Routes Included
---------------
Frontend (Blueprint: frontend_bp)
  GET /                -> Home page (upload form & links)
  GET/POST /identify   -> Pill identification page
  GET /medications     -> User medications list
  GET/POST /interactions -> Interaction checker form

API (Blueprint: api_bp, prefix /api)
  POST /identify-pill      -> Identify pill from uploaded image file
  POST /add-medication     -> Add medication to session list
  GET  /check-interactions -> Check interactions for session medications
  GET  /search-drugs       -> Search sample drug catalog by name or imprint
"""
from __future__ import annotations
from flask import (
    Blueprint,
    render_template,
    request,
    current_app,
    session,
    jsonify,
)
from werkzeug.utils import secure_filename
import os
import uuid

from src.utils.image_processing import load_image, preprocess_image
from src.models.pill_model import identify_pill
from src.utils.interaction_checker import check_interactions
from src.utils.validators import validate_image_file, validate_drug_name, validate_confidence

frontend_bp = Blueprint("frontend", __name__)
api_bp = Blueprint("api", __name__)

# Expanded drug catalog with 14 common medications
DRUG_CATALOG = [
    {"name": "Aspirin", "imprint": "ASP", "strength": "100mg"},
    {"name": "Ibuprofen", "imprint": "IBU", "strength": "200mg"},
    {"name": "Acetaminophen", "imprint": "ACM", "strength": "500mg"},
    {"name": "Metformin", "imprint": "MET", "strength": "500mg"},
    {"name": "Amoxicillin", "imprint": "AMX", "strength": "500mg"},
    {"name": "Lisinopril", "imprint": "LIS", "strength": "10mg"},
    {"name": "Atorvastatin", "imprint": "ATV", "strength": "20mg"},
    {"name": "Omeprazole", "imprint": "OME", "strength": "20mg"},
    {"name": "Levothyroxine", "imprint": "LEV", "strength": "50mcg"},
    {"name": "Metoprolol", "imprint": "MTP", "strength": "50mg"},
    {"name": "Amlodipine", "imprint": "AML", "strength": "5mg"},
    {"name": "Gabapentin", "imprint": "GBP", "strength": "300mg"},
    {"name": "Hydrochlorothiazide", "imprint": "HCT", "strength": "25mg"},
    {"name": "Sertraline", "imprint": "SER", "strength": "50mg"},
]

SESSION_KEY = "user_medications"


def _ensure_session_list():
    if SESSION_KEY not in session:
        session[SESSION_KEY] = []
    return session[SESSION_KEY]

@frontend_bp.route("/")
def home():
    meds = _ensure_session_list()
    return render_template("index.html", medications=meds)

@frontend_bp.route("/identify", methods=["GET", "POST"])
def identify_page():
    pill_id = confidence = image_filename = warning = None
    model_status = "demo"  # Check if trained model exists
    from pathlib import Path
    from config import get_config
    cfg = get_config()
    models_dir = Path(cfg.MODEL_STORAGE_PATH)
    if list(models_dir.glob("*.keras")):
        model_status = "trained"
    
    if request.method == "POST":
        file = request.files.get("pill_image")
        valid, error = validate_image_file(file)
        if not valid:
            return render_template("identify.html", error=error, model_status=model_status)
        try:
            filename = secure_filename(file.filename or "upload.jpg")  # type: ignore[arg-type]
            save_path = os.path.join(current_app.config["IMAGE_UPLOAD_FOLDER"], filename)
            file.save(save_path)  # type: ignore[union-attr]
            image = load_image(save_path)
            processed = preprocess_image(image)
            pill_id, confidence = identify_pill(processed)
            image_filename = filename
            threshold = current_app.config.get("MIN_CONFIDENCE_THRESHOLD", 0.5)
            acceptable, warning = validate_confidence(confidence, threshold)
            if model_status == "demo":
                warning = "Using demo mode predictions. Train a model for accurate results."
        except Exception as e:
            return render_template("identify.html", error=f"Processing failed: {str(e)}", model_status=model_status)
    return render_template(
        "identify.html",
        pill_id=pill_id,
        confidence=f"{confidence:.2%}" if confidence else None,
        image_filename=image_filename,
        warning=warning,
        model_status=model_status,
    )

@frontend_bp.route("/medications")
def medications_page():
    meds = _ensure_session_list()
    return render_template("medications.html", medications=meds)

@frontend_bp.route("/interactions", methods=["GET", "POST"])
def interactions_page():
    meds = _ensure_session_list()
    result = None
    if request.method == "POST":
        # Get manually entered drugs from the form
        drugs_input = request.form.get("drugs", "").strip()
        if drugs_input:
            # Split by comma and clean up drug names
            drug_names = [d.strip() for d in drugs_input.split(",") if d.strip()]
            if len(drug_names) >= 2:
                result = check_interactions(drug_names)
            else:
                result = {"error": "Please enter at least 2 medications"}
        else:
            result = {"error": "Please enter medication names"}
    return render_template("interactions.html", result=result, medications=meds)

@frontend_bp.route("/resources")
def resources_page():
    import json
    from pathlib import Path
    data_path = Path(__file__).resolve().parents[1] / "data" / "drug_information.json"
    try:
        with open(data_path, "r") as f:
            data = json.load(f)
        return render_template("resources.html", medications=data["medications"], resources=data["resources"])
    except Exception as e:
        return render_template("resources.html", medications=[], resources=[], error=str(e))

# ------------------ API ENDPOINTS ------------------ #
@api_bp.route("/identify-pill", methods=["POST"])
def api_identify_pill():
    file = request.files.get("image")
    valid, error = validate_image_file(file)
    if not valid:
        return jsonify({"error": error}), 400
    try:
        filename = secure_filename(file.filename or "upload.jpg")  # type: ignore[arg-type]
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        save_path = os.path.join(current_app.config["IMAGE_UPLOAD_FOLDER"], unique_name)
        file.save(save_path)  # type: ignore[union-attr]
        image = load_image(save_path)
        processed = preprocess_image(image)
        pill_id, confidence = identify_pill(processed)
        threshold = current_app.config.get("MIN_CONFIDENCE_THRESHOLD", 0.5)
        acceptable, warning = validate_confidence(confidence, threshold)
        return jsonify(
            {
                "pill_id": pill_id,
                "confidence": round(confidence, 4),
                "filename": unique_name,
                "acceptable": acceptable,
                "warning": warning,
            }
        )
    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

@api_bp.route("/add-medication", methods=["POST"])
def api_add_medication():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    dose = data.get("dose", "")
    valid, error = validate_drug_name(name)
    if not valid:
        return jsonify({"error": error}), 400
    try:
        meds = _ensure_session_list()
        entry = {"name": (name or "").strip(), "dose": dose}
        meds.append(entry)
        session.modified = True
        return jsonify({"status": "added", "medication": entry, "count": len(meds)})
    except Exception as e:
        return jsonify({"error": f"Failed to add medication: {str(e)}"}), 500

@api_bp.route("/check-interactions", methods=["GET"])
def api_check_interactions():
    try:
        meds = _ensure_session_list()
        drug_names = [m["name"] for m in meds]
        if len(drug_names) < 2:
            return jsonify({"medications": drug_names, "interactions": {}, "message": "Need at least 2 medications to check interactions"})
        result = check_interactions(drug_names)
        return jsonify({"medications": drug_names, "interactions": result})
    except Exception as e:
        return jsonify({"error": f"Interaction check failed: {str(e)}"}), 500

@api_bp.route("/search-drugs", methods=["GET"])
def api_search_drugs():
    query = request.args.get("q", "").lower().strip()
    if not query:
        return jsonify({"results": []})
    matches = [
        d for d in DRUG_CATALOG if query in d["name"].lower() or query in d["imprint"].lower()
    ]
    return jsonify({"results": matches})

# Utility endpoint (optional) to list current medications
@api_bp.route("/medications", methods=["GET"])
def api_list_meds():
    meds = _ensure_session_list()
    return jsonify({"medications": meds})

@api_bp.route("/remove-medication", methods=["GET"])  # simple GET for demo; switch to DELETE for real API
def api_remove_medication():
    idx = request.args.get("index")
    meds = _ensure_session_list()
    try:
        i = int(idx) if idx is not None else -1
    except ValueError:
        return jsonify({"error": "invalid index"}), 400
    if i < 0 or i >= len(meds):
        return jsonify({"error": "index out of range"}), 400
    removed = meds.pop(i)
    session.modified = True
    return jsonify({"status": "removed", "removed": removed, "count": len(meds)})
