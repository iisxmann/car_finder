#!/usr/bin/env python3
"""
Car Info Lookup - Generate detailed car information from analysis reports.

This script allows users to:
1. Browse existing analysis txt files from car_analyzer.py
2. Select one to explore in more detail
3. Extract the vehicle classification from the report
4. Look up matching vehicles in the local database (data/vehicles.json)
5. Use TinyLlama LLM to generate detailed, educational information
6. Save the enhanced report to a new txt file

Usage:
    python3 car_info_lookup.py                    # Interactive mode
    python3 car_info_lookup.py --file report.txt  # Analyze a specific file directly

Models used:
    - TinyLlama 1.1B Chat (offline LLM) for generating detailed car descriptions
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from llama_cpp import Llama


# Vehicle category keywords for matching against database models
CATEGORY_KEYWORDS = {
    "sports car": ["sport", "racing", "performance", "gt", "coupe", "brz", "gr86", "gt-r", "camaro", "mustang", "rs"],
    "convertible": ["convertible", "roadster", "spider", "mx-5", "miata"],
    "minibus": ["minibus", "van", "shuttle", "bus"],
    "passenger car": ["sedan", "hatchback", "saloon", "3 series", "5 series", "c-class", "e-class", "a4", "golf", "corolla", "camry", "civic", "accord", "focus", "mazda3"],
    "jeep": ["jeep", "suv", "offroad", "crossover", "x5", "gle", "q5", "rav4", "cr-v", "tucson", "sportage", "forester", "outback", "cx-5", "cx-60"],
    "limousine": ["limousine", "limo"],
    "minivan": ["minivan"],
    "trolleybus": ["trolleybus", "tram"],
    "streetcar": ["streetcar"],
    "electric": ["electric", "ev", "i4", "eqe", "e-tron", "id.4", "ioniq", "ev6", "leaf", "bolt", "mach-e"],
}


class CarInfoLookup:
    """Handles loading the database and generating detailed car information using TinyLlama."""

    def __init__(self):
        self.db: dict = {}
        self.llm: Optional[Llama] = None
        self._load_database()
        self._load_llm()

    def _load_database(self) -> None:
        """Load the vehicles database from JSON."""
        db_path = Path(__file__).parent / "data" / "vehicles.json"
        if not db_path.exists():
            raise FileNotFoundError(f"Vehicle database not found: {db_path}")

        with open(db_path, "r", encoding="utf-8") as f:
            self.db = json.load(f)

        print(f"✓ Loaded vehicle database with {len(self.db)} brands")

    def _load_llm(self) -> None:
        """Load the TinyLlama model for generating detailed descriptions."""
        print("Loading TinyLlama model (this may take a moment)...")

        model_path = "/opt/models/tinyllama/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
        if not Path(model_path).exists():
            raise FileNotFoundError(f"TinyLlama model not found at: {model_path}")

        self.llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_batch=128,
            verbose=False,
        )
        print("✓ TinyLlama loaded successfully\n")

    def find_matching_cars(self, classification: str) -> list[dict]:
        """
        Find cars in the database that match the given classification.

        Returns a list of matching cars with their specs.
        """
        classification_lower = classification.lower()
        matches = []

        # Get keywords for this category
        keywords = CATEGORY_KEYWORDS.get(classification_lower, [classification_lower])

        for brand, models in self.db.items():
            for model_name, specs in models.items():
                model_lower = model_name.lower()
                brand_lower = brand.lower()

                # Check if any keyword matches brand or model name
                for kw in keywords:
                    kw_lower = kw.lower()
                    if kw_lower in model_lower or kw_lower in brand_lower:
                        matches.append({
                            "brand": brand,
                            "model": model_name,
                            "engine": specs.get("engine", "N/A"),
                            "hp": specs.get("hp", "N/A"),
                            "fuel": specs.get("fuel", "N/A"),
                            "match_reason": f"Matched keyword '{kw}'"
                        })
                        break  # Don't add duplicates

        # Also add a few examples from each brand if we have few matches
        if len(matches) < 3:
            for brand, models in list(self.db.items())[:5]:
                for model_name, specs in list(models.items())[:2]:
                    entry = {
                        "brand": brand,
                        "model": model_name,
                        "engine": specs.get("engine", "N/A"),
                        "hp": specs.get("hp", "N/A"),
                        "fuel": specs.get("fuel", "N/A"),
                        "match_reason": "Sample vehicle from catalog"
                    }
                    if entry not in matches:
                        matches.append(entry)
                        if len(matches) >= 8:
                            break
                if len(matches) >= 8:
                    break

        return matches[:10]  # Limit to top 10

    def generate_detailed_info(self, classification: str, matching_cars: list[dict]) -> str:
        """
        Use TinyLlama to generate a detailed, educational description about the car type.
        """
        if self.llm is None:
            raise RuntimeError("LLM not loaded")

        # Build a context string with the database info
        car_list = "\n".join([
            f"- {car['brand']} {car['model']}: {car['engine']}, {car['hp']} hp, {car['fuel']}"
            for car in matching_cars[:6]
        ])

        prompt = f"""You are a helpful automotive expert. A user has an image classified as a "{classification}".

Here are some matching vehicles from our database:
{car_list}

Please provide a detailed, educational response that includes:
1. A brief explanation of what a {classification} is
2. Key characteristics and features of this type of vehicle
3. The main advantages and disadvantages
4. Notable examples or history if relevant

Be informative but concise. Use about 200-300 words."""

        # Generate response using TinyLlama
        output = self.llm(
            prompt,
            max_tokens=400,
            temperature=0.7,
            stop=["</s>", "User:", "Assistant:"],
        )

        response_text = output["choices"][0]["text"].strip()
        return response_text

    def parse_analysis_file(self, file_path: Path) -> dict:
        """
        Parse an analysis txt file to extract key information.
        Returns a dict with image name, classification, confidence, etc.
        """
        content = file_path.read_text(encoding="utf-8")

        result = {
            "file_path": str(file_path),
            "file_name": file_path.name,
            "image_name": None,
            "classification": None,
            "confidence": None,
            "raw_content": content,
        }

        # Extract image name
        img_match = re.search(r"Image:\s*([^\n]+)", content)
        if img_match:
            result["image_name"] = img_match.group(1).strip()

        # Extract the best vehicle match (classification)
        class_match = re.search(r"Best vehicle match:\s*([^(]+)\s*\(([^)]+)\)", content)
        if class_match:
            result["classification"] = class_match.group(1).strip()
            result["confidence"] = class_match.group(2).strip()

        # Fallback: look for "appears to show a X"
        if not result["classification"]:
            show_match = re.search(r"appears to show a\s+([a-zA-Z\s]+?)\s*\(", content, re.IGNORECASE)
            if show_match:
                result["classification"] = show_match.group(1).strip()

        return result


def list_txt_files(directory: Path) -> list[Path]:
    """List all txt files in a directory."""
    files = sorted([
        f for f in directory.iterdir()
        if f.is_file() and f.suffix.lower() == ".txt"
    ])
    return files


def interactive_mode(base_dir: Path) -> None:
    """Run the interactive txt file selection and detailed info generation."""
    lookup = CarInfoLookup()

    while True:
        txt_files = list_txt_files(base_dir)

        if not txt_files:
            print(f"\nNo txt files found in: {base_dir}")
            print("Run car_analyzer.py first to generate some analysis reports.")
            return

        print(f"\nAnalysis reports found in: {base_dir}")
        print("-" * 50)
        for i, f in enumerate(txt_files, 1):
            print(f"  [{i}] {f.name}")
        print("-" * 50)
        print("  [Q] Quit")
        print()

        choice = input("Select a report by number (or Q to quit): ").strip()

        if choice.lower() in ("q", "quit", "exit"):
            print("Goodbye!")
            return

        if not choice.isdigit():
            print("Please enter a valid number or Q to quit.")
            continue

        idx = int(choice)
        if idx < 1 or idx > len(txt_files):
            print(f"Please enter a number between 1 and {len(txt_files)}.")
            continue

        selected_file = txt_files[idx - 1]
        print(f"\nReading: {selected_file.name}...")
        print()

        # Parse the analysis file
        parsed = lookup.parse_analysis_file(selected_file)

        print(f"Image analyzed: {parsed.get('image_name', 'Unknown')}")
        classification = parsed.get("classification", "Unknown")
        confidence = parsed.get("confidence", "N/A")
        print(f"Classification: {classification} ({confidence})")
        print()

        # Find matching cars in the database
        print("Looking up matching vehicles in the database...")
        matching_cars = lookup.find_matching_cars(classification)

        if matching_cars:
            print(f"Found {len(matching_cars)} matching vehicles:")
            for car in matching_cars[:5]:
                print(f"  - {car['brand']} {car['model']} ({car['engine']}, {car['hp']} hp)")
        else:
            print("No direct matches found. Will include general catalog samples.")
        print()

        # Generate detailed info using TinyLlama
        print("Generating detailed information using TinyLlama...")
        print()

        try:
            detailed_text = lookup.generate_detailed_info(classification, matching_cars)

            # Build the final report
            report_lines = []
            report_lines.append("=" * 60)
            report_lines.append("DETAILED CAR INFORMATION REPORT")
            report_lines.append("=" * 60)
            report_lines.append("")
            report_lines.append(f"Source analysis: {selected_file.name}")
            report_lines.append(f"Original image: {parsed.get('image_name', 'Unknown')}")
            report_lines.append(f"Classification: {classification}")
            report_lines.append(f"Confidence: {confidence}")
            report_lines.append(f"Generated: {datetime.now().isoformat()}")
            report_lines.append("")
            report_lines.append("-" * 60)
            report_lines.append("MATCHING VEHICLES FROM DATABASE")
            report_lines.append("-" * 60)
            report_lines.append("")

            if matching_cars:
                for car in matching_cars:
                    report_lines.append(f"  • {car['brand']} {car['model']}")
                    report_lines.append(f"      Engine: {car['engine']}")
                    report_lines.append(f"      Power:  {car['hp']} hp")
                    report_lines.append(f"      Fuel:   {car['fuel']}")
                    report_lines.append("")
            else:
                report_lines.append("  No specific matches found in the catalog.")
                report_lines.append("")

            report_lines.append("-" * 60)
            report_lines.append("DETAILED DESCRIPTION (Generated by TinyLlama)")
            report_lines.append("-" * 60)
            report_lines.append("")
            report_lines.append(detailed_text)
            report_lines.append("")
            report_lines.append("=" * 60)
            report_lines.append("Report generated using: TinyLlama 1.1B + Local Vehicle Database")
            report_lines.append("=" * 60)

            report = "\n".join(report_lines)

            # Print to screen
            print(report)

            # Save to file
            output_dir = Path(__file__).parent / "analysis_output"
            output_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = selected_file.stem.replace(" ", "_")
            output_file = output_dir / f"detailed_{safe_name}_{timestamp}.txt"

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report)

            print(f"\n✓ Detailed report saved to: {output_file}")

        except Exception as e:
            print(f"\nError generating detailed info: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()

        print()
        again = input("Process another report? (y/n): ").strip().lower()
        if again not in ("y", "yes"):
            print("Goodbye!")
            return


def analyze_single_file(file_path: Path) -> None:
    """Analyze a single file non-interactively."""
    lookup = CarInfoLookup()

    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    print(f"\nReading: {file_path.name}...\n")

    parsed = lookup.parse_analysis_file(file_path)

    print(f"Image analyzed: {parsed.get('image_name', 'Unknown')}")
    classification = parsed.get("classification", "Unknown")
    confidence = parsed.get("confidence", "N/A")
    print(f"Classification: {classification} ({confidence})\n")

    print("Looking up matching vehicles in the database...")
    matching_cars = lookup.find_matching_cars(classification)

    if matching_cars:
        print(f"Found {len(matching_cars)} matching vehicles:")
        for car in matching_cars[:5]:
            print(f"  - {car['brand']} {car['model']} ({car['engine']}, {car['hp']} hp)")

    print("\nGenerating detailed information using TinyLlama...\n")

    try:
        detailed_text = lookup.generate_detailed_info(classification, matching_cars)

        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("DETAILED CAR INFORMATION REPORT")
        report_lines.append("=" * 60)
        report_lines.append("")
        report_lines.append(f"Source analysis: {file_path.name}")
        report_lines.append(f"Original image: {parsed.get('image_name', 'Unknown')}")
        report_lines.append(f"Classification: {classification}")
        report_lines.append(f"Confidence: {confidence}")
        report_lines.append(f"Generated: {datetime.now().isoformat()}")
        report_lines.append("")
        report_lines.append("-" * 60)
        report_lines.append("MATCHING VEHICLES FROM DATABASE")
        report_lines.append("-" * 60)
        report_lines.append("")

        if matching_cars:
            for car in matching_cars:
                report_lines.append(f"  • {car['brand']} {car['model']}")
                report_lines.append(f"      Engine: {car['engine']}")
                report_lines.append(f"      Power:  {car['hp']} hp")
                report_lines.append(f"      Fuel:   {car['fuel']}")
                report_lines.append("")

        report_lines.append("-" * 60)
        report_lines.append("DETAILED DESCRIPTION (Generated by TinyLlama)")
        report_lines.append("-" * 60)
        report_lines.append("")
        report_lines.append(detailed_text)
        report_lines.append("")
        report_lines.append("=" * 60)
        report_lines.append("Report generated using: TinyLlama 1.1B + Local Vehicle Database")
        report_lines.append("=" * 60)

        report = "\n".join(report_lines)
        print(report)

        output_dir = Path(__file__).parent / "analysis_output"
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = file_path.stem.replace(" ", "_")
        output_file = output_dir / f"detailed_{safe_name}_{timestamp}.txt"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"\n✓ Detailed report saved to: {output_file}")

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Car Info Lookup - Generate detailed car information from analysis reports using TinyLlama",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This tool reads analysis reports generated by car_analyzer.py and enriches them
with detailed information from the local vehicle database and the TinyLlama LLM.

Models used:
  - TinyLlama 1.1B Chat - Offline LLM for generating educational descriptions

Examples:
  python3 car_info_lookup.py                              # Interactive mode
  python3 car_info_lookup.py --file analysis_output/bw_20260402_234006.txt
        """
    )
    parser.add_argument(
        "--file", "-f",
        type=Path,
        help="Analyze a specific report file directly"
    )
    args = parser.parse_args()

    if args.file:
        analyze_single_file(args.file)
    else:
        base_dir = Path(__file__).parent / "analysis_output"
        interactive_mode(base_dir)


if __name__ == "__main__":
    main()
