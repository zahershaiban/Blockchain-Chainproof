# Imports json so training configuration can be saved as a JSON file.
import json
# Imports Path to build safe file paths.
from pathlib import Path

# Imports joblib to save the trained scikit-learn model to disk.
import joblib
# Imports pandas to load and manipulate the CSV dataset.
import pandas as pd
# Imports ColumnTransformer to apply different preprocessing to categorical and numeric columns.
from sklearn.compose import ColumnTransformer
# Imports RandomForestClassifier as the machine-learning model used in this project.
from sklearn.ensemble import RandomForestClassifier
# Imports accuracy_score to evaluate the model after training.
from sklearn.metrics import accuracy_score
# Imports train_test_split to split the dataset into training and testing parts.
from sklearn.model_selection import train_test_split
# Imports Pipeline to combine preprocessing and model training into one object.
from sklearn.pipeline import Pipeline
# Imports OneHotEncoder to convert text categories into numeric columns for the model.
from sklearn.preprocessing import OneHotEncoder


# Finds the main chainproof/ project folder by going one level above backend/.
BASE_DIR = Path(__file__).resolve().parent.parent
# Points to the health dataset used for model training.
DATASET_PATH = BASE_DIR / "data" / "health_dataset_1000.csv"
# Points to the artifacts folder where model.pkl and config.json are saved.
ARTIFACTS_DIR = BASE_DIR / "artifacts"

# Defines the output path for the trained model file.
MODEL_PATH = ARTIFACTS_DIR / "model.pkl"
# Defines the output path for the training configuration file.
CONFIG_PATH = ARTIFACTS_DIR / "config.json"


# Main training function for the Health Risk Classifier.
def main():
    # Creates the artifacts folder if it does not already exist.
    ARTIFACTS_DIR.mkdir(exist_ok=True)

    # Reads the health dataset into a pandas DataFrame.
    df = pd.read_csv(DATASET_PATH)

    # Sets the prediction target to the risk_level column.
    target_column = "risk_level"

    # Lists columns that should not be used as input features.
    drop_columns = [
        # Removes patient_id because it is an identifier, not a medical feature.
        "patient_id",
        # Removes audit_record_id because it is an audit identifier, not a medical feature.
        "audit_record_id",
        # Removes created_at because the date is not needed for this simple model.
        "created_at",
        # Removes the target column from the input features to avoid data leakage.
        "risk_level",
    ]

    # Creates the feature matrix by dropping identifiers and the target column.
    X = df.drop(columns=drop_columns)
    # Creates the target vector that the model will learn to predict.
    y = df[target_column]

    # Lists text/category columns that need one-hot encoding.
    categorical_features = [
        # Patient gender category.
        "gender",
        # Smoker status category.
        "smoker",
        # Family history category.
        "family_history",
        # Medication adherence category.
        "medication_adherence",
        # Diagnosis category.
        "diagnosis",
    ]

    # Lists numeric columns that can pass directly into the model.
    numeric_features = [
        # Patient age.
        "age",
        # Body mass index.
        "bmi",
        # Systolic blood pressure.
        "systolic_bp",
        # Diastolic blood pressure.
        "diastolic_bp",
        # Cholesterol measurement.
        "cholesterol_mg_dl",
        # Glucose measurement.
        "glucose_mg_dl",
        # Weekly exercise hours.
        "exercise_hours_week",
        # Number of previous hospitalizations.
        "previous_hospitalizations",
    ]

    # Creates a preprocessing object that handles categorical and numeric columns differently.
    preprocessor = ColumnTransformer(
        # Defines the preprocessing transformations.
        transformers=[
            # One-hot encodes categorical columns and ignores unseen categories during prediction.
            ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical_features),
            # Passes numeric columns through without transformation.
            ("numeric", "passthrough", numeric_features),
        ]
    )

    # Creates the Random Forest classifier used for risk-level prediction.
    model = RandomForestClassifier(
        # Uses 100 decision trees inside the forest.
        n_estimators=100,
        # Sets random_state for repeatable training results.
        random_state=42
    )

    # Combines preprocessing and the model into one reusable pipeline.
    pipeline = Pipeline(
        # Defines the ordered steps of the machine-learning workflow.
        steps=[
            # First step: transform raw columns into numeric features.
            ("preprocessor", preprocessor),
            # Second step: train/predict with the Random Forest model.
            ("model", model),
        ]
    )

    # Splits the dataset into training and testing sets.
    X_train, X_test, y_train, y_test = train_test_split(
        # Feature matrix to split.
        X,
        # Target labels to split.
        y,
        # Uses 20% of the data for testing.
        test_size=0.2,
        # Sets random_state for repeatable splitting.
        random_state=42,
        # Keeps similar class proportions in train and test sets.
        stratify=y
    )

    # Trains the full pipeline on the training data.
    pipeline.fit(X_train, y_train)

    # Predicts risk levels for the test features.
    predictions = pipeline.predict(X_test)
    # Calculates model accuracy by comparing predictions with the true test labels.
    accuracy = accuracy_score(y_test, predictions)

    # Saves the trained pipeline to artifacts/model.pkl.
    joblib.dump(pipeline, MODEL_PATH)

    # Creates a training configuration record for auditing and reproducibility.
    config = {
        # Project name.
        "project": "ChainProof",
        # Human-readable model name.
        "model_name": "Health Risk Classifier",
        # Model version.
        "version": "1.0.0",
        # Dataset used for training.
        "dataset": "health_dataset_1000.csv",
        # Target column predicted by the model.
        "target_column": target_column,
        # Machine-learning algorithm used.
        "algorithm": "RandomForestClassifier",
        # Number of trees in the Random Forest.
        "n_estimators": 100,
        # Random seed used by the model.
        "random_state": 42,
        # Fraction of data used for testing.
        "test_size": 0.2,
        # Test accuracy achieved after training.
        "accuracy": accuracy,
        # Feature lists used by the model.
        "features": {
            # Categorical feature names.
            "categorical": categorical_features,
            # Numeric feature names.
            "numeric": numeric_features
        }
    }

    # Opens artifacts/config.json for writing.
    with open(CONFIG_PATH, "w", encoding="utf-8") as file:
        # Saves the training configuration as readable JSON.
        json.dump(config, file, indent=4)

    # Prints a success message.
    print("Model trained successfully.")
    # Prints where the model was saved.
    print("Model saved to:", MODEL_PATH)
    # Prints where the config was saved.
    print("Config saved to:", CONFIG_PATH)
    # Prints the model accuracy.
    print("Accuracy:", accuracy)


# Runs main() only when this file is executed directly.
if __name__ == "__main__":
    # Starts the model training workflow.
    main()
