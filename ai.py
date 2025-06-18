import app as a

# Roboflow إعدادات
ROBOFLOW_API_KEY = "J5B3YIN1MZzAhnSQFLoV"
MODEL_ID = "strawberry-detections"
VERSION = "1"
ROBOFLOW_API_URL = f"https://detect.roboflow.com/{MODEL_ID}/{VERSION}?api_key={ROBOFLOW_API_KEY}"

# قاموس الأمراض
plant_diseases = {
    "Angular Leafspot": {
        "Cause": "Bacterial infection (Pseudomonas syringae pv. lachrymans)",
        "Treatment": "Use copper-based fungicides and remove infected leaves",
        "Prevention": "Avoid overhead irrigation, use disease-resistant varieties, rotate crops"
    },
    "Anthracnose Fruit Rot": {
        "Cause": "Fungal infection (Colletotrichum spp.)",
        "Treatment": "Apply fungicides like chlorothalonil or copper sprays, remove infected fruits",
        "Prevention": "Ensure good air circulation, avoid fruit injury, sanitize tools"
    },
    "Blossom Blight": {
        "Cause": "Fungal infection (e.g., Botrytis cinerea or Monilinia spp.)",
        "Treatment": "Use fungicides such as iprodione or thiophanate-methyl",
        "Prevention": "Avoid high humidity, prune for air circulation, remove infected blossoms"
    },
    "Gray Mold": {
        "Cause": "Fungal infection (Botrytis cinerea)",
        "Treatment": "Apply fungicides like fenhexamid, remove and destroy infected parts",
        "Prevention": "Improve ventilation, avoid excess moisture, remove plant debris"
    },
    "Leaf Spot": {
        "Cause": "Fungal or bacterial pathogens (e.g., Septoria, Cercospora)",
        "Treatment": "Use appropriate fungicides or bactericides depending on the cause",
        "Prevention": "Avoid wetting foliage, use resistant varieties, clean up fallen leaves"
    },
    "Powdery Mildew Fruit": {
        "Cause": "Fungal infection (e.g., Podosphaera spp.)",
        "Treatment": "Spray with sulfur-based or systemic fungicides like myclobutanil",
        "Prevention": "Ensure good air circulation, avoid over-fertilizing, use resistant cultivars"
    },
    "Powdery Mildew Leaf": {
        "Cause": "Fungal infection (e.g., Erysiphe spp.)",
        "Treatment": "Apply fungicides like neem oil, potassium bicarbonate, or sulfur",
        "Prevention": "Prune overcrowded plants, reduce humidity, plant in sunny areas"
    }
}

@a.app.route("/predict", methods=["POST"])
def predict():
    if 'image' not in a.request.files:
        return a.jsonify({'error': 'No image provided'}), 400

    try:
        # استلام الصورة
        image_file = a.request.files['image']
        img = a.Image.open(image_file).convert("RGB")

        buffered = a.io.BytesIO()
        img.save(buffered, format="JPEG")
        buffered.seek(0)

        response = a.requests.post(
            ROBOFLOW_API_URL,
            files={"file": buffered}
        )

        if response.status_code == 200:
            rf_result = response.json()
            predictions = rf_result.get("predictions", [])

            if predictions:
                first_prediction = predictions[0]
                disease_name = first_prediction.get("class", "Unknown")
                confidence = round(first_prediction.get("confidence", 0) * 100, 2)

                disease_info = plant_diseases.get(disease_name, {})

                return a.jsonify({
                    'disease': {
                        "name": disease_name,
                        "confidence": confidence,
                        "info": disease_info or {}
                    }
                })

            else:
                return a.jsonify({"message": "No disease detected"}), 200

        else:
            return a.jsonify({'roboflow_error': response.text}), 500

    except Exception as e:
        return a.jsonify({'error': f'Failed to process image: {str(e)}'}), 500