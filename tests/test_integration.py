"""Integration test for complete flow: upload -> identify -> add -> check interactions."""
from __future__ import annotations
import io
from pathlib import Path
from PIL import Image
import numpy as np

from src.app import create_app


def test_complete_flow():
    """Test the complete user flow from image upload to interaction checking."""
    app = create_app("testing")
    client = app.test_client()
    
    with app.app_context():
        # 1. Home page loads
        resp = client.get("/")
        assert resp.status_code == 200
        
        # 2. Create a dummy image
        img_arr = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        img = Image.fromarray(img_arr)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        
        # 3. Upload via API
        resp = client.post(
            "/api/identify-pill",
            data={"image": (img_bytes, "test_pill.png")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "pill_id" in data
        assert "confidence" in data
        pill_name = data["pill_id"]
        
        # 4. Add identified drug to session
        resp = client.post(
            "/api/add-medication",
            json={"name": pill_name, "dose": "100mg"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "added"
        
        # 5. Add another drug manually
        resp = client.post(
            "/api/add-medication",
            json={"name": "ibuprofen", "dose": "200mg"},
        )
        assert resp.status_code == 200
        
        # 6. Check interactions
        resp = client.get("/api/check-interactions")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "medications" in data
        assert len(data["medications"]) == 2
        assert "interactions" in data
        
        # 7. Remove medication
        resp = client.get("/api/remove-medication?index=0")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 1


def test_error_handling():
    """Test error handling for invalid inputs."""
    app = create_app("testing")
    client = app.test_client()
    
    with app.app_context():
        # Invalid file type
        resp = client.post(
            "/api/identify-pill",
            data={"image": (io.BytesIO(b"test"), "test.txt")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400
        
        # Missing drug name
        resp = client.post("/api/add-medication", json={"dose": "100mg"})
        assert resp.status_code == 400
        
        # Invalid index for removal
        resp = client.get("/api/remove-medication?index=999")
        assert resp.status_code == 400


if __name__ == "__main__":
    test_complete_flow()
    test_error_handling()
    print("✓ All integration tests passed")
