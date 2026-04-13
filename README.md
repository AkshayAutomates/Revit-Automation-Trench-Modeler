# 🔧 Revit Trench Automation Tool (Cable Tray Generator)

A custom pyRevit tool that automates cable tray (trench) creation in Autodesk Revit using selected MEP elements such as pipes and conduits.

Designed to simplify coordination and eliminate manual modelling by dynamically calculating trench geometry from real project conditions.

---

## 🚀 Features

- Supports multiple selection of pipes and conduits  
- Works across disciplines (Plumbing + Electrical)  
- Automatically detects shortest element for tray length  
- Calculates tray width based on outer span of selected elements  
- Adds configurable side clearance (default: 50 mm each side)  
- Computes tray height using largest diameter + bottom clearance  
- Automatically sets bottom elevation relative to pipe BOP  
- Handles both positive and negative elevations correctly  
- Aligns tray to the center of the full element bundle  
- Matches reference level of selected elements  
- Fully compatible with pyRevit (IronPython)
---
## 🧠 Workflow

1. Select pipes and/or conduits  
2. Tool extracts:
   - Diameter  
   - Location  
   - Elevation (relative to level)  

3. Automatically calculates:
   - Width = outer span + clearance  
   - Height = largest diameter + offset  
   - Bottom = lowest BOP – offset  

4. Generates cable tray aligned with:
   - Shortest element length  
   - Center of the full bundle  
---
## 📐 Key Logic

- Uses perpendicular projection for accurate width calculation  
- Handles level-based elevation (supports negative values)  
- Uses `LookupParameter()` for robust parameter handling  
---
## 🛠 Requirements

- Autodesk Revit 2024 or later  
- pyRevit  
- IronPython (default with pyRevit)  
---

## ⚠️ Notes

- Cable tray family must include:
  - Width  
  - Height  
  - Lower End Bottom Elevation  

- Works best with standard Revit MEP families  
- Custom families may require parameter mapping  

---

## 📦 Installation

1. Clone or download this repository  
2. Place it inside your pyRevit extensions folder  
3. Reload pyRevit  
4. Run tool from custom ribbon tab  

---

## 🎯 Use Cases

- Underground trench modelling  
- MEP coordination workflows  
- Automated routing preparation  
- BIM standardization  

---

## 🙌 Author

**Akshay Pawar**  
BIM Automation | Revit API Enthusiast  

---

## 📸 Demo

