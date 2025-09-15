from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model
import bitsandbytes as bnb
import json

# Load dataset
def load_jsonl(path):
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            data.append({
                "input": f"Citizen query: {obj['instruction']}\nContext: {json.dumps(obj['context'])}",
                "output": json.dumps(obj['response'])
            })
    return data

train_data = load_jsonl("cleaned_dataset.jsonl")[:800]
val_data = load_jsonl("cleaned_dataset.jsonl")[800:]

# Save to HF dataset
from datasets import Dataset
train_dataset = Dataset.from_list(train_data)
val_dataset = Dataset.from_list(val_data)

# # Model + tokenizer
# model_name = "mistralai/Mistral-7B-Instruct-v0.2"
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModelForCausalLM.from_pretrained(
#     model_name,
#     load_in_4bit=True,
#     device_map="auto"
# )
model_name = "microsoft/phi-3-mini-128k-instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    load_in_4bit=True,
    device_map="auto"
)




# LoRA config
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj","v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, lora_config)

# Tokenize
def tokenize(batch):
    inp = tokenizer(batch["input"], truncation=True, padding="max_length", max_length=512)
    out = tokenizer(batch["output"], truncation=True, padding="max_length", max_length=512)
    inp["labels"] = out["input_ids"]
    return inp

train_dataset = train_dataset.map(tokenize, batched=True)
val_dataset = val_dataset.map(tokenize, batched=True)

# Training args
args = TrainingArguments(
    output_dir="./shubham_mistral_finetuned",
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    gradient_accumulation_steps=4,
    evaluation_strategy="steps",
    save_strategy="steps",
    learning_rate=2e-4,
    num_train_epochs=2,
    logging_dir="./logs",
    logging_steps=50,
    save_steps=200,
    eval_steps=200,
    bf16=True
)

trainer = Trainer(
    model=model,
    args=args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset
)

trainer.train()
