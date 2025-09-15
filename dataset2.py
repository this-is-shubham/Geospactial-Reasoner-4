# import os
# import json
# import google.generativeai as genai
# from PyPDF2 import PdfReader
# import dotenv
# dotenv.load_dotenv()

# # ----------------------
# # Setup Gemini
# # ----------------------
# API_KEY = os.getenv("GEMINI_API_KEY")
# if not API_KEY:
#     raise ValueError("⚠️ Please set GEMINI_API_KEY in your .env or system environment")

# genai.configure(api_key=API_KEY)
# model = genai.GenerativeModel("gemini-2.5-flash")  # fast & cheap for dataset generation

# # ----------------------
# # Helper: extract text from PDF
# # ----------------------
# def extract_text_from_pdf(pdf_path):
#     reader = PdfReader(pdf_path)
#     text = ""
#     for page in reader.pages:
#         text += page.extract_text() + "\n"
#     return text

# # ----------------------
# # Helper: chunk text into ~2000 chars
# # ----------------------
# def chunk_text(text, max_len=2000):
#     paragraphs = text.split("\n")
#     chunks, current = [], ""
#     for p in paragraphs:
#         if len(current) + len(p) < max_len:
#             current += p.strip() + " "
#         else:
#             chunks.append(current.strip())
#             current = p.strip() + " "
#     if current:
#         chunks.append(current.strip())
#     return chunks

# # ----------------------
# # Prompt Gemini to generate JSON
# # ----------------------
# def make_example(chunk):
#     prompt = f"""
#     You are preparing fine-tuning data for a disaster management AI assistant.

#     TASK:
#     - Read the following passage.
#     - From it, invent a realistic user query (like a tweet, WhatsApp, or citizen query) describing a disaster in a location.
#     - Convert it into a JSON with:
#         * instruction: the messy real-world query
#         * context: structured JSON of hazard features (like flooded_area, rainfall, hospitals, roads, magnitude, etc.)
#         * response: a clear GIS-expert style management plan, grounded in the passage.

#     Input passage:
#     {chunk}

#     IMPORTANT: Output only one valid JSON object.
#     """
#     response = model.generate_content(prompt)
#     raw = response.text.strip()
#     start, end = raw.find("{"), raw.rfind("}")
#     if start == -1 or end == -1:
#         return None
#     try:
#         return json.loads(raw[start:end+1])
#     except:
#         return None


# # ----------------------
# # Main pipeline
# # ----------------------
# def build_dataset(pdf_path, output_jsonl="train.jsonl"):
#     text = extract_text_from_pdf(pdf_path)
#     chunks = chunk_text(text)

#     with open(output_jsonl, "w", encoding="utf-8") as f:
#         for i, chunk in enumerate(chunks, 1):
#             ex = make_example(chunk)
#             if ex:
#                 f.write(json.dumps(ex, ensure_ascii=False) + "\n")
#                 print(f"✅ Example {i} saved")
#             else:
#                 print(f"⚠️ Example {i} failed")

#     print(f"\n🎉 Dataset saved to {output_jsonl}")


# if __name__ == "__main__":
#     # Example usage: replace with your PDF guideline
#     build_dataset('C://Users//Dell//Desktop//LTI project//PREPARATION OF STATE DISASTER.pdf')

# import os
# import json
# import random
# import fitz  # PyMuPDF
# import re
# import dotenv
# import google.generativeai as genai

# dotenv.load_dotenv()

# # ----------------------------
# # Setup Gemini
# # ----------------------------
# API_KEY = os.getenv("GEMINI_API_KEY")
# if not API_KEY:
#     raise ValueError("⚠️ Please set GEMINI_API_KEY in .env")
# genai.configure(api_key=API_KEY)
# model = genai.GenerativeModel("gemini-1.5-flash")

# # ----------------------------
# # Helpers
# # ----------------------------
# def clean_text(text: str) -> str:
#     return re.sub(r"\s+", " ", text).strip()

# def extract_sections_from_pdf(pdf_path: str, max_len=1500) -> list[str]:
#     """Extract reasonably sized text sections from PDF."""
#     doc = fitz.open(pdf_path)
#     sections, current = [], ""
#     for page in doc:
#         text = clean_text(page.get_text())
#         if len(current) + len(text) < max_len:
#             current += text + " "
#         else:
#             sections.append(current.strip())
#             current = text + " "
#     if current:
#         sections.append(current.strip())
#     return sections

# def make_context(hazard_type: str) -> dict:
#     hazard_data = {
#         "flooded_area_km2": None,
#         "rainfall_anomaly": None,
#         "slope_risk_percent": None,
#         "earthquake_risk_zone": None
#     }
#     if hazard_type == "flood":
#         hazard_data["flooded_area_km2"] = round(random.uniform(1, 50), 1)
#         hazard_data["rainfall_anomaly"] = round(random.uniform(20, 80), 1)
#     elif hazard_type == "drought":
#         hazard_data["rainfall_anomaly"] = round(random.uniform(-80, -20), 1)
#     elif hazard_type == "landslide":
#         hazard_data["slope_risk_percent"] = round(random.uniform(5, 40), 1)
#     elif hazard_type == "earthquake":
#         hazard_data["earthquake_risk_zone"] = random.choice(
#             ["Low Risk", "Moderate Risk", "High Risk"]
#         )
#     osm_features = {
#         "hospitals": [{"name": "Civil Hospital"}],
#         "shelters": [{"name": "School Shelter"}],
#         "roads": ["NH15", "Main Road"],
#         "critical_infra": ["Police Station"]
#     }
#     return {"hazard_data": hazard_data, "osm_features": osm_features}

# # ----------------------------
# # Gemini refinement (updated)
# # ----------------------------
# def refine_with_gemini(section: str, hazard: str, context: dict):
#     prompt = f"""
#     You are preparing fine-tuning data for a GIS disaster management assistant.

#     Requirements:
#     - Hazard type: {hazard}
#     - Structured context: {json.dumps(context)}
#     - Background passage: {section}

#     TASK:
#     1. Invent a **realistic citizen query** (messy, urgent, like a tweet or SOS call) according to the disaster detected which is {hazard}.
#     2. The query MUST explicitly mention a **realistic location**: 
#        - A city/town/village in India
#        - Optionally a road/landmark
#        - And/or a valid 6-digit pincode
#     3. Write a clear GIS-expert style disaster management response,
#        grounding it in both the context and the background passage.
#     4. Return valid JSON with fields:
#        - instruction (messy query with location info)
#        - context (the given structured JSON)
#        - response (expert-level plan)

#     Example 1:
#     {{
#       "instruction": "{hazard} in Patna (800001)! Roads near Gandhi Maidan are ... (or any other disaster discription of background passage). What should we do?",
#       "context": {{...}},
#       "response": "GIS analysis shows ..."
#     }}
#     """

#     resp = model.generate_content(prompt)
#     raw = resp.text.strip()
#     start, end = raw.find("{"), raw.rfind("}")
#     if start == -1 or end == -1:
#         return None
#     try:
#         ex = json.loads(raw[start:end+1])
#         ex["context"] = context  # enforce schema consistency

#         # 🔍 Validation: ensure location is present
#         if not re.search(r"\b\d{6}\b", ex["instruction"]) and \
#            not any(place in ex["instruction"] for place in ["Mumbai","Delhi","Patna","Shimla","Assam","Bihar","Kerala","Odisha","Tamil Nadu"]):
#             return None  # reject and regenerate later
#         return ex
#     except:
#         return None


# # ----------------------------
# # Main pipeline
# # ----------------------------
# def build_dataset(pdf_path, out_path="train.jsonl"):
#     sections = extract_sections_from_pdf(pdf_path)
#     hazard_types = ["flood", "drought", "landslide", "earthquake"]
#     with open(out_path, "w", encoding="utf-8") as f:
#         for i, sec in enumerate(sections, 1):
#             hazard = random.choice(hazard_types)
#             context = make_context(hazard)
#             ex = refine_with_gemini(sec, hazard, context)
#             if ex:
#                 f.write(json.dumps(ex, ensure_ascii=False) + "\n")
#                 print(f"✅ Example {i} saved")
#             else:
#                 print(f"⚠️ Example {i} failed")
#     print(f"\n🎉 Dataset saved to {out_path}")

# # ----------------------------
# # Run
# # ----------------------------
# if __name__ == "__main__":
#     build_dataset("C://Users//Dell//Desktop//LTI project//cyclones.pdf",
#                   "cyclones.jsonl")

# import os
# import json
# import re
# import fitz  # PyMuPDF
# import dotenv
# import google.generativeai as genai

# dotenv.load_dotenv()

# # ----------------------------
# # Setup Gemini
# # ----------------------------
# API_KEY = os.getenv("GEMINI_API_KEY")
# if not API_KEY:
#     raise ValueError("⚠️ Please set GEMINI_API_KEY in .env")
# genai.configure(api_key=API_KEY)
# model = genai.GenerativeModel("gemini-2.0-flash")  # use "pro" for better QnA quality

# # ----------------------------
# # PDF Utilities
# # ----------------------------
# def clean_text(text: str) -> str:
#     return re.sub(r"\s+", " ", text).strip()

# def extract_sections_from_pdf(pdf_path: str, max_len=2000) -> list[str]:
#     """Extract reasonably sized text sections from a PDF."""
#     doc = fitz.open(pdf_path)
#     sections, current = [], ""
#     for page in doc:
#         text = clean_text(page.get_text())
#         if len(current) + len(text) < max_len:
#             current += text + " "
#         else:
#             sections.append(current.strip())
#             current = text + " "
#     if current:
#         sections.append(current.strip())
#     return sections

# # ----------------------------
# # Generate QnA from section
# # ----------------------------
# def make_qna_pairs(section: str, hazard: str, num_qna: int = 3):
#     """
#     Ask Gemini to create expert-level QnA pairs from a passage.
#     """
#     prompt = f"""
#     You are creating fine-tuning data for a GIS disaster management assistant.

#     Hazard type: {hazard}

#     Background passage (guidelines/manual):
#     {section}

#     TASK:
#     - Generate {num_qna} diverse QnA pairs.
#     - The **question** should sound like a realistic query a disaster officer or citizen might ask and should strictly be in english, if its not english, redo it in english.
#     - The **answer** should be an expert GIS-style explanation or plan, grounded in the passage.
#     - Use clear professional language (not too bookish, but not casual).
#     - Return ONLY valid JSON list with objects in format:
#       {{
#         "instruction": "...",
#         "response": "..."
#       }}
#     """

#     resp = model.generate_content(prompt)
#     raw = resp.text.strip()

#     # Extract JSON safely
#     start, end = raw.find("["), raw.rfind("]")
#     if start == -1 or end == -1:
#         return []
#     try:
#         return json.loads(raw[start:end+1])
#     except Exception as e:
#         print(f"⚠️ JSON parse failed: {e}")
#         return []

# # ----------------------------
# # Build Dataset
# # ----------------------------
# def build_qna_dataset(pdf_path, hazard, out_path="qna_dataset.jsonl"):
#     sections = extract_sections_from_pdf(pdf_path)
#     with open(out_path, "w", encoding="utf-8") as f:
#         for i, sec in enumerate(sections, 1):
#             qna_list = make_qna_pairs(sec, hazard, num_qna=3)
#             for qna in qna_list:
#                 f.write(json.dumps(qna, ensure_ascii=False) + "\n")
#             print(f"✅ Section {i}: {len(qna_list)} pairs saved")
#     print(f"\n🎉 Dataset saved to {out_path}")

# # ----------------------------
# # Run
# # ----------------------------
# if __name__ == "__main__":
#     # Example: Cyclone PDF
#     build_qna_dataset(
#         pdf_path="C://Users//Dell//Desktop//LTI project//cyclones.pdf",
#         hazard="cyclone",
#         out_path="cyclone_qna.jsonl"
#     )

import os
import json
import random
import fitz  # PyMuPDF
import re
import dotenv
import google.generativeai as genai

dotenv.load_dotenv()

# ----------------------------
# Setup Gemini
# ----------------------------
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("⚠️ Please set GEMINI_API_KEY in .env")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# ----------------------------
# Helpers
# ----------------------------

def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def extract_sections_from_pdf(pdf_path: str, max_len=1500) -> list[str]:
    """Extract reasonably sized text sections from PDF."""
    doc = fitz.open(pdf_path)
    sections, current = [], ""
    for page in doc:
        text = clean_text(page.get_text())
        if len(current) + len(text) < max_len:
            current += text + " "
        else:
            sections.append(current.strip())
            current = text + " "
    if current:
        sections.append(current.strip())
    return sections

def make_context(hazard_type: str) -> dict:
    hazard_data = {
        "flooded_area_km2": None,
        "rainfall_anomaly": None,
        "slope_risk_percent": None,
        "earthquake_risk_zone": None
    }
    if hazard_type == "flood":
        hazard_data["flooded_area_km2"] = round(random.uniform(1, 50), 1)
        hazard_data["rainfall_anomaly"] = round(random.uniform(20, 80), 1)
    elif hazard_type == "drought":
        hazard_data["rainfall_anomaly"] = round(random.uniform(-80, -20), 1)
    elif hazard_type == "landslide":
        hazard_data["slope_risk_percent"] = round(random.uniform(5, 40), 1)
    elif hazard_type == "earthquake":
        hazard_data["earthquake_risk_zone"] = random.choice(
            ["Low Risk", "Moderate Risk", "High Risk"]
        )
    osm_features = {
        "hospitals": [{"name": "Civil Hospital"}],
        "shelters": [{"name": "School Shelter"}],
        "roads": ["NH15", "Main Road"],
        "critical_infra": ["Police Station"]
    }
    return {"hazard_data": hazard_data, "osm_features": osm_features}

# ----------------------------
# Gemini refinement (strict schema)
# ----------------------------
def refine_with_gemini(section: str, hazard: str, context: dict):
    prompt = f"""
You are generating fine-tuning data for a **GIS disaster management assistant**.

## TASK REQUIREMENTS

1. **Citizen Query ("instruction")**
   - Must be written in **urgent, natural English** (like WhatsApp, SMS, tweet, or shouted plea).
   - Must **explicitly mention the hazard**: "{hazard}".
   - Must include a **real Indian city/town/village/district/state name**.
   - Must also include **either**:
     - a well-known **road, landmark, or neighborhood**, OR
     - a **valid 6-digit Indian pincode**.
   - It should sound **specific and desperate**, not generic ("Flood here" is invalid).
   - Example styles:
     - "Earthquake jolted Guwahati near GS Road, buildings cracked, people trapped, urgent help!"
     - "Flood in Cuttack (753001), water 4 feet near Mangalabag, families stranded!"
     - "Massive landslide in Shimla near Mall Road, slope collapsing, need rescue teams!"

2. **Context**
   - Always use exactly the provided structured JSON (do not alter keys):
   {json.dumps(context, indent=2)}

3. **Response (GIS-expert style disaster management plan)**
   - Must be in **structured JSON** with these fields:
     {{
       "situation_assessment": "...",
       "immediate_actions": ["...", "..."],
       "evacuation_and_shelter": ["...", "..."],
       "medical_and_critical_infra": ["...", "..."],
       "long_term_strategies": ["...", "..."]
     }}
   - **situation_assessment**:
     - Must reference `hazard_data` values from context (e.g., flooded_area_km2, rainfall_anomaly, slope_risk_percent, earthquake_risk_zone).
   - **immediate_actions**:
     - Concrete urgent steps (boats, barricades, sirens, alerts).
     - Must reference `osm_features` if relevant (e.g., "Police Station to issue alerts").
   - **evacuation_and_shelter**:
     - Must direct people to actual `shelters` and use `roads` as corridors.
   - **medical_and_critical_infra**:
     - Must activate hospitals, critical_infra (Civil Hospital, Police Station, etc.).
   - **long_term_strategies**:
     - GIS-informed measures (drainage upgrades, slope stabilization, seismic retrofitting).

## Background reference (to enrich realism):
{section}

## OUTPUT INSTRUCTIONS
- Output **valid JSON only**, nothing else.
- Ensure the JSON structure matches this example exactly:

{{
  "instruction": "Flood in Patna (800001)! Water waist-deep near Gandhi Maidan, people trapped!",
  "context": {json.dumps(context, indent=2)},
  "response": {{
    "situation_assessment": "Flooding has impacted 12.4 km² in Patna near Gandhi Maidan with +45.6% rainfall anomaly.",
    "immediate_actions": [
      "Deploy boats to Gandhi Maidan where people are trapped.",
      "Issue evacuation orders via Police Station loudspeaker vans."
    ],
    "evacuation_and_shelter": [
      "Direct residents to the School Shelter.",
      "Keep NH15 clear as evacuation corridor."
    ],
    "medical_and_critical_infra": [
      "Civil Hospital to activate emergency triage.",
      "Police Station to coordinate rescue operations."
    ],
    "long_term_strategies": [
      "Inspect drainage capacity around Gandhi Maidan.",
      "Reinforce flood bunds before next monsoon."
    ]
  }}
}}
"""
    resp = model.generate_content(prompt)
    raw = resp.text.strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        ex = json.loads(raw[start:end+1])
        ex["context"] = context  # enforce schema consistency
        return ex
    except:
        return None


# ----------------------------
# Main pipeline
# ----------------------------
def build_dataset(pdf_path, out_path="train.jsonl", hazard_filter=None):
    sections = extract_sections_from_pdf(pdf_path)

    with open(out_path, "w", encoding="utf-8") as f:
        for i, sec in enumerate(sections, 1):
            # 🔹 If hazard_filter is provided, lock to that
            if hazard_filter:
                hazard = hazard_filter
            else:
                hazard = random.choice(["flood", "landslide", "earthquake"])

            context = make_context(hazard)
            ex = refine_with_gemini(sec, hazard, context)

            if ex:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")
                print(f"✅ Example {i} saved ({hazard})")
            else:
                print(f"⚠️ Example {i} failed")

    print(f"\n🎉 Dataset saved to {out_path}")


# ----------------------------
# Run
# ----------------------------
if __name__ == "__main__":

    build_dataset("C://Users//Dell//Desktop//LTI project//earthquakes.pdf",
                "earthquake_dataset.jsonl",
                hazard_filter="earthquake")  # lock to earthquake


