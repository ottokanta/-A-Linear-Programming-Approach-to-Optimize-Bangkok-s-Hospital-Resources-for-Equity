import pulp
import pandas as pd
import numpy as np
import math

def solve_hospital_allocation():
    #Read data from csv files
    print("Reading data from CSV files.")
    hospitals_df = pd.read_csv('Research Dataset (for Optimization) - Hospitals.csv')
    districts_df = pd.read_csv('Research Dataset (for Optimization) - Districts.csv')
    distances_df = pd.read_csv('Research Dataset (for Optimization) - Distances.csv')

    #Create sets for optimization
    H = hospitals_df['Hospital ID'].tolist()
    D = districts_df['District ID'].tolist()

    #Create parameter dictionaries for the hospitals and districts
    pop = dict(zip(districts_df['District ID'], districts_df['Population']))
    CVI = dict(zip(districts_df['District ID'], districts_df['Composite Vulnerability Index']))
    current_doctors = dict(zip(hospitals_df['Hospital ID'], hospitals_df['Doctor Count']))
    current_beds = dict(zip(hospitals_df['Hospital ID'], hospitals_df['Inpatient Beds'])) 
    dist = {}
    for _, row in distances_df.iterrows():
        h = row['Hospital ID']
        d = row['District ID']
        distance = row['Distance (km)']
        dist[(h,d)] = distance #Store it

    # Create ownership dictionary (1 for public, 0 for private)
    is_public = {}
    for _, row in hospitals_df.iterrows():
        h = row['Hospital ID']
        ownership = row['Ownership']
        is_public[h] = 1 if ownership.lower() == 'Public' else 0
    
    # Create lists of public and private hospitals
    public_hospitals = [h for h in H if is_public[h] == 1]
    private_hospitals = [h for h in H if is_public[h] == 0]
    
    #Only hospitals within 15km of a district centroid is eligible for consideration/reallocation
    hospital_districts = {} 
    for h in H:
        hospital_districts[h] = [d for d in D if (h, d) in dist and dist[(h, d)] <= 15.0]
    
    district_hospitals = {} 
    district_public_hospitals = {}
    district_private_hospitals = {}
    for d in D:
        district_hospitals[d] = [h for h in H if (h, d) in dist and dist[(h, d)] <= 15.0]
        district_public_hospitals[d] = [h for h in district_hospitals[d] if is_public[h] == 1]
        district_private_hospitals[d] = [h for h in district_hospitals[d] if is_public[h] == 0]

    #We will calculate the weight for the objective function first
    hospital_demand = {}
    for h in H:
        total_weighted_demand = 0
        for d in hospital_districts[h]:
            ownership_factor = 1.5 if is_public[h] == 1 else 1.0
            demand_weight = (ownership_factor * CVI[d] * pop[d]) / (dist[(h, d)] ** 2)
            total_weighted_demand += demand_weight
        hospital_demand[h] = total_weighted_demand

    #Now, we create the model
    print("Model created.")
    model = pulp.LpProblem("Hospital Allocation", pulp.LpMaximize)
    
    #Decision variables
    X_hd = pulp.LpVariable.dicts("Doctors",
                                 H,
                                 lowBound=0,
                                 cat='Integer')
    X_hb = pulp.LpVariable.dicts("Beds",
                                 H,
                                 lowBound=0,
                                 cat='Integer')
    
    #Objective Function
    model += pulp.lpSum([hospital_demand[h] * (X_hd[h] + X_hb[h]) for h in H])
    
    #Constraints
    print("Adding constraints.")
    #1. Conservation of resources (reallocation)
    model += pulp.lpSum([X_hd[h] for h in H]) == sum(current_doctors.values())
    model += pulp.lpSum([X_hb[h] for h in H]) == sum(current_beds.values())

    #2. Hospital capacity limits (cannot expand too much, cannot be left with 0)
    for h in H:
        model += X_hd[h] <= current_doctors[h] * 1.5
        model += X_hb[h] <= current_beds[h] * 1.5
    for h in H:
        model += X_hd[h] >= 0
        model += X_hb[h] >= 0

    #3. District coverage (ensure that all districts get adequate healthcare)
    for d in D:
        if district_hospitals[d]:
            district_need_doctors = int(0.004 * pop[d] * (1+CVI[d]))
            district_need_beds = int(0.011 * pop[d] * (1+CVI[d]))
            # Weighted allocation based on distance
            model += pulp.lpSum([X_hd[h] / math.sqrt(dist[(h, d)]) * (1.5 if is_public[h] == 1 else 1.0) 
                                for h in district_hospitals[d]]) >= district_need_doctors/90
            model += pulp.lpSum([X_hd[h] / math.sqrt(dist[(h, d)]) * (1.5 if is_public[h] == 1 else 1.0) 
                                for h in district_hospitals[d]]) >= district_need_beds/240

    #4. Vulnerable coverage gets priority
    for d in D:
        if CVI[d] >= 0.5 and district_hospitals[d]:
            nearby_capacity_doctors = pulp.lpSum([X_hd[h] for h in district_hospitals[d]])
            nearby_capacity_beds = pulp.lpSum([X_hb[h] for h in district_hospitals[d]])
            
            model += nearby_capacity_doctors >= district_need_doctors * 2
            model += nearby_capacity_beds >= district_need_beds * 2

            # If public hospitals exist in range, ensure they provide at least 50% of the capacity
            if district_public_hospitals[d]:
                model += pulp.lpSum([X_hd[h] for h in district_public_hospitals[d]]) >= 0.5 * district_need_doctors * 2
                model += pulp.lpSum([X_hb[h] for h in district_public_hospitals[d]]) >= 0.5 * district_need_beds * 2

    #5. Doctor-bed ratio preferably (1:8)
    for h in H:
        model += 8 * X_hd[h] >= X_hb[h]
        model += X_hd[h] <= 8 * X_hb[h]

    print("Constraints successfully added.")

    #Solve the model
    print("Solving optimization model.")
    model.solve(pulp.PULP_CBC_CMD(msg=1))

    #Display results
    if model.status == pulp.LpStatusOptimal:
        print("OPTIMAL SOLUTION FOUND.")
        print(f"Optimal objective value: {pulp.value(model.objective):.2f}")

        print("\nOptimal Hospital Allocations:")
        print("-" * 80)
        print(f"{'Hospital':<10} {'Current':<15} {'Optimal':<15} {'Current':<15} {'Optimal':<15} {'Districts':<10}")
        print(f"{'ID':<10} {'Doctors':<15} {'Doctors':<15} {'Beds':<15} {'Beds':<15} {'Served':<10}")
        print("-" * 80)

        for h in H: 
            current_doc = current_doctors[h]
            current_bed = current_beds[h]
            optimal_doc = int(pulp.value(X_hd[h]))
            optimal_bed = int(pulp.value(X_hb[h]))
            districts_served = len(hospital_districts[h])
        
            print(f"{h:<10} {current_doc:<15} {optimal_doc:<15} {current_bed:<15} {optimal_bed:<15} {districts_served:<10}")

    #Save results
        results = []
        for h in H:
            results.append({
                'Hospital ID': h,
                'Current Doctors': current_doctors[h],
                'Optimal Doctors': int(pulp.value(X_hd[h])),
                'Current Beds': current_beds[h],
                'Optimal Beds': int(pulp.value(X_hb[h])),
                'Doctor Change': int(pulp.value(X_hd[h])) - current_doctors[h],
                'Bed Change': int(pulp.value(X_hb[h])) - current_beds[h]
            })

        results_df = pd.DataFrame(results)
        results_df.to_csv('Hospital Reallocation Results (All).csv', index=False)
        print(f"\nResults saved to 'Hospital Reallocation Results.csv'")
    
    else:
        print("No optimal solution found")
        print(f"Status: {pulp.LpStatus[model.status]}")
    
    return model

if __name__ == "__main__":
    model = solve_hospital_allocation()