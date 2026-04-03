#!/usr/bin/env python3
"""
Car Analyzer - Offline image-based car detection and classification.

This script allows users to:
1. Browse images in a directory
2. Select an image to analyze
3. Detect if there's a car in the image (using YOLOv8)
4. Classify the type of vehicle (using EfficientNet-B0)
5. Save detailed analysis results to a text file

Usage:
    python3 car_analyzer.py                    # Interactive mode (uses ./sample_images/)
    python3 car_analyzer.py --dir /path/to/images
    python3 car_analyzer.py --image /path/to/photo.jpg

Models used:
    - YOLOv8n (yolov8n.pt) for object detection (detects cars in images)
    - EfficientNet-B0 for image classification (identifies car type)
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import torch
from PIL import Image
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights
from ultralytics import YOLO


# Vehicle-related class names from YOLOv8 COCO dataset
VEHICLE_CLASSES = {"car", "bus", "truck", "motorcycle"}

# Vehicle-related categories from ImageNet (EfficientNet)
VEHICLE_CATEGORIES = {
    "ambulance", "convertible", "fire engine", "freight car", "garbage truck",
    "golfcart", "jeep", "limousine", "minibus", "minivan", "moving van",
    "passenger car", "police van", "recreational vehicle", "school bus",
    "sports car", "streetcar", "tow truck", "trailer truck", "trolleybus"
}


class CarAnalyzer:
    """Handles car detection and classification using offline ML models."""

    def __init__(self):
        self.yolo_model: Optional[YOLO] = None
        self.efficientnet_model = None
        self.efficientnet_weights = None
        self._load_models()

    def _load_models(self) -> None:
        """Load both YOLO and EfficientNet models."""
        print("Loading offline AI models...")

        # Load YOLOv8 for object detection
        yolo_path = Path(__file__).parent / "yolov8n.pt"
        if yolo_path.exists():
            self.yolo_model = YOLO(str(yolo_path))
            print("  ✓ YOLOv8n loaded (for car detection)")
        else:
            print("  ⚠ YOLOv8n not found locally, downloading...")
            self.yolo_model = YOLO("yolov8n.pt")
            print("  ✓ YOLOv8n loaded (for car detection)")

        # Load EfficientNet-B0 for classification
        self.efficientnet_weights = EfficientNet_B0_Weights.DEFAULT
        self.efficientnet_model = efficientnet_b0(weights=self.efficientnet_weights)
        self.efficientnet_model.eval()
        print("  ✓ EfficientNet-B0 loaded (for car classification)")

        print("All models ready!\n")

    def detect_cars(self, image_path: Path) -> dict:
        """
        Use YOLOv8 to detect if there's a car in the image.

        Returns a dict with detection results including:
        - has_car: bool indicating if a vehicle was found
        - detections: list of detected vehicles with confidence scores
        """
        if self.yolo_model is None:
            raise RuntimeError("YOLO model not loaded")

        results = self.yolo_model(str(image_path), verbose=False)[0]

        detections = []
        has_car = False

        for box in results.boxes:
            cls_id = int(box.cls[0])
            class_name = self.yolo_model.names[cls_id]
            confidence = float(box.conf[0])

            if class_name in VEHICLE_CLASSES:
                has_car = True
                detections.append({
                    "type": class_name,
                    "confidence": confidence,
                    "bbox": [int(x) for x in box.xyxy[0].tolist()]
                })

        return {
            "has_car": has_car,
            "detections": detections,
            "total_objects_detected": len(results.boxes)
        }

    def classify_car(self, image_path: Path, top_k: int = 5) -> dict:
        """
        Use EfficientNet-B0 to classify what type of car/vehicle is in the image.

        Returns top-k predictions with confidence scores.
        """
        if self.efficientnet_model is None or self.efficientnet_weights is None:
            raise RuntimeError("EfficientNet model not loaded")

        # Load and preprocess the image
        img = Image.open(image_path).convert("RGB")
        preprocess = self.efficientnet_weights.transforms()
        input_tensor = preprocess(img).unsqueeze(0)

        # Run inference
        with torch.no_grad():
            output = self.efficientnet_model(input_tensor)

        # Convert to probabilities
        probabilities = torch.nn.functional.softmax(output[0], dim=0)
        top_prob, top_catid = torch.topk(probabilities, top_k)

        predictions = []
        for i in range(top_prob.size(0)):
            label = self.efficientnet_weights.meta["categories"][top_catid[i]]
            confidence = top_prob[i].item()
            is_vehicle_related = label.lower() in VEHICLE_CATEGORIES

            predictions.append({
                "label": label,
                "confidence": confidence,
                "is_vehicle_related": is_vehicle_related
            })

        return {
            "predictions": predictions,
            "top_vehicle_prediction": next(
                (p for p in predictions if p["is_vehicle_related"]), None
            )
        }

    def analyze_image(self, image_path: Path) -> dict:
        """
        Full analysis pipeline: detect cars first, then classify if found.
        """
        result = {
            "image_path": str(image_path),
            "image_name": image_path.name,
            "timestamp": datetime.now().isoformat(),
            "detection": None,
            "classification": None,
            "summary": ""
        }

        # Step 1: Detect if there's a car in the picture
        detection_result = self.detect_cars(image_path)
        result["detection"] = detection_result

        if not detection_result["has_car"]:
            result["summary"] = (
                f"No vehicle detected in '{image_path.name}'. "
                f"The image contains {detection_result['total_objects_detected']} object(s), "
                f"none of which are recognized as cars, buses, trucks, or motorcycles."
            )
            return result

        # Step 2: Classify the car type
        classification_result = self.classify_car(image_path)
        result["classification"] = classification_result

        # Build a human-readable summary
        vehicle_types = [d["type"] for d in detection_result["detections"]]
        vehicle_count = len(vehicle_types)

        top_class = classification_result.get("top_vehicle_prediction")
        if top_class:
            summary = (
                f"Found {vehicle_count} vehicle(s) in '{image_path.name}': "
                f"{', '.join(set(vehicle_types))}. "
                f"The image appears to show a {top_class['label']} "
                f"({top_class['confidence']:.1%} confidence)."
            )
        else:
            summary = (
                f"Found {vehicle_count} vehicle(s) in '{image_path.name}': "
                f"{', '.join(set(vehicle_types))}. "
                f"Classification suggests this may be a general vehicle scene."
            )

        result["summary"] = summary
        return result

    def generate_report(self, analysis: dict) -> str:
        """Generate a formatted text report from the analysis results."""
        lines = []
        lines.append("=" * 60)
        lines.append("CAR ANALYSIS REPORT")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"Image: {analysis['image_name']}")
        lines.append(f"Analyzed: {analysis['timestamp']}")
        lines.append(f"Full path: {analysis['image_path']}")
        lines.append("")

        # Detection section
        lines.append("-" * 60)
        lines.append("STEP 1: VEHICLE DETECTION")
        lines.append("-" * 60)
        lines.append("")

        detection = analysis["detection"]
        if detection["has_car"]:
            lines.append("✓ Vehicle(s) detected in the image!")
            lines.append("")
            lines.append(f"  Total objects found: {detection['total_objects_detected']}")
            lines.append(f"  Vehicles identified: {len(detection['detections'])}")
            lines.append("")
            lines.append("  Detected vehicles:")
            for i, det in enumerate(detection["detections"], 1):
                lines.append(
                    f"    {i}. {det['type'].upper()} - "
                    f"{det['confidence']:.1%} confidence"
                )
        else:
            lines.append("✗ No vehicle detected in this image.")
            lines.append("")
            lines.append("  The image does not appear to contain any cars,")
            lines.append("  buses, trucks, or motorcycles.")

        lines.append("")

        # Classification section (only if car was detected)
        if detection["has_car"] and analysis["classification"]:
            lines.append("-" * 60)
            lines.append("STEP 2: CAR CLASSIFICATION")
            lines.append("-" * 60)
            lines.append("")

            classification = analysis["classification"]
            lines.append("Top predictions from EfficientNet-B0:")
            lines.append("")

            for i, pred in enumerate(classification["predictions"], 1):
                vehicle_marker = " [VEHICLE]" if pred["is_vehicle_related"] else ""
                lines.append(
                    f"  {i}. {pred['label']:<25} {pred['confidence']:>7.2%}{vehicle_marker}"
                )

            top_vehicle = classification.get("top_vehicle_prediction")
            if top_vehicle:
                lines.append("")
                lines.append(
                    f"Best vehicle match: {top_vehicle['label']} "
                    f"({top_vehicle['confidence']:.1%})"
                )

        lines.append("")
        lines.append("-" * 60)
        lines.append("SUMMARY")
        lines.append("-" * 60)
        lines.append("")
        lines.append(analysis["summary"])
        lines.append("")
        lines.append("=" * 60)
        lines.append("Analysis complete. Models used: YOLOv8n + EfficientNet-B0")
        lines.append("=" * 60)

        return "\n".join(lines)


def list_images(directory: Path) -> list[Path]:
    """List all supported image files in a directory."""
    extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
    images = sorted([
        f for f in directory.iterdir()
        if f.is_file() and f.suffix.lower() in extensions
    ])
    return images


def interactive_mode(base_dir: Path) -> None:
    """Run the interactive image selection and analysis workflow."""
    analyzer = CarAnalyzer()

    while True:
        # List images in the directory
        images = list_images(base_dir)

        if not images:
            print(f"\nNo images found in: {base_dir}")
            print("Please add some images (.jpg, .png, etc.) to this folder and try again.")
            return

        print(f"\nImages found in: {base_dir}")
        print("-" * 50)
        for i, img in enumerate(images, 1):
            print(f"  [{i}] {img.name}")
        print("-" * 50)
        print("  [Q] Quit")
        print()

        # Get user selection
        choice = input("Select an image by number (or Q to quit): ").strip()

        if choice.lower() in ("q", "quit", "exit"):
            print("Goodbye!")
            return

        if not choice.isdigit():
            print("Please enter a valid number or Q to quit.")
            continue

        idx = int(choice)
        if idx < 1 or idx > len(images):
            print(f"Please enter a number between 1 and {len(images)}.")
            continue

        selected_image = images[idx - 1]
        print(f"\nAnalyzing: {selected_image.name}...")
        print()

        # Run the analysis
        try:
            analysis = analyzer.analyze_image(selected_image)
            report = analyzer.generate_report(analysis)

            # Print to screen
            print(report)

            # Save to file
            output_dir = Path(__file__).parent / "analysis_output"
            output_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = selected_image.stem.replace(" ", "_")
            output_file = output_dir / f"{safe_name}_{timestamp}.txt"

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report)

            print(f"\n✓ Report saved to: {output_file}")

        except Exception as e:
            print(f"\nError analyzing image: {e}", file=sys.stderr)

        # Ask if user wants to analyze another image
        print()
        again = input("Analyze another image? (y/n): ").strip().lower()
        if again not in ("y", "yes"):
            print("Goodbye!")
            return


def analyze_single_image(image_path: Path) -> None:
    """Analyze a single image non-interactively and print the report."""
    analyzer = CarAnalyzer()

    if not image_path.exists():
        print(f"Error: Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    print(f"\nAnalyzing: {image_path.name}...\n")

    analysis = analyzer.analyze_image(image_path)
    report = analyzer.generate_report(analysis)

    print(report)

    # Save to file
    output_dir = Path(__file__).parent / "analysis_output"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = image_path.stem.replace(" ", "_")
    output_file = output_dir / f"{safe_name}_{timestamp}.txt"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n✓ Report saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Car Analyzer - Detect and classify vehicles in images using offline AI models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Models used:
  1. YOLOv8n (yolov8n.pt) - Object detection to identify if a car is present
  2. EfficientNet-B0 - Image classification to determine the type of vehicle

Examples:
  python3 car_analyzer.py                           # Interactive mode
  python3 car_analyzer.py --dir ./my_photos         # Use a custom image directory
  python3 car_analyzer.py --image ./photo.jpg       # Analyze a single image
        """
    )
    parser.add_argument(
        "--dir", "-d",
        type=Path,
        default=Path(__file__).parent / "sample_images",
        help="Directory containing images to browse (default: ./sample_images/)"
    )
    parser.add_argument(
        "--image", "-i",
        type=Path,
        help="Analyze a single image directly without interactive selection"
    )
    args = parser.parse_args()

    if args.image:
        analyze_single_image(args.image)
    else:
        interactive_mode(args.dir)


if __name__ == "__main__":
    main()
