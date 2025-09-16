# # trial.py
# from fastapi import FastAPI
# from typing import Dict, Optional
# from hazard_features import HAZARD_FEATURE_MAP
# from geocode import nominatim_geocode
# from phase3_features import get_disaster_features
# from schemas import InterpretationRequest, InterpretationResponse, DisasterFeatures

# import os, json, torch
# from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# # ----------------------------
# # MODEL LOAD (your fine-tuned T5)
# # ----------------------------
# MODEL_PATH = r"C:\Users\Dell\Desktop\LTI project\downloaded_folder\content\drive\MyDrive\R2-disaster_model_t5"

# tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
# model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH)
# device = "cuda" if torch.cuda.is_available() else "cpu"
# model.to(device)

# print("✅ Disaster model loaded from:", MODEL_PATH)

# # ----------------------------
# # Helper: Run model inference
# # ----------------------------
# def run_model(user_text: str, context: dict) -> dict:
#     """Takes user query + disaster features context → returns structured JSON response."""
#     # Input formatting just like training
#     input_text = f"{user_text}\nContext: {json.dumps(context)}"
#     inputs = tokenizer(input_text, return_tensors="pt", truncation=True, padding=True).to(device)

#     outputs = model.generate(**inputs, max_new_tokens=300)
#     decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)

#     try:
#         return json.loads(decoded)
#     except Exception:
#         # if output is not perfect JSON, wrap it
#         return {"raw_output": decoded}

# # ----------------------------
# # FASTAPI APP
# # ----------------------------
# app = FastAPI(title="Disaster Response API", version="1.0.0")

# @app.post("/interpret", response_model=InterpretationResponse)
# def interpret_disaster(req: InterpretationRequest):
#     user_text = req.user_text

#     # 1️⃣ Geocode
#     geo = {}
#     try:
#         geo = nominatim_geocode(user_text)
#         if not geo and "," in user_text:
#             geo = nominatim_geocode(user_text.split(",")[-1].strip())
#     except Exception as e:
#         print(f"Geocoding error: {e}")

#     # 2️⃣ Hazard type (basic guess)
#     hazard_type = "unknown"
#     for h in HAZARD_FEATURE_MAP.keys():
#         if h in user_text.lower():
#             hazard_type = h
#             break

#     # 3️⃣ Fetch disaster features (GEE + OSM)
#     disaster_features_data = {}
#     if geo.get("bounding_box"):
#         try:
#             disaster_features_data = get_disaster_features(
#                 bbox=geo["bounding_box"],
#                 hazard_types=[hazard_type],
#             )
#         except Exception as e:
#             print(f"Error fetching disaster features: {e}")

#     disaster_features = DisasterFeatures(**disaster_features_data) if disaster_features_data else None

#     # 4️⃣ Run your fine-tuned model for structured response
#     model_response = run_model(user_text, {
#         "hazard_data": disaster_features_data.get("hazard_data", {}),
#         "osm_features": disaster_features_data.get("osm_features", {})
#     })

#     # 5️⃣ Return enriched response
#     return InterpretationResponse(
#         disaster_type=hazard_type,
#         location_text=user_text,
#         pincode=geo.get("pincode", ""),
#         time_horizon="now",
#         severity_hint="",
#         notes="",
#         confidence=1.0,  # placeholder, could add heuristic
#         lat=geo.get("lat"),
#         lon=geo.get("lon"),
#         bounding_box=geo.get("bounding_box"),
#         features_to_fetch=HAZARD_FEATURE_MAP.get(hazard_type, []),
#         disaster_features=disaster_features,
#         response=model_response
#     )
# # trial.py
# from fastapi import FastAPI
# from typing import Dict, Optional
# from hazard_features import HAZARD_FEATURE_MAP
# from geocode import nominatim_geocode
# from phase3_features import get_disaster_features
# from schemas import InterpretationRequest, InterpretationResponse, DisasterFeatures

# import os, json, torch
# from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# # ----------------------------
# # MODEL LOAD (fine-tuned T5)
# # ----------------------------
# MODEL_PATH = r"C:\Users\Dell\Desktop\LTI project\downloaded_folder\content\drive\MyDrive\R2-disaster_model_t5"

# tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
# model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH)
# device = "cuda" if torch.cuda.is_available() else "cpu"
# model.to(device)

# print("✅ Disaster model loaded from:", MODEL_PATH)


# def run_model(input_text: str) -> dict:
#     """Run model and parse JSON if possible."""
#     inputs = tokenizer(input_text, return_tensors="pt", truncation=True, padding=True).to(device)
#     outputs = model.generate(**inputs, max_new_tokens=300)
#     decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)

#     try:
#         return json.loads(decoded)
#     except Exception:
#         return {"raw_output": decoded}


# # ----------------------------
# # FASTAPI APP
# # ----------------------------
# app = FastAPI(title="Disaster Response API", version="1.1.0")


# @app.post("/interpret", response_model=InterpretationResponse)
# def interpret_disaster(req: InterpretationRequest):
#     user_text = req.user_text

#     # 1️⃣ Step 1: Structured interpretation from model
#     base = run_model(user_text)
#     hazard_type = base.get("disaster_type", "unknown")
#     location_text = base.get("location_text", user_text)  # fallback

#     # 2️⃣ Step 2: Geocode location_text
#     geo = {}
#     if location_text:
#         try:
#             geo = nominatim_geocode(location_text)
#             if not geo and "," in location_text:
#                 geo = nominatim_geocode(location_text.split(",")[-1].strip())
#         except Exception as e:
#             print(f"Geocoding error: {e}")

#     if geo.get("pincode") and not base.get("pincode"):
#         base["pincode"] = geo["pincode"]

#     # 3️⃣ Step 3: Fetch disaster features (GEE + OSM)
#     disaster_features_data = {}
#     if geo.get("bounding_box"):
#         try:
#             disaster_features_data = get_disaster_features(
#                 bbox=geo["bounding_box"],
#                 hazard_types=[hazard_type],
#             )
#         except Exception as e:
#             print(f"Error fetching disaster features: {e}")

#     disaster_features = DisasterFeatures(**disaster_features_data) if disaster_features_data else None

#     # 4️⃣ Step 4: Detailed evaluation plan from model (with context)
#     model_response = run_model(
#         f"Instruction: {user_text}\nContext: {json.dumps(disaster_features_data)}"
#     )

#     # 5️⃣ Final return
#     return InterpretationResponse(
#         **base,
#         lat=geo.get("lat"),
#         lon=geo.get("lon"),
#         bounding_box=geo.get("bounding_box"),
#         features_to_fetch=HAZARD_FEATURE_MAP.get(hazard_type, []),
#         disaster_features=disaster_features,
#         response=model_response
#     )
# trial-new.py
# trial-new.py
# trial-new.py
# from fastapi import FastAPI
# from typing import List, Tuple, Optional, Dict, Any
# from hazard_features import HAZARD_FEATURE_MAP
# from geocode import nominatim_geocode
# from phase3_features import get_disaster_features
# from schemas import InterpretationRequest, InterpretationResponse, DisasterFeatures

# import os, json, torch
# from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# # ----------------------------
# # MODEL SETUP
# # ----------------------------
# MODEL_PATH = MODEL_PATH = "C://Users//Dell//Desktop//LTI project//disaster_t5_model//content//disaster_t5_model"# <-- replace with your trained folder path

# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
# model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH).to(device)

# print(f"✅ Disaster model loaded from: {MODEL_PATH}")

# # ----------------------------
# # MODEL INFERENCE
# # ----------------------------
# def run_model(instruction: str, context: dict) -> dict:
#     """
#     Run fine-tuned T5 on user instruction + hazard context.
#     Always try to return JSON, fallback to structured dict if parse fails.
#     """
#     # Prepare input text
#     input_text = f"Instruction: {instruction}\nContext: {json.dumps(context)}"
#     inputs = tokenizer(input_text, return_tensors="pt", truncation=True, padding=True).to(device)

#     # Generate
#     outputs = model.generate(
#         **inputs,
#         max_new_tokens=512,
#         num_beams=4,
#         early_stopping=True
#     )
#     decoded = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

#     # Debug log
#     os.makedirs("logs", exist_ok=True)
#     with open("logs/model_outputs.txt", "a", encoding="utf-8") as f:
#         f.write(f"\nINPUT: {input_text}\nOUTPUT: {decoded}\n{'='*50}\n")

#     # Try parsing JSON
#     start, end = decoded.find("{"), decoded.rfind("}")
#     if start != -1 and end != -1:
#         try:
#             return json.loads(decoded[start:end+1])
#         except:
#             pass

#     # Fallback if not JSON
#     return {
#         "situation_assessment": decoded,
#         "immediate_actions": [],
#         "evacuation_and_shelter": [],
#         "medical_and_critical_infra": [],
#         "long_term_strategies": []
#     }

# # ----------------------------
# # FASTAPI APP
# # ----------------------------
# app = FastAPI(title="Disaster Response API", version="1.0.0")

# @app.post("/interpret", response_model=InterpretationResponse)
# def interpret_disaster(req: InterpretationRequest):
#     user_text = req.user_text

#     # 1️⃣ Geocode location
#     geo = {}
#     try:
#         geo = nominatim_geocode(user_text)
#     except Exception as e:
#         print(f"Geocoding error: {e}")

#     # 2️⃣ Hazard + OSM features (if bbox available)
#     disaster_features_data = {}
#     if geo.get("bounding_box"):
#         try:
#             disaster_features_data = get_disaster_features(
#                 bbox=geo["bounding_box"],
#                 hazard_types=["flood", "earthquake", "landslide", "cyclone"]  # broad by default
#             )
#         except Exception as e:
#             print(f"Error fetching disaster features: {e}")

#     disaster_features = DisasterFeatures(**disaster_features_data) if disaster_features_data else None

#     # 3️⃣ Generate response from fine-tuned model
#     model_response = run_model(user_text, disaster_features_data)

#     # 4️⃣ Build structured response
#     return InterpretationResponse(
#         disaster_type=model_response.get("disaster_type", "unknown"),
#         location_text=user_text,
#         pincode=geo.get("pincode", ""),
#         time_horizon=model_response.get("time_horizon", "now"),
#         severity_hint=model_response.get("severity_hint", ""),
#         notes=model_response.get("notes", ""),
#         confidence=model_response.get("confidence", 0.7),
#         lat=geo.get("lat"),
#         lon=geo.get("lon"),
#         bounding_box=geo.get("bounding_box"),
#         features_to_fetch=HAZARD_FEATURE_MAP.get(model_response.get("disaster_type", "unknown"), []),
#         disaster_features=disaster_features,
#         response=model_response  # raw model output included
#     )
from fastapi import FastAPI
from hazard_features import HAZARD_FEATURE_MAP
from geocode import nominatim_geocode
from phase3_features import get_disaster_features
from schemas import InterpretationRequest, InterpretationResponse, DisasterFeatures

import os, re, json, torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# ----------------------------
# MODEL SETUP
# ----------------------------
MODEL_PATH = r"C:\Users\Dell\Desktop\LTI project\disaster_t5_model\content\disaster_t5_model"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH).to(device)

print(f"✅ Disaster model loaded from: {MODEL_PATH}")

# ----------------------------
# MODEL INFERENCE
# ----------------------------
def run_model(instruction: str, context: dict) -> dict:
    """
    Run fine-tuned T5 on user instruction + hazard context.
    Force JSON output.
    """
    schema_hint = """
    You must return a JSON object with these keys:
    {
      "disaster_type": "...",
      "location_text": "...",
      "pincode": "...",
      "time_horizon": "...",
      "severity_hint": "...",
      "notes": "...",
      "confidence": 0.0,
      "situation_assessment": "...",
      "immediate_actions": [],
      "evacuation_and_shelter": [],
      "medical_and_critical_infra": [],
      "long_term_strategies": []
    }
    """

    input_text = f"Instruction: {instruction}\nContext: {json.dumps(context)}\n{schema_hint}"
    inputs = tokenizer(input_text, return_tensors="pt", truncation=True, padding=True).to(device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=512,
        num_beams=4,
        early_stopping=True
    )
    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

    # Try parsing JSON
    start, end = decoded.find("{"), decoded.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(decoded[start:end+1])
        except:
            pass

    # Fallback
    return {"raw_output": decoded, "disaster_type": "unknown"}

# ----------------------------
# FASTAPI APP
# ----------------------------
app = FastAPI(title="Disaster Response API", version="1.2.0")

@app.post("/interpret", response_model=InterpretationResponse)
def interpret_disaster(req: InterpretationRequest):
    user_text = req.user_text

    # 1️⃣ Run model to interpret disaster
    base = run_model(user_text, {})
    hazard_type = base.get("disaster_type", "unknown")
    location_text = base.get("location_text", user_text)

    # 2️⃣ Geocode (use location_text first, fallback user_text)
    geo = {}
    try:
        geo = nominatim_geocode(location_text)
        if not geo:
            geo = nominatim_geocode(user_text)
    except Exception as e:
        print(f"Geocoding error: {e}")

    # Fallback: extract pincode from text if missing
    if not geo.get("pincode"):
        match = re.search(r"\b\d{6}\b", user_text)
        if match:
            geo["pincode"] = match.group(0)

    if geo.get("pincode") and not base.get("pincode"):
        base["pincode"] = geo["pincode"]

    # 3️⃣ Fetch disaster features
    disaster_features_data = {}
    if geo.get("bounding_box"):
        try:
            disaster_features_data = get_disaster_features(
                bbox=geo["bounding_box"],
                hazard_types=[hazard_type],
            )
        except Exception as e:
            print(f"Error fetching disaster features: {e}")

    disaster_features = DisasterFeatures(**disaster_features_data) if disaster_features_data else None

    # 4️⃣ Generate detailed response (with context)
    model_response = run_model(user_text, disaster_features_data)

    # 5️⃣ Build structured response
    return InterpretationResponse(
        disaster_type=hazard_type,
        location_text=location_text,
        pincode=base.get("pincode", ""),
        time_horizon=base.get("time_horizon", "now"),
        severity_hint=base.get("severity_hint", ""),
        notes=base.get("notes", ""),
        confidence=base.get("confidence", 0.7),
        lat=geo.get("lat"),
        lon=geo.get("lon"),
        bounding_box=geo.get("bounding_box"),
        features_to_fetch=HAZARD_FEATURE_MAP.get(hazard_type, []),
        disaster_features=disaster_features,
        response=model_response
    )


