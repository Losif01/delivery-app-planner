# Reasoning
## Usage:
```bash
git clone https://github.com/Losif01/delivery-app-planner
cd delivery-app-planner
python planner.py deliveries.csv
python planner.py empty.csv
```
no need to install any packages, the libs used are default python 

expected output:
```
--- Delivery Route Plan ---
Trip 1 | Areas: Heliopolis, Maadi | Weight: 8.5kg | Util: 85.0%
  - ID: 6 | Area: Heliopolis | Priority: 1 | Weight: 3.0kg
  - ID: 2 | Area: Maadi | Priority: 1 | Weight: 2.0kg
  - ID: 5 | Area: Maadi | Priority: 2 | Weight: 3.5kg
Trip 2 | Areas: Maadi | Weight: 8.0kg | Util: 80.0%
  - ID: 7 | Area: Maadi | Priority: 2 | Weight: 8.0kg
Trip 3 | Areas: Zamalek | Weight: 9.0kg | Util: 90.0%
  - ID: 4 | Area: Zamalek | Priority: 1 | Weight: 7.0kg
  - ID: 10 | Area: Zamalek | Priority: 3 | Weight: 2.0kg
Trip 4 | Areas: Nasr City | Weight: 4.5kg | Util: 45.0%
  - ID: 1 | Area: Nasr City | Priority: 2 | Weight: 4.5kg
Trip 5 | Areas: Nasr City | Weight: 7.2kg | Util: 72.0%
  - ID: 9 | Area: Nasr City | Priority: 2 | Weight: 6.0kg
  - ID: 3 | Area: Nasr City | Priority: 3 | Weight: 1.2kg

--- Fleet Analytics ---
Total Trips: 5
Average Fleet Utilization: 74.4%

--- Skipped Packages (Exceeds Capacity) ---
  - ID: 8 | Area: Dokki | Weight: 12.5kg (Max: 10.0kg)

Detailed route plan exported to output.json
--- Delivery Route Plan ---
No deliveries to process.
```
## 1- Approach:
first of all, we have *requirements* as follows: 

```
Each delivery has an ID, area, priority, and package weight.
A vehicle can carry a maximum of 10 kg per trip.
A trip must never exceed the vehicle capacity.
Deliveries going to the same area should be grouped together where reasonably possible.
Lower priority numbers represent more urgent deliveries and should be handled first.
Every valid delivery must appear in exactly one trip.
```

the problem is basically just sorting, finding the best way to sort solves it (according to the problem statement)
**a greedy approach shall be used!**
1. sort by minimum priority
2. sort by area
3. sort in the same area by priority feature (this was not required and this is what i added)

 "deliveries to the same area should be grouped" AND "lower priority numbers are handled first," the algorithm sorts the entire list of valid deliveries in one pass using a 3-part tuple key: `(area_min_pri[d.area], d.area, d.priority)`.

- **First Sort (`area_min_pri`):** areas that contain highly urgent packages are routed first. This ensures an area with a Priority 1 package is processed before an area whose most urgent package is Priority 3.
    
- **Second Sort (`d.area`):** if two areas have the same urgency score, they are sorted alphabetically. This forces all packages for a specific area to cluster perfectly together in the list, satisfying the geographical grouping requirement.
    
- **Third Sort (`d.priority`):** within a specific area's cluster, the individual packages are ordered from most urgent to least urgent.

**Greedy Trip Assembly** With the data ==perfectly sequenced==, the algorithm uses a "greedy" packing method. It iterates through the sorted list and adds packages one by one to the current `Trip`. Because the list is already sorted by area, packages for the same neighborhood will naturally flow into the same truck. The moment adding a package would exceed the 10kg threshold, the algorithm "seals" the current trip and opens a new one, continuing exactly where it left off.

### IMPORTANT NOTES
there exists only 1 sort as per problem description, first and second sort are actually grouped in one sort and they are not separate.
the other sort is a feature for priority in the same area
**I deliberately wrote the solution to be simple and readable as much as possible**

### Features that were not asked
- **Intra-Trip Sequencing:** Sorting items _within_ the trip by priority perfectly aligns with a driver's trip (handing out the most urgent package first upon arrival).

- **Business Intelligence:** Fleet utilization metrics (85%, 90%, etc.) provide data for operations teams to monitor truck efficiency, another attribute to take into account when grouping too
## 2- most difficult part
**Balancing competing heuristics...**

strict capacity limits vs. priority routing vs. geographical grouping. The problem requires that deliveries to the same area be "grouped together where reasonably possible" while also ensuring "lower priority numbers are handled first." Deciding how to weight these variables, creating a composite sort key `(minimum_area_priority, area_name, delivery_priority)`... this was the most challenging architectural decision. It required balancing driver efficiency (not bouncing between cities) with urgency.

## 3- situations where this algorithm may not produce the best possible grouping

because the algorithm uses a greedy, chronological approach based on pre sorted data, it fails to optimize for maximum weight capacity (the 1D Bin Packing problem).

_Example:_ A truck has a 10kg capacity. We have three packages for Maadi: 6kg, 5kg, and 4kg (all same priority).
The algorithm evaluates them in order.
It adds the 6kg package.
It checks the 5kg package, sees it exceeds the 10kg limit, and pushes it to a new truck.
It then evaluates the 4kg package and pushes _that_ to the second truck as well.

_Result:_ Trip 1 is 6kg (60% full). Trip 2 is 9kg (90% full).
A better weight-packing algorithm (like First-Fit Decreasing) would have combined the 6kg and 4kg packages for 100% utilization, but our strict sequence grouping misses this optimization.

## 4- If the input contained 1,000,000 delivery requests, what part of the solution might become slow or memory-intensive?
- **Memory Bottleneck (RAM):** The program loads all data into RAM at once. Creating 1,000,000 `Delivery` Python objects will consume hundreds of megabytes. Furthermore, during the JSON export, the line `[asdict(d) for d in t.deliveries]` duplicates the entire dataset into a massive nested dictionary buffer before writing to disk, which could cause an OOM crash on constrained systems.
- **CPU Bottleneck:** While $\mathcal{O}(N \log N)$ sorting is highly efficient, sorting 1,000,000 Python objects by a tuple key will cause a noticeable CPU spike.
- **How to scale this solution:** We would need to move away from python lists and utilize a database (like PostgreSQL/SQLite) to group and index by area/priority using SQL queries, processing the output in manageable chunks (e.g., streaming the JSON to disk iteratively rather than dumping a single massive dictionary).

## 5- if i had to work another day on it i would...
implement everything from 4, plus figuring out ways to rewrite the same solution and follow as much SWE best practices as timely possible, like single priority functions and using suitable design patterns for it to integrate with an existing system, and finally make a simple UI, i don't like to overcomplicate things, i like to keep it simple to avoid bugs, which is why the current solutions just delivers what it is supposed to do, nothing else.
