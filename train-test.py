import json
import random

# Input & Output
input_file = "C://Users//Dell//Desktop//LTI project//train-test.py"
train_file = "train.jsonl"
eval_file = "eval.jsonl"

# Read data
with open(input_file, "r", encoding="utf-8") as f:
    data = [json.loads(line) for line in f]

# Shuffle for randomness
random.shuffle(data)

# 90/10 split
split_idx = int(0.9 * len(data))
train_data, eval_data = data[:split_idx], data[split_idx:]

# Save train
with open(train_file, "w", encoding="utf-8") as f:
    for ex in train_data:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

# Save eval
with open(eval_file, "w", encoding="utf-8") as f:
    for ex in eval_data:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"✅ Split complete: {len(train_data)} train, {len(eval_data)} eval")
