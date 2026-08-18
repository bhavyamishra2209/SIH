import pytesseract
from PIL import Image

def extract_text_from_image(image: Image.Image) -> tuple[str, float]:
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    words, confidences = [], []
    for word, conf in zip(data["text"], data["conf"]):
        if word.strip():
            words.append(word)
            if conf != "-1":
                confidences.append(int(conf))
    text = " ".join(words)
    avg_confidence = (sum(confidences) / len(confidences) / 100) if confidences else 0.0
    return text, avg_confidence