import os
import cv2
import numpy as np
from sklearn import svm
from sklearn.model_selection import train_test_split
from tensorflow.keras.applications import VGG16
from tensorflow.keras.preprocessing.image import img_to_array, load_img
from tensorflow.keras.applications.vgg16 import preprocess_input
from PIL import Image

# Define the image path for testing
image_path = '../IMG_4476.JPG'  # Example image path

# Check if the image file exists
print(f"Image file exists: {os.path.exists(image_path)}")

# Load the VGG16 model (CNN) for feature extraction
model = VGG16(weights='imagenet', include_top=False, pooling='avg')

# Function to check if the file is an image
def is_image_file(filename):
    return filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))

# Function to extract features from images
def extract_features(image_path):
    try:
        # Load and preprocess the image
        img = load_img(image_path, target_size=(224, 224))  # Resize image to 224x224
        img_array = img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)  # Preprocess image for VGG16
        
        # Extract features
        features = model.predict(img_array)
        return features.flatten()  # Flatten the feature array
    
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None

# Function to load dataset
def load_dataset(data_dir):
    features = []
    labels = []
    print("Loading dataset from:", data_dir)
    
    # Check if dataset directory exists
    if not os.path.exists(data_dir):
        print(f"Dataset directory does not exist: {data_dir}")
        return np.array(features), np.array(labels)

    for label in os.listdir(data_dir):  # Loop through folders
        label_dir = os.path.join(data_dir, label)
        if not os.path.isdir(label_dir):
            continue  # Skip if it's not a directory

        print(f"Processing directory: {label_dir}")
        
        for img_file in os.listdir(label_dir):  # Loop through files in each folder
            if not is_image_file(img_file):
                continue  # Skip non-image files

            img_path = os.path.join(label_dir, img_file)
            print(f"Processing image: {img_path}")
            feature = extract_features(img_path)
            if feature is not None:  # Only append valid features
                features.append(feature)
                labels.append(label)

    return np.array(features), np.array(labels)

# Load the dataset
data_dir = '../Vehicle-Detection/dataset'  # Update with your dataset path
X, y = load_dataset(data_dir)

# Check if the dataset is loaded
if len(X) == 0 or len(y) == 0:
    print("Error: No data loaded. Check your dataset path and contents.")
    exit(1)

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the SVM classifier
svm_classifier = svm.SVC(kernel='linear', C=1.0)
svm_classifier.fit(X_train, y_train)  # Fit the model with training data

# Sliding window function
def sliding_window(image, step_size, window_size):
    for y in range(0, image.shape[0] - window_size[1], step_size):
        for x in range(0, image.shape[1] - window_size[0], step_size):
            yield (x, y, image[y:y + window_size[1], x:x + window_size[0]])

# Vehicle detection using sliding window and trained SVM
def detect_vehicles(image_path, model, svm_classifier, window_size=(224, 224), step_size=32):
    if not os.path.exists(image_path):
        print(f"Error: Image file {image_path} does not exist.")
        return 0

    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image {image_path}")
        return 0

    vehicle_count = 0

    for (x, y, window) in sliding_window(image, step_size, window_size):
        if window.shape[0] != window_size[1] or window.shape[1] != window_size[0]:
            continue

        img_array = cv2.resize(window, window_size)
        img_array = img_to_array(img_array)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)

        features = model.predict(img_array).flatten()

        prediction = svm_classifier.predict([features])[0]

        # Replace 'vehicle' with the correct class name or use the correct index
        if prediction == 'vehicle':  # Example: change based on your actual labels
            vehicle_count += 1
            cv2.rectangle(image, (x, y), (x + window_size[0], y + window_size[1]), (0, 255, 0), 2)

    cv2.imwrite('output_detection.jpg', image)  # Save the result image
    print(f"Total vehicles detected: {vehicle_count}")
    return vehicle_count

# Detect vehicles in the example image
detected_vehicles = detect_vehicles(image_path, model, svm_classifier)
print(f"Number of vehicles detected: {detected_vehicles}")
