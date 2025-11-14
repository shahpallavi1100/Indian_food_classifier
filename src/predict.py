import torch
from PIL import Image
from src.model_loader import load_model
from src.transforms import base_transform, tta_transforms
from src.config import DEVICE, CLASS_NAMES
from src.nutrition import NUTRITION_DB

# ---------------------------------------------------------
# Load model only ONCE → major performance speed boost
# ---------------------------------------------------------
_model = None

def get_model():
    global _model
    if _model is None:
        _model = load_model()
    return _model


# ---------------------------------------------------------
# PREDICTION FUNCTION
# ---------------------------------------------------------
def predict_image(img: Image.Image):
    model = get_model()
    model.eval()

    tta_logits = []

    # Apply each TTA transform
    for tfm in tta_transforms:
        x = tfm(img).unsqueeze(0).to(DEVICE)

        with torch.no_grad():
            logits = model(x)

        tta_logits.append(logits)

    # Average predictions across TTA variants
    avg_logits = torch.stack(tta_logits).mean(0)

    # Softmax → probabilities
    prob = torch.softmax(avg_logits, dim=1).cpu().numpy()[0]
    top_idx = prob.argmax()

    dish = CLASS_NAMES[top_idx]
    confidence = float(prob[top_idx])

    # Nutrition lookup
    nutrition = NUTRITION_DB.get(dish.lower(), None)

    return dish, confidence, nutrition
