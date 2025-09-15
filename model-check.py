from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

MODEL_PATH = r"C://Users//Dell//Desktop//LTI project//disaster_t5_model"

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH)
print("✅ Model loaded successfully")
