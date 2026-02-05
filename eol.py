#!/usr/bin/env python3
"""
Software Inventory EOL Status Checker
Uses endoflife.date API to check EOL status of software in your inventory
"""

import csv
import requests
from datetime import datetime
from typing import List, Dict, Optional
import time


class EOLChecker:
    """Check End of Life status for software products"""

    BASE_URL = "https://endoflife.date/api"

    def __init__(self):
        self.cache = {}

    def get_product_info(self, product: str, version: Optional[str] = None) -> Optional[Dict]:
        cache_key = f"{product}:{version}" if version else product

        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            if version:
                url = f"{self.BASE_URL}/{product}/{version}.json"
            else:
                url = f"{self.BASE_URL}/{product}.json"

            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                self.cache[cache_key] = data
                return data
            elif response.status_code == 404:
                print(f"Product '{product}' not found in endoflife.date")
                return None
            else:
                print(f"Error fetching {product}: HTTP {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Network error for {product}: {e}")
            return None

    def find_best_match(self, product: str, version: str) -> Optional[Dict]:
        all_cycles = self.get_product_info(product)

        if not all_cycles or not isinstance(all_cycles, list):
            return None

        for cycle in all_cycles:
            if str(cycle.get("cycle", "")) == version:
                return cycle

        for cycle in all_cycles:
            cycle_version = str(cycle.get("cycle", ""))
            if (
                version.startswith(cycle_version + ".")
                or cycle_version.startswith(version + ".")
            ):
                return cycle

        return None

    def get_eol_status(self, product: str, version: str) -> Dict:
        info = self.find_best_match(product, version)

        if not info:
            return {
                "eol_date": "Unknown",
                "is_eol": "Unknown",
                "support_status": "Unknown",
                "days_until_eol": None,
                "lts": False,
                "latest_version": "Unknown",
            }

        eol_value = info.get("eol")
        support_value = info.get("support")

        today = datetime.now()
        is_eol = False
        eol_date = "Unknown"
        days_until_eol = None

        if eol_value is True:
            is_eol = True
            eol_date = "EOL"
            days_until_eol = 0

        elif eol_value is False:
            is_eol = False
            eol_date = "No EOL date set"

        elif isinstance(eol_value, str):
            try:
                eol_date_obj = datetime.strptime(eol_value, "%Y-%m-%d")
                eol_date = eol_value

                if eol_date_obj < today:
                    is_eol = True
                    days_until_eol = 0
                else:
                    is_eol = False
                    days_until_eol = (eol_date_obj - today).days

            except ValueError:
                eol_date = eol_value

        if support_value is False:
            return {
                "eol_date": eol_date,
                "is_eol": True,
                "support_status": "End of Support",
                "days_until_eol": 0,
                "lts": info.get("lts", False),
                "latest_version": info.get("latest", "Unknown"),
            }

        if is_eol:
            support_status = "End of Life"
        elif days_until_eol is not None:
            if days_until_eol < 90:
                support_status = "EOL Soon (<90 days)"
            elif days_until_eol < 180:
                support_status = "EOL Approaching (<6 months)"
            else:
                support_status = "Actively Supported"
        else:
            support_status = "Actively Supported"

        return {
            "eol_date": eol_date,
            "is_eol": is_eol,
            "support_status": support_status,
            "days_until_eol": days_until_eol,
            "lts": info.get("lts", False),
            "latest_version": info.get("latest", "Unknown"),
        }


class SoftwareInventory:
    """Manage software inventory with EOL checking"""

    def __init__(self, inventory_file: str):
        self.inventory_file = inventory_file
        self.inventory = []
        self.eol_checker = EOLChecker()

    def load_from_csv(self):
        try:
            with open(self.inventory_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.inventory = list(reader)
            print(f"Loaded {len(self.inventory)} items from {self.inventory_file}")
        except FileNotFoundError:
            print(f"File not found: {self.inventory_file}")
            self.inventory = []

    def create_sample_inventory(self):
        sample_data = [
            {"product": "python", "version": "3.9", "system": "Production Server 1", "criticality": "High"},
            {"product": "python", "version": "3.11", "system": "Development Server", "criticality": "Medium"},
            {"product": "nodejs", "version": "16", "system": "Web Application", "criticality": "High"},
            {"product": "ubuntu", "version": "20.04", "system": "Production Server 1", "criticality": "High"},
            {"product": "postgresql", "version": "12", "system": "Database Server", "criticality": "Critical"},
            {"product": "nginx", "version": "1.20", "system": "Load Balancer", "criticality": "High"},
        ]

        with open(self.inventory_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["product", "version", "system", "criticality"],
            )
            writer.writeheader()
            writer.writerows(sample_data)

        self.inventory = sample_data
        print(f"Created sample inventory: {self.inventory_file}")

    def check_all_eol_status(self) -> List[Dict]:
        results = []

        print(f"\nChecking EOL status for {len(self.inventory)} items...\n")

        for idx, item in enumerate(self.inventory, 1):
            product = item.get("product", "").lower().strip()
            version = item.get("version", "").strip()

            print(f"[{idx}/{len(self.inventory)}] Checking {product} {version}...")

            eol_status = self.eol_checker.get_eol_status(product, version)
            results.append({**item, **eol_status})

            time.sleep(0.5)

        return results

    def save_results(self, results: List[Dict], output_file: str):
        if not results:
            print("No results to save")
            return

        fieldnames = [
            "product",
            "version",
            "system",
            "criticality",
            "support_status",
            "eol_date",
            "is_eol",
            "days_until_eol",
            "lts",
            "latest_version",
        ]

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        print(f"Results saved to: {output_file}")

    def print_summary(self, results: List[Dict]):
        if not results:
            print("No results to summarize")
            return

        eol_count = sum(1 for r in results if r.get("is_eol") is True)
        eol_soon_count = sum(1 for r in results if "EOL Soon" in str(r.get("support_status", "")))
        supported_count = sum(1 for r in results if r.get("support_status") == "Actively Supported")

        print("\n" + "=" * 80)
        print("EOL STATUS SUMMARY")
        print("=" * 80)
        print(f"Total items checked: {len(results)}")
        print(f"End of Life: {eol_count}")
        print(f"EOL Soon (<90 days): {eol_soon_count}")
        print(f"Actively Supported: {supported_count}")
        print("=" * 80)

        critical_eol = [
            r for r in results
            if r.get("is_eol") is True
            and r.get("criticality", "").lower() in ["high", "critical"]
        ]

        if critical_eol:
            print("\nCRITICAL: High/Critical systems with EOL software:")
            for item in critical_eol:
                print(f"  - {item['product']} {item['version']} on {item['system']}")

        print()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Check EOL status of software inventory")
    parser.add_argument("--inventory", default="software_inventory.csv")
    parser.add_argument("--output", default="inventory_with_eol.csv")
    parser.add_argument("--create-sample", action="store_true")

    args = parser.parse_args()

    inventory = SoftwareInventory(args.inventory)

    if args.create_sample:
        inventory.create_sample_inventory()
        print("\nEdit the file and run again without --create-sample")
        return

    inventory.load_from_csv()

    if not inventory.inventory:
        print("\nNo inventory loaded. Use --create-sample to create one.")
        return

    results = inventory.check_all_eol_status()
    inventory.save_results(results, args.output)
    inventory.print_summary(results)

    print(f"\nReview the results in: {args.output}")


if __name__ == "__main__":
    main()
