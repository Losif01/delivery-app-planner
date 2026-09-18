import csv
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict

MAX_CAPACITY_KG = 10.0

@dataclass
class Delivery:
    id: int
    area: str
    priority: int
    weight: float

@dataclass
class Trip:
    trip_id: int
    deliveries: list[Delivery] = field(default_factory=list)
    total_weight: float = 0.0
    areas: set[str] = field(default_factory=set)

    def add(self, d: Delivery):
        self.deliveries.append(d)
        self.total_weight += d.weight
        self.areas.add(d.area)

def process_routes(filename: str):
    valid, skipped = [], []
    area_min_pri = defaultdict(lambda: float('inf'))

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                try:
                    d = Delivery(int(row['ID']), row['Area'].strip(), int(row['Priority']), float(row['Package Weight (kg)']))
                    if d.weight > MAX_CAPACITY_KG:
                        skipped.append(d)
                    else:
                        valid.append(d)
                        area_min_pri[d.area] = min(area_min_pri[d.area], d.priority)
                except (ValueError, KeyError) as e:
                    print(f"Warning: Skipping invalid row. Error: {e}")
    except FileNotFoundError:
        sys.exit(f"Error: File '{filename}' not found.")

    # Sort in one pass: Area's lowest priority -> Area name alphabetically -> Delivery priority
    valid.sort(key=lambda d: (area_min_pri[d.area], d.area, d.priority))

    trips, current = [], Trip(1)
    for d in valid:
        if current.total_weight + d.weight > MAX_CAPACITY_KG:
            trips.append(current)
            current = Trip(len(trips) + 1)
        current.add(d)

    if current.deliveries:
        trips.append(current)

    return trips, skipped

def output_results(trips: list[Trip], skipped: list[Delivery], out_file="output.json"):
    print("--- Delivery Route Plan ---")
    if not trips and not skipped:
        return print("No deliveries to process.")

    for t in trips:
        print(f"Trip {t.trip_id} | Areas: {', '.join(sorted(t.areas))} | Weight: {t.total_weight:.1f}kg")
        for d in t.deliveries:
            print(f"  - ID: {d.id} | Area: {d.area} | Priority: {d.priority} | Weight: {d.weight}kg")

    if skipped:
        print("\n--- Skipped Packages (Exceeds Capacity) ---")
        for d in skipped:
            print(f"  - ID: {d.id} | Area: {d.area} | Weight: {d.weight}kg (Max: {MAX_CAPACITY_KG}kg)")

    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump({
            "trips": [{
                "trip_id": t.trip_id,
                "areas": sorted(t.areas),
                "total_weight": t.total_weight,
                "deliveries": [asdict(d) for d in t.deliveries]
            } for t in trips],
            "skipped_packages": [asdict(d) for d in skipped]
        }, f, indent=4)
    print(f"\nDetailed route plan exported to {out_file}")

if __name__ == "__main__":
    file_path = sys.argv[1] if len(sys.argv) > 1 else "deliveries.csv"
    trips, skipped = process_routes(file_path)
    output_results(trips, skipped)
