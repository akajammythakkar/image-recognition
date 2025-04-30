import base64
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from google.cloud import aiplatform
from google.cloud.aiplatform.gapic.schema import predict
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "supersecretkey"  # Needed for session storage

# Configuration
PROJECT = os.getenv("PROJECT","97482719406")
ENDPOINT_ID = os.getenv("ENDPOINT_ID","1995891780855267328")
LOCATION = os.getnev("LOCATION","us-central1")
API_ENDPOINT = os.getenv("API_ENDPOINT","us-central1-aiplatform.googleapis.com")

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/result')
def result():
    # Get prediction from session
    prediction = session.get("prediction", {"label": "Unknown", "confidence": 0.0})
    return render_template("result.html", prediction=prediction)

@app.route('/predict', methods=['POST'])
def predict_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        file_content = file.read()
        predictions = predict_image_classification(PROJECT, ENDPOINT_ID, file_content, LOCATION, API_ENDPOINT)

        # Store result in session
        session["prediction"] = predictions

        # Redirect to result page
        return redirect(url_for('result'))
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def predict_image_classification(project, endpoint_id, file_content, location, api_endpoint):
    client_options = {"api_endpoint": api_endpoint}
    client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)

    encoded_content = base64.b64encode(file_content).decode("utf-8")
    instance = predict.instance.ImageClassificationPredictionInstance(content=encoded_content).to_value()
    
    instances = [instance]
    parameters = predict.params.ImageClassificationPredictionParams(
        confidence_threshold=0.5,
        max_predictions=5,
    ).to_value()
    
    endpoint = client.endpoint_path(project=project, location=location, endpoint=endpoint_id)
    response = client.predict(endpoint=endpoint, instances=instances, parameters=parameters)

    # Extract predictions
    formatted_predictions = []
    for pred in response.predictions:
        pred_dict = dict(pred)

        formatted_predictions.append({
            "label": pred_dict.get("displayNames", ["Unknown"])[0],  
            "confidence": round(pred_dict.get("confidences", [0.0])[0], 2)
        })
            
    return formatted_predictions[0] if formatted_predictions else {"label": "Unknown", "confidence": 0.0}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
