"""
Test script to verify image support in dispute analysis.
This demonstrates how to send base64-encoded images with dispute requests.
"""

import base64
import requests
import json

# Configuration
API_URL = "http://localhost:8000/dispute/analyze"
API_KEY = "your-test-api-key-here"  # Replace with actual API key


def encode_image_to_base64(image_path: str) -> tuple[str, str]:
    """
    Encode an image file to base64 string.

    Args:
        image_path: Path to the image file

    Returns:
        Tuple of (base64_data, media_type)
    """
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")

    # Determine media type from file extension
    if image_path.lower().endswith(".png"):
        media_type = "image/png"
    elif image_path.lower().endswith((".jpg", ".jpeg")):
        media_type = "image/jpeg"
    elif image_path.lower().endswith(".gif"):
        media_type = "image/gif"
    elif image_path.lower().endswith(".webp"):
        media_type = "image/webp"
    else:
        media_type = "image/jpeg"  # default

    return image_data, media_type


def test_dispute_with_images():
    """Test dispute analysis with image attachments."""

    # Example 1: Dispute with images
    # Replace with actual image paths
    # image_path1 = "/path/to/damaged_product.jpg"
    # image_data1, media_type1 = encode_image_to_base64(image_path1)

    # For testing without actual images, use a small sample base64 image
    # This is a 1x1 red pixel PNG
    sample_image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="

    request_payload = {
        "dispute_description": "The product arrived damaged. I'm attaching photos showing the damage to the packaging and the product itself.",
        "transaction_id": "TXN-20241101-TEST",
        "amount": 99.99,
        "images": [
            {"data": sample_image_data, "mediaType": "image/png"}
            # You can add multiple images:
            # {
            #     "data": image_data2,
            #     "mediaType": media_type2
            # }
        ],
    }

    headers = {"Content-Type": "application/json", "X-API-Key": API_KEY}

    print("Sending dispute analysis request with images...")
    print(f"Number of images: {len(request_payload['images'])}")

    try:
        response = requests.post(API_URL, json=request_payload, headers=headers)
        response.raise_for_status()

        result = response.json()
        print("\n✅ Success!")
        print(f"Status: {result.get('status')}")
        print(f"Message: {result.get('message')}")
        print(f"Session ID: {result.get('session_id')}")

        if result.get("decision"):
            decision = result["decision"]
            print(f"\nDecision: {decision.get('decision')}")
            print(f"Confidence: {decision.get('confidence')}")
            print(f"Justification: {decision.get('justification')}")
            print(f"Evidence Reviewed: {decision.get('evidence_reviewed')}")

        return result

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
        if hasattr(e.response, "text"):
            print(f"Response: {e.response.text}")
        return None


def test_dispute_without_images():
    """Test dispute analysis without images (standard flow)."""

    request_payload = {
        "dispute_description": "The product never arrived, but tracking shows it was delivered.",
        "transaction_id": "TXN-20241101-TEST2",
        "amount": 49.99,
    }

    headers = {"Content-Type": "application/json", "X-API-Key": API_KEY}

    print("\n" + "=" * 60)
    print("Sending dispute analysis request WITHOUT images...")

    try:
        response = requests.post(API_URL, json=request_payload, headers=headers)
        response.raise_for_status()

        result = response.json()
        print("\n✅ Success!")
        print(f"Status: {result.get('status')}")
        print(f"Message: {result.get('message')}")

        return result

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
        if hasattr(e.response, "text"):
            print(f"Response: {e.response.text}")
        return None


if __name__ == "__main__":
    print("Testing Dispute Analysis with Image Support")
    print("=" * 60)

    # Test with images
    result1 = test_dispute_with_images()

    # Test without images
    result2 = test_dispute_without_images()

    print("\n" + "=" * 60)
    print("Testing complete!")
