# Car Finder

A PHP CLI application that lets you search a local JSON vehicle catalog by brand and model, returning detailed specifications such as engine type, horsepower, and fuel type.

---

## Requirements

- PHP 8.1 or higher (tested on PHP 8.2)
- No external dependencies or Composer required

---

## Project Structure

```
car_finder/
├── data/
│   └── vehicles.json       # JSON vehicle catalog (20 brands, 4 models each)
├── autoload.php            # PSR-4-style autoloader for the CarFinder\ namespace
├── carfinder.php           # CLI entry point
├── Config.php              # Project paths and runtime configuration
├── CatalogException.php    # Exception thrown on catalog errors
├── VehicleSpec.php         # Immutable DTO holding vehicle specifications
├── JsonCarRepository.php   # Reads and queries the JSON data file
├── CatalogService.php      # High-level service (brands, models, vehicle lookup)
├── Terminal.php            # stdin / stdout helpers
└── CarFinderApp.php        # Interactive CLI flow controller
```

---

## Installation

Clone or download the project, then navigate to the project root — no additional setup is required.

```bash
cd car_finder
```

---

## Usage

Run the entry point from the project root:

```bash
php carfinder.php
```

### Interactive flow

1. A numbered list of all **20 brands** is displayed.
2. Enter a brand by **number** or by **name** (case-insensitive, partial match supported).
3. A numbered list of **models** for that brand is displayed.
4. Enter a model by **number** or by **name**.
5. The vehicle specification is printed.
6. The brand list reappears — repeat or quit.

### Example session

```
=== Car Finder (JSON catalog) ===
Type a brand name or number from the list. Commands: quit, exit, q

Available brands:
  [1] Audi
  [2] BMW
  ...
  [20] Volvo

Brand> 2

Models for BMW:
  [1] 3 Series
  [2] 5 Series
  [3] X5
  [4] i4

Model> 1

--- Vehicle details ---
Brand : BMW
Model : 3 Series
Engine: 2.0L Turbo
Power : 184 hp
Fuel  : Petrol
-----------------------
```

### Quit

Type `q`, `quit`, or `exit` at any prompt to exit the application.

---

## Data

The catalog lives in `data/vehicles.json`. Each brand contains models with the following fields:

| Field    | Description                              |
|----------|------------------------------------------|
| `engine` | Engine displacement and type             |
| `hp`     | Horsepower output                        |
| `fuel`   | Fuel type (Petrol, Diesel, Hybrid, etc.) |

### Example entry

```json
{
  "BMW": {
    "3 Series": {
      "engine": "2.0L Turbo",
      "hp": "184",
      "fuel": "Petrol"
    }
  }
}
```

### Brands included

Audi, BMW, Chevrolet, Fiat, Ford, Honda, Hyundai, Jaguar, Kia, Land Rover, Mazda, Mercedes-Benz, Nissan, Peugeot, Renault, Subaru, Tesla, Toyota, Volkswagen, Volvo

---

## Architecture

| Layer | File(s) | Responsibility |
|-------|---------|----------------|
| Entry | `carfinder.php` | Bootstraps the app, wires dependencies |
| Loader | `autoload.php` | Resolves `CarFinder\*` class names to files |
| Config | `Config.php` | Centralises path resolution |
| Model | `VehicleSpec.php` | Typed, immutable value object |
| Repository | `JsonCarRepository.php` | Reads JSON, normalises data, resolves brand/model keys case-insensitively |
| Service | `CatalogService.php` | Provides sorted brand/model lists and hydrated `VehicleSpec` objects |
| CLI | `Terminal.php`, `CarFinderApp.php` | Handles I/O and the interactive loop |
| Error | `CatalogException.php` | Single exception type for all data errors |

---

## Extending the catalog

Open `data/vehicles.json` and add a new brand or model following the existing structure. No code changes are needed.


