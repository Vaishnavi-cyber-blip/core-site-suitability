## 🚀 Problem Statement

India’s agriculture is highly dependent on rainfall, and incorrect placement of water harvesting structures leads to:

- Poor water retention  
- Structural failure  
- Financial loss for farmers  
- Inefficient use of resources  

Current planning relies on manual judgment and static rules.

**Goal:** Build a data-driven, explainable system for site suitability evaluation.

---

## 🧠 What This Project Does

- Validates suitability of water harvesting structures  
- Detects user-side and system-side errors  
- Automates geospatial feature extraction using Google Earth Engine  
- Applies rule-based evaluation  
- Uses machine learning for pattern analysis and recommendations  

---

## 🏗️ System Architecture

Frontend (React)
↓
Flask Backend API
↓
Google Earth Engine
↓
Rules Engine (JSON)
↓
Suitability Output + Recommendation

---

## 🌍 Key Parameters

The system evaluates each site using:

- **Slope (%)** → Controls runoff and erosion  
- **Drainage Distance (m)** → Water availability  
- **Stream Order** → Flow magnitude  
- **Catchment Area (ha)** → Runoff contribution  
- **LULC (Land Use/Land Cover)** → Feasibility  

---

## ⚙️ Methodology

### 1. Rule-Based Evaluation
Each parameter is classified as:
- Accepted  
- Partially Accepted  
- Not Accepted  

Thresholds are defined per structure based on literature and field validation.

---

### 2. DPR Ground Truth Validation

- 30 real-world sites analyzed  
- Multi-state validation (Odisha, Rajasthan, Gujarat)  
- Manual validation using QGIS  

#### Error Types:
- **Error 1 (User-side):** Wrong location marking  
- **Error 2 (System-side):** Data issues (LULC, missing data)  
- **Error 3:** Rule inconsistencies  

---

### 3. Automated Geospatial Pipeline

Using Google Earth Engine:

- Slope extraction  
- Drainage distance calculation  
- Catchment area (with snapping)  
- Stream order extraction  
- LULC classification  

---
### 4. Smart Improvements

- **Snapped Catchment Area**  
  Uses nearby values instead of exact pixel to improve accuracy  

- **Buffer Tolerance (±0.5)**  
  Prevents false negatives due to small variations  

---
### 5. Machine Learning Extension

- Model: Random Forest  
- Tasks:
  - Suitability classification  
  - Structure recommendation  

Helps capture non-linear relationships beyond fixed rules.

---
## 🧪 Workflow

1. User inputs:
   - Plan ID  
   - Location  

2. System:
   - Fetches DPR data  
   - Performs error checks  

3. If valid:
   - Extracts geospatial features  
   - Applies rules  

4. Output:
   - Parameter-wise evaluation  
   - Final suitability decision  
   - Recommended structure  

---
## 🖥️ Tech Stack

- **Frontend:** React  
- **Backend:** Flask (Python)  
- **Geospatial:** Google Earth Engine  
- **GIS Tools:** QGIS  
- **ML:** Scikit-learn (Random Forest)  

---
## 📂 Project Structure
core-site-suitability/
│
├── backend/
│ ├── app.py
│ ├── gee_scripts/
│ ├── rules.json
│
├── frontend/
│ ├── src/
│
├── data/
├── notebooks/
├── reports/
└── README.md
---

## 📊 Key Insights

- Rule-based systems alone are insufficient  
- Data errors significantly impact planning  
- ML can identify hidden patterns  
- Explainability is critical for adoption  

---
## 🎯 Future Work

- Expand dataset for better ML performance  
- Add soil and groundwater parameters  
- Integrate rainfall data  
- Build decision dashboard  

---
## ⭐ Impact

This project aims to improve:

- Water resource planning  
- Agricultural productivity  
- Climate resilience  
