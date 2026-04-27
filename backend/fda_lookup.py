import requests
import os

# OpenFDA base URL - this is a free public API, no key needed
FDA_BASE_URL = "https://api.fda.gov/drug"


def search_drug_info(medicine_name: str) -> dict:
    """
    Takes medicine name → calls OpenFDA API → returns drug info
    """
    try:
        # Search in drug label database
        url = f"{FDA_BASE_URL}/label.json"
        params = {
            "search": f"openfda.generic_name:{medicine_name}",
            "limit": 1  # we only need the top result
        }

        response = requests.get(url, params=params, timeout=10)

        # If not found by generic name, try brand name
        if response.status_code == 404:
            params["search"] = f"openfda.brand_name:{medicine_name}"
            response = requests.get(url, params=params, timeout=10)

        # If still not found
        if response.status_code == 404:
            return {
                "medicine_name": medicine_name,
                "found": False,
                "message": "Drug not found in FDA database"
            }

        response.raise_for_status()
        data = response.json()

        # Extract the first result
        result = data["results"][0]

        # Pull out the fields we care about
        drug_info = extract_relevant_fields(medicine_name, result)
        return drug_info

    except requests.exceptions.Timeout:
        return {
            "medicine_name": medicine_name,
            "found": False,
            "message": "FDA API request timed out"
        }
    except requests.exceptions.RequestException as e:
        return {
            "medicine_name": medicine_name,
            "found": False,
            "message": f"API error: {str(e)}"
        }
    except Exception as e:
        return {
            "medicine_name": medicine_name,
            "found": False,
            "message": f"Unexpected error: {str(e)}"
        }


def extract_relevant_fields(medicine_name: str, result: dict) -> dict:
    """
    FDA API returns a LOT of data — we extract only what matters
    """

    def get_first(field, default=None):
        """Helper: FDA fields are lists, we take first item only"""
        value = result.get(field, [])
        if isinstance(value, list) and len(value) > 0:
            # Truncate long text to 300 chars for readability
            text = value[0]
            return text[:300] + "..." if len(text) > 300 else text
        return default

    # Get brand and generic names from openfda section
    openfda = result.get("openfda", {})

    brand_names = openfda.get("brand_name", [])
    generic_names = openfda.get("generic_name", [])
    manufacturer = openfda.get("manufacturer_name", [])

    return {
        "medicine_name": medicine_name,
        "found": True,
        "brand_names": brand_names[:3] if brand_names else [],
        "generic_names": generic_names[:3] if generic_names else [],
        "manufacturer": manufacturer[0] if manufacturer else None,
        "purpose": get_first("purpose"),
        "warnings": get_first("warnings"),
        "side_effects": get_first("adverse_reactions"),
        "dosage_info": get_first("dosage_and_administration"),
        "interactions": get_first("drug_interactions"),
        "contraindications": get_first("contraindications"),
        "storage": get_first("storage_and_handling"),
    }


def lookup_all_medicines(medicines: list) -> list:
    """
    Takes list of medicine dicts from llm_parser
    Looks up each one and returns enriched list
    This is what main.py will call
    """
    enriched = []

    for medicine in medicines:
        name = medicine.get("name", "")
        if not name:
            continue

        print(f"  Looking up: {name}...")
        fda_info = search_drug_info(name)

        # Merge prescription info + FDA info
        enriched.append({
            "prescription_info": medicine,
            "fda_info": fda_info
        })

    return enriched


def format_fda_output(enriched_medicines: list) -> str:
    """
    Human readable summary of FDA lookups
    """
    lines = []

    for item in enriched_medicines:
        rx = item["prescription_info"]
        fda = item["fda_info"]

        lines.append("=" * 50)
        lines.append(f"💊 {rx.get('name', 'Unknown').upper()}")
        lines.append(f"   Dosage    : {rx.get('dosage', 'N/A')}")
        lines.append(f"   Frequency : {rx.get('frequency', 'N/A')}")
        lines.append(f"   Duration  : {rx.get('duration', 'N/A')}")
        lines.append("")

        if fda["found"]:
            lines.append(f"   📋 FDA Info:")
            if fda.get("brand_names"):
                lines.append(f"   Brand Names  : {', '.join(fda['brand_names'])}")
            if fda.get("purpose"):
                lines.append(f"   Purpose      : {fda['purpose']}")
            if fda.get("warnings"):
                lines.append(f"   ⚠️  Warnings  : {fda['warnings']}")
            if fda.get("side_effects"):
                lines.append(f"   Side Effects : {fda['side_effects']}")
            if fda.get("interactions"):
                lines.append(f"   Interactions : {fda['interactions']}")
        else:
            lines.append(f"   ℹ️  {fda['message']}")

        lines.append("")

    return "\n".join(lines)


# ── Quick test ────────────────────────────────────────
if __name__ == "__main__":

    # Test with medicines from our sample prescription
    test_medicines = [
        {
            "name": "Paracetamol",
            "dosage": "500mg",
            "frequency": "twice daily",
            "duration": "5 days",
            "instructions": "after food"
        },
        {
            "name": "Azithromycin",
            "dosage": "250mg",
            "frequency": "once daily",
            "duration": "3 days",
            "instructions": "after food"
        },
        {
            "name": "Cetirizine",
            "dosage": "10mg",
            "frequency": "at night",
            "duration": "7 days",
            "instructions": "before sleep"
        }
    ]

    print("Looking up medicines in FDA database...\n")
    enriched = lookup_all_medicines(test_medicines)

    print("\n" + format_fda_output(enriched))

    print("\nRAW JSON OUTPUT (first medicine):")
    import json
    print(json.dumps(enriched[0], indent=2))