import os
import sys
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
from PIL import Image, ImageDraw
import random

# Config import
# Set path to include current dir
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from src import config

def generate_synthetic_dataset(dataset_dir):
    """
    Generates a small synthetic leaf disease dataset for quick testing and training.
    Supports all 10 classes present in the database.
    """
    classes = [
        "Tomato___healthy",
        "Tomato___Bacterial_spot",
        "Apple___Black_rot",
        "Potato___Early_blight",
        "Potato___Late_blight",
        "Apple___healthy",
        "Potato___healthy",
        "Apple___Apple_scab",
        "Tomato___Early_blight",
        "Tomato___Late_blight"
    ]
    
    print(f"Checking dataset directories under '{dataset_dir}'...")
    os.makedirs(dataset_dir, exist_ok=True)
    
    generated_any = False
    for cls in classes:
        cls_dir = os.path.join(dataset_dir, cls)
        # Check if dir exists and has images, if not, generate them
        if not os.path.exists(cls_dir) or len([f for f in os.listdir(cls_dir) if f.endswith('.jpg')]) == 0:
            os.makedirs(cls_dir, exist_ok=True)
            print(f"Generating synthetic images for: {cls}")
            generated_any = True
            
            # Generate 20 synthetic leaf images per class
            for i in range(20):
                # Base green color for the leaf (varies slightly by plant type)
                if "Apple" in cls:
                    # Dark forest green
                    leaf_color = (
                        random.randint(30, 60),   # Red
                        random.randint(90, 130),  # Green
                        random.randint(30, 60)    # Blue
                    )
                elif "Potato" in cls:
                    # Pale yellowish green
                    leaf_color = (
                        random.randint(90, 130),  # Red
                        random.randint(160, 200), # Green
                        random.randint(50, 90)    # Blue
                    )
                else: # Tomato
                    # Bright medium green
                    leaf_color = (
                        random.randint(40, 80),   # Red
                        random.randint(140, 180), # Green
                        random.randint(40, 80)    # Blue
                    )
                
                # Create base image (224x224) with light gray background for high contrast
                img = Image.new('RGB', (224, 224), color=(240, 240, 240))
                draw = ImageDraw.Draw(img)
                
                # Draw plant-specific leaf shapes
                if "Apple" in cls:
                    # Apple leaf: Broad, rounded oval
                    draw.ellipse([40, 30, 184, 194], fill=leaf_color, outline=(20, 60, 20), width=2)
                    # Midrib
                    draw.line([112, 30, 112, 194], fill=(20, 60, 20), width=2)
                elif "Potato" in cls:
                    # Potato leaf: Wide, smooth oval
                    draw.ellipse([30, 45, 194, 179], fill=leaf_color, outline=(40, 90, 30), width=2)
                    # Midrib
                    draw.line([112, 45, 112, 179], fill=(40, 90, 30), width=2)
                else: # Tomato
                    # Tomato leaf: Lobed compound leaf look (three overlapping ellipses)
                    draw.ellipse([72, 40, 152, 140], fill=leaf_color, outline=(20, 70, 20), width=1)
                    draw.ellipse([42, 90, 112, 170], fill=leaf_color, outline=(20, 70, 20), width=1)
                    draw.ellipse([112, 90, 182, 170], fill=leaf_color, outline=(20, 70, 20), width=1)
                    # Midrib
                    draw.line([112, 40, 112, 170], fill=(20, 70, 20), width=2)
                
                # Add disease symptoms
                if "Bacterial_spot" in cls:
                    # Add small brown spots on the leaf
                    for _ in range(12):
                        x = random.randint(40, 180)
                        y = random.randint(60, 160)
                        r = random.randint(2, 5)
                        draw.ellipse([x-r, y-r, x+r, y+r], fill=(120, 60, 20))
                
                elif "Black_rot" in cls:
                    # Add larger black/decayed spots
                    for _ in range(3):
                        x = random.randint(50, 170)
                        y = random.randint(60, 160)
                        r = random.randint(12, 22)
                        draw.ellipse([x-r, y-r, x+r, y+r], fill=(15, 15, 15))
                        
                elif "Early_blight" in cls:
                    # Add target-like concentric rings/brown spots
                    for _ in range(4):
                        x = random.randint(50, 170)
                        y = random.randint(60, 160)
                        r = random.randint(8, 15)
                        # Concentric rings
                        draw.ellipse([x-r, y-r, x+r, y+r], fill=(139, 90, 43))
                        draw.ellipse([x-r+3, y-r+3, x+r-3, y+r-3], fill=leaf_color)
                        draw.ellipse([x-r+6, y-r+6, x+r-6, y+r-6], fill=(100, 60, 20))
                        
                elif "Late_blight" in cls:
                    # Add dark, water-soaked lesions that turn brown, with a light halo
                    for _ in range(3):
                        x = random.randint(50, 170)
                        y = random.randint(60, 160)
                        r = random.randint(15, 25)
                        # Pale halo
                        draw.ellipse([x-r, y-r, x+r, y+r], fill=(200, 220, 150))
                        # Brown center
                        draw.ellipse([x-r+4, y-r+4, x+r-4, y+r-4], fill=(80, 50, 20))

                elif "Apple_scab" in cls:
                    # Add olive-green/brown velvety spots
                    for _ in range(8):
                        x = random.randint(40, 180)
                        y = random.randint(60, 160)
                        r = random.randint(3, 8)
                        draw.ellipse([x-r, y-r, x+r, y+r], fill=(85, 107, 47))
                
                img.save(os.path.join(cls_dir, f"leaf_{i}.jpg"))
                
    if generated_any:
        print(f"Synthetic dataset generation complete! Images stored in: {dataset_dir}\n")
    else:
        print("All target class subdirectories are already populated.")

def train_model():
    dataset_dir = os.path.join(config.BASE_DIR, 'dataset', 'PlantVillage')
    
    # Check/generate synthetic dataset classes
    generate_synthetic_dataset(dataset_dir)

    # Data transformation and augmentation
    train_transforms = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406], 
            std=[0.229, 0.224, 0.225]
        )
    ])

    print("Loading dataset...")
    try:
        dataset = datasets.ImageFolder(dataset_dir, transform=train_transforms)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return

    classes = dataset.classes
    num_classes = len(classes)
    print(f"Classes found: {classes}")
    print(f"Total images: {len(dataset)}")

    # Ensure models directory exists
    os.makedirs(config.MODEL_DIR, exist_ok=True)

    # Save classes list
    import json
    with open(config.CLASSES_PATH, 'w') as f:
        json.dump(classes, f)
    print(f"Saved class names list to {config.CLASSES_PATH}")

    # Set up DataLoader
    batch_size = 8  # Small batch size to run fast on CPU/GPUs
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # Setup device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on device: {device}")

    # Load pre-trained MobileNetV2
    print("Downloading/Loading pre-trained MobileNetV2 model...")
    try:
        from torchvision.models import MobileNetV2_Weights
        model = models.mobilenet_v2(weights=MobileNetV2_Weights.DEFAULT)
    except ImportError:
        model = models.mobilenet_v2(pretrained=True)

    # Freeze feature layers (fine-tune only the classifier for speed)
    for param in model.features.parameters():
        param.requires_grad = False

    # Swap output layer
    model.classifier[1] = nn.Linear(model.last_channel, num_classes)
    model = model.to(device)

    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.classifier.parameters(), lr=0.001)

    # Training loop
    num_epochs = 5
    print(f"Starting training for {num_epochs} epochs...")
    model.train()

    for epoch in range(num_epochs):
        running_loss = 0.0
        corrects = 0
        total = 0
        
        for inputs, labels in dataloader:
            inputs, labels = inputs.to(device), labels.to(device)
            
            optimizer.zero_grad()
            
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * inputs.size(0)
            _, preds = torch.max(outputs, 1)
            corrects += torch.sum(preds == labels.data)
            total += inputs.size(0)
            
        epoch_loss = running_loss / total
        epoch_acc = corrects.double() / total
        print(f"Epoch {epoch+1}/{num_epochs} - Loss: {epoch_loss:.4f} - Acc: {epoch_acc:.4f}")

    print("Training finished.")
    
    # Save trained model weights
    torch.save(model.state_dict(), config.MODEL_PATH)
    print(f"Trained model weights saved to {config.MODEL_PATH}\n")

if __name__ == '__main__':
    train_model()
