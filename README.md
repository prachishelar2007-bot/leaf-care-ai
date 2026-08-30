# Leaf-Care AI 🌿

Leaf-Care AI is a web-based plant health diagnosis and treatment assistant. It classifies plant leaf images using a custom-trained PyTorch MobileNetV2 model and generates comprehensive plant recovery plans utilizing local botanical databases and LLM APIs (Gemini or Ollama).

## Features

- **Leaf Pathogen Classification**: Custom fine-tuned **MobileNetV2** model built in PyTorch (compatible with Python 3.14+).
- **Watering Routine Planner**: Dynamically calculated watering schedules depending on plant variety and active disease state.
- **Actionable AI Care Plans**: Generates structured, step-by-step disease mitigation steps via **Gemini 1.5 Flash** or local **Ollama** models.
- **Interactive Botanical Chatbot**: Allows gardeners to ask follow-up questions about plant diseases, soil health, and fertilizing.
- **Diagnostic Scan History**: High-performance SQLite database logs past uploads, confidence rates, diagnoses, and custom plans.

## Project Structure

```
leaf_care_ai/
├── app.py                  # Main Flask Web Server & API handlers
├── train.py                # MobileNetV2 Model Trainer (with synthetic data fallback)
├── requirements.txt        # Package dependencies
├── .env.example            # Environment variables configuration template
├── .gitignore              # Files ignored by git
├── README.md               # Documentation
│
├── src/
│   ├── __init__.py         # Package declaration
│   ├── config.py           # Application settings and directory resolvers
│   ├── image_utils.py      # Image validators (mime-type, size, PIL integrity)
│   ├── predictor.py        # CPU-based PyTorch inference module
│   ├── knowledge.py        # Local plant details and watering routine math
│   └── llm_service.py      # Gemini/Ollama connector and fallback generators
│
├── templates/              # HTML layout files
│   ├── base.html           # Unified navigation and flash boxes
│   ├── index.html          # Drag-and-drop file upload index
│   ├── result.html         # Analysis results and chatbot dashboard
│   └── history.html        # Database history table
│
├── static/
│   ├── css/
│   │   └── style.css       # Clean leaf-themed style overrides
│   ├── js/
│   │   └── app.js          # File validations, previews, and chat AJAX calls
│   └── uploads/            # Diagnostic image storage (dynamically created)
│
├── models/                 # Model files (dynamically created)
│   └── README.md
│
├── dataset/                # Dataset folder (dynamically created)
│   └── README.md
│
└── data/                   # SQLite database (dynamically created)
```

## Setup Instructions

### 1. Prerequisite Configuration
Ensure Python 3.10+ (specifically verified up to 3.14.7) is installed.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a local `.env` file from the example:
```bash
cp .env.example .env
```
Update your LLM provider (`gemini`, `ollama`, or `none`) and corresponding API keys.

### 4. Train the Model
You can train on your own directory structure under `dataset/PlantVillage/` containing plant subdirectories (e.g. `Tomato___healthy`, `Potato___Early_blight`). 
If the dataset is missing or empty, running this command will **automatically generate a mock synthetic dataset** of leaf images to verify the compilation and run training immediately:
```bash
python train.py
```
This trains a MobileNetV2 model for 5 epochs and writes:
- `models/leaf_care_model.pth`
- `models/classes.txt`

### 5. Run the Web Server
Launch the Flask application:
```bash
python app.py
```
Open your browser and navigate to **`http://localhost:5000`**.
