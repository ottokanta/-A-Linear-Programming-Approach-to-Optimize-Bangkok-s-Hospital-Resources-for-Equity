# Optimizing Hospital Resource Allocation in Bangkok

This repository contains the code and data used in the paper:

**"A Linear Programming Approach to Optimize Bangkok's Hospitals' Resources for Equity"**

---

## Overview

This project applies **multi-integer linear programming** to examine how doctors and hospital beds could be reallocated across districts in Bangkok to improve equity in healthcare access. The model integrates:

- District-level population and vulnerability indices (CVI)  
- Accessibility thresholds based on distance  
- Resource conservation and capacity expansion limits  
- Doctor-to-bed ratio constraints

The optimization results identify "hub hospitals" and suggest strategies for reducing inequities in access.

---

## Repository Structure

This project contains 2 datasets and 3 coding files. 
- Research Dataset - Districts.csv # Population & vulnerability index by district
- Research Dataset - Hospitals.csv # Hospital resource availability (anonymized)
- District Centroid.py # Calculates geographic centroids for districts
- Distance Hospital and District.py # Computes distance matrix between hospitals and districts
- Optimization Model (All).py # MILP optimization model for resource allocation

Note: Data was publicly gathered from Thailand's official ministries, and individual hospital websites.

---

You are free to use, modify, and share, with attribution.
