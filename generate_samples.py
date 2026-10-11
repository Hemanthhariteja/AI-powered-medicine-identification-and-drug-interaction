"""Generate sample pill images for testing (simple colored squares)."""
from pathlib import Path
from PIL import Image
import random

DATA_DIR = Path(__file__).resolve().parent / "data" / "pills_dataset"

CLASSES = {
    "aspirin": (255, 255, 255),      # white
    "ibuprofen": (255, 200, 100),     # orange
    "acetaminophen": (240, 240, 220), # off-white
    "metformin": (255, 255, 255),     # white/oblong shape
}

def create_sample_images():
    """Create 5 sample images per class for testing."""
    for class_name, base_color in CLASSES.items():
        class_dir = DATA_DIR / class_name
        class_dir.mkdir(parents=True, exist_ok=True)
        
        for i in range(5):
            # Create simple colored image with slight variation
            r = base_color[0] + random.randint(-20, 20)
            g = base_color[1] + random.randint(-20, 20)
            b = base_color[2] + random.randint(-20, 20)
            color = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
            
            img = Image.new("RGB", (224, 224), color)
            img.save(class_dir / f"sample_{i+1}.jpg")
    
    print(f"✓ Created sample images in {DATA_DIR}")

if __name__ == "__main__":
    create_sample_images()
