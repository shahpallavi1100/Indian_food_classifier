import torch
import timm
from src.config import MODEL_PATH, DEVICE, CLASS_NAMES, MODEL_NAME

_cached_model = None


def load_model():
    """Load & cache the trained model for fast inference."""
    global _cached_model

    # Return cached model if already loaded
    if _cached_model is not None:
        return _cached_model

    try:
        # ---------------------
        # Create model architecture
        # ---------------------
        model = timm.create_model(
            MODEL_NAME,     # <--- now controlled from config.py
            pretrained=False,
            num_classes=len(CLASS_NAMES)
        )

        # ---------------------
        # Load weights
        # ---------------------
        state = torch.load(
            MODEL_PATH,
            map_location=DEVICE
        )

        model.load_state_dict(state, strict=True)
        model.to(DEVICE)
        model.eval()

        _cached_model = model
        return _cached_model

    except FileNotFoundError:
        raise RuntimeError(f"❌ Model file not found at {MODEL_PATH}")
    except Exception as e:
        raise RuntimeError(f"❌ Error loading model: {e}")
