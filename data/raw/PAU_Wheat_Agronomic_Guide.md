# 🌾 PAU Agronomic Guide: Wheat (ਕਣਕ / गेहूँ) Cultivation for Punjab & Ludhiana Region
**Source Reference:** Punjab Agricultural University (PAU), Ludhiana — *Package of Practices for Rabi Crops (Rabi/Wheat)*

This document structures PAU's official agricultural recommendations for **Wheat** into clean, rule-based logic ready for your **Knowledge Base (KB)** and **RAG Pipeline**.

---

## 📌 Executive Summary (At a Glance)

| Parameter | Standard Recommendation (PAU) |
|---|---|
| **Target Crop** | Wheat (ਕਣਕ / गेहूँ) — Popular varieties: PBW 824, PBW 869, HD 3086, HD 2967, DBW 187, DBW 222 |
| **Target Region** | Ludhiana & Central Plain Zone of Punjab |
| **Most Critical Irrigation** | **Crown Root Initiation (CRI) stage** at **20–25 days after sowing (DAS)**. Missing this causes irreversible yield loss. |
| **Total Irrigations** | 4 to 5 irrigations across the season (depending on winter rains/Western Disturbances). |
| **Fertilizer Split** | Full DAP (55 kg/acre) + 1/2 Urea at sowing; remaining 1/2 Urea at 1st irrigation (CRI stage). Complete all nitrogen before 2nd irrigation. |
| **Weather Risk** | **High winds & terminal heat in Feb/March:** Never irrigate on windy days during grain filling to prevent crop lodging (falling over). |

---

## 💧 1. Irrigation Management (ਸਿੰਚਾਈ ਪ੍ਰਬੰਧਨ)

Wheat requires 4–5 timely irrigations. The timing must match specific physiological growth stages rather than fixed calendar days.

### Critical Growth Stages & Irrigation Priority:

```
Sowing (0 DAS) ────► 1. CRI Stage (20–25 DAS) ──► 2. Tillering (40–45 DAS)
                               │
       ┌───────────────────────┴────────────────────────┐
       ▼                                                ▼
3. Late Jointing / Booting (70–75 DAS) ──► 4. Flowering / Milking (90–105 DAS) ──► 5. Dough Stage (115–120 DAS)
```

| Priority | Growth Stage | Days After Sowing (DAS) | Criticality / Rule |
|---|---|---|---|
| **1 (Must Apply)** | **Crown Root Initiation (CRI)** | **20–25 days** | **Most critical irrigation.** If water is limited to only 1 irrigation the whole season, apply it here. |
| **2** | **Tillering Stage** | **40–45 days** | Coincides with second urea split; promotes productive tillers. |
| **3** | **Late Jointing / Booting** | **70–75 days** | Spike and earhead formation. |
| **4** | **Flowering / Anthesis** | **90–95 days** | Moisture stress during pollination causes unfilled spikelets. |
| **5** | **Milking / Soft Dough** | **105–115 days** | Grain weight accumulation. **Check wind speed before irrigating.** |

> **PAU Cut-off Rule:** Stop irrigation completely by **end of March** (soft-to-hard dough stage) to allow natural ripening.

---

## 🌱 2. Fertilizer Management (ਖਾਦ ਪ੍ਰਬੰਧਨ)

### Recommended Doses per Acre (Medium Fertility Soils):
* **Nitrogen (N):** ~50 kg N per acre $\rightarrow$ **110 kg Urea per acre** (or 90 kg Urea if preceding paddy had green manure/adequate fertility).
* **Phosphorus ($P_2O_5$):** 25 kg per acre $\rightarrow$ **55 kg DAP per acre** (or 150 kg Single Super Phosphate / SSP).
* **Potassium ($K_2O$):** 12 kg per acre $\rightarrow$ **20 kg MOP per acre** (only if soil testing indicates low potash).
* **Zinc / Manganese Deficiency:** In light sandy soils, spray 0.5% Manganese Sulphate ($MnSO_4$) solution 2–3 times at weekly intervals starting before 1st irrigation.

### Fertilizer Application Timeline:

```
┌───────────────────────────────────────────────┬───────────────────────────────────────────────┐
│              At Sowing (Basal)                │      1st Irrigation / CRI (20–25 DAS)         │
├───────────────────────────────────────────────┼───────────────────────────────────────────────┤
│ • Full DAP (55 kg/acre)                       │ • Remaining 1/2 Urea (45–55 kg/acre)          │
│ • Full MOP (20 kg/acre, if needed)            │ • Apply just before or immediately after      │
│ • 1/2 Urea (45–55 kg/acre)                    │   the 1st irrigation                          │
│ (Drill below seed using seed-cum-fert drill)  │ (Finish ALL nitrogen application here!)       │
└───────────────────────────────────────────────┴───────────────────────────────────────────────┘
```

> **PAU Golden Rule:** Complete the entire dose of Urea **before the second irrigation** (maximum by 45–50 DAS). Applying urea late during boot or flowering stages causes excessive leafiness, delayed maturity, rust infections, and heavy lodging.

---

## 🌦️ 3. Weather & Context-Aware Decision Gates (For AI Logic)

In your AI pipeline, use these programmatic gates before advising wheat farmers:

```
[Farmer asks: "Should I irrigate my wheat field this week?"]
   │
   ├─► Check Growth Stage: Is crop at Dough/Milking Stage (Feb/March)?
   │     ├─► YES: Check Wind Speed API!
   │     │     ├─► Wind speed > 12-15 km/h: "DO NOT IRRIGATE. High wind causes lodging (crop falling over)."
   │     │     └─► Wind speed < 10 km/h / Calm: "Safe to apply light irrigation."
   │     └─► NO: Check if current stage matches (CRI / Tillering / Booting / Flowering).
   │
   └─► Check Weather Forecast: Rain / Western Disturbance expected in 48 hrs?
         ├─► YES: "Postpone irrigation. Winter rain will provide necessary root-zone moisture."
         └─► NO: "Apply scheduled irrigation."
```

```
[Farmer asks: "Wheat leaves turning yellow in patches (Jan/Feb)"]
   │
   ├─► Check 1: Waterlogged field after heavy irrigation/rain?
   │     └─► "Temporary nitrogen starvation due to excess water. Drain excess water; spray 3% Urea solution."
   │
   ├─► Check 2: Yellow powdery dust on leaves (Yellow Rust / ਪੀਲੀ ਕੁੰਗੀ)?
   │     └─► "Yellow Rust symptom. Spray Propiconazole 25 EC (Tilt) @ 200 ml in 200 L water per acre immediately."
```

---

## 🐛 4. Major Pests & Diseases (Weed, Rust & Aphid)

1. **Gullidanda / Phalaris minor (ਗੁੱਲੀ ਡੰਡਾ - Canary grass):**
   * *Critical Window:* Spray weedicides within **30–35 days after sowing** (2–3 days after 1st irrigation when soil has adequate moisture).
2. **Yellow Rust (ਪੀਲੀ ਕੁੰਗੀ):**
   * *Symptom:* Yellow stripes of fungal powder on leaves in cool, humid winter (Jan–Feb).
   * *Action:* Immediate spray of *Tilt 25 EC* (Propiconazole) or *Nativo 75 WG*.
3. **Wheat Aphid (ਚੇਪਾ):**
   * *ETL Trigger:* Spray only if population exceeds **5 aphids per ear head** in March.

---

## 🗂️ 5. Sample Structured Data Chunk (For RAG Ingestion)

When building your JSON/Postgres Knowledge Base (Phase 1), structure Wheat PAU rules like this:

```json
[
  {
    "id": "pau_wheat_irrig_01",
    "crop": "wheat",
    "variety": "all",
    "district": "Ludhiana",
    "growth_stage": "CRI (Crown Root Initiation, 20-25 DAS)",
    "topic": "irrigation",
    "rule": "First irrigation must be applied at 20-25 days after sowing (CRI stage).",
    "reasoning": "Crown roots develop at this stage; water deficit here permanently stunts tiller count and root volume.",
    "source": "PAU Package of Practices Rabi 2024"
  },
  {
    "id": "pau_wheat_irrig_02",
    "crop": "wheat",
    "variety": "all",
    "district": "Ludhiana",
    "growth_stage": "Milking/Dough stage (Feb-March)",
    "topic": "irrigation",
    "rule": "Never irrigate wheat when wind speed is above 12-15 km/h.",
    "reasoning": "Irrigation weakens soil hold, causing heavy lodging (crop falling over), leading to massive yield loss.",
    "source": "PAU Package of Practices Rabi 2024"
  },
  {
    "id": "pau_wheat_fert_01",
    "crop": "wheat",
    "variety": "all",
    "district": "Ludhiana",
    "growth_stage": "sowing to 1st irrigation",
    "topic": "fertilizer",
    "rule": "Apply full DAP (55 kg/acre) + 1/2 Urea at sowing. Apply remaining 1/2 Urea at 1st irrigation (20-25 DAS). Complete all nitrogen before 2nd irrigation.",
    "reasoning": "Late urea after 45 days increases susceptibility to yellow rust and lodging without boosting yield.",
    "source": "PAU Package of Practices Rabi 2024"
  }
]
```
