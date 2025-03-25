from transformers import pipeline

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def classify_email(text, labels):
    result = classifier(text, labels)
    best_label = result['labels'][0]
    score = result['scores'][0]
    return best_label, score, result

def detect_multiple_requests(text, labels):
    lines = text.split('\n')
    requests = []
    for line in lines:
        label, score, _ = classify_email(line, labels)
        if score > 0.7:
            requests.append((line.strip(), label, score))
    primary_request = max(requests, key=lambda x: x[2], default=None)
    return requests, primary_request
