# 🌾 PAU Agronomic Guide: Paddy (Rice) Cultivation for Punjab & Ludhiana Region
**Source Reference:** Punjab Agricultural University (PAU), Ludhiana — *Package of Practices for Kharif Crops (Kharif/Paddy)*

This document structures PAU's official agricultural recommendations into clean, rule-based logic ready for your **Knowledge Base (KB)** and **RAG Pipeline**.

---

## 📌 Executive Summary (At a Glance)

| Parameter | Standard Recommendation (PAU) |
|---|---|
| **Target Crop** | Paddy / Rice (ਝੋਨਾ / धान) — Varieties: PR 126, PR 121, PR 128, PR 130 |
| **Target Region** | Ludhiana & Central Plain Zone of Punjab |
| **Water Strategy** | Standing water for **first 15 days only**, then **Alternate Wetting & Drying (AWD)**: irrigate 2 days after ponded water has infiltrated. |
| **Urea Schedule** | 3 split doses: Basal/Transplanting, 21 Days (3 weeks), 42 Days (6 weeks). For short-duration (PR 126): finish by 35 days. |
| **Phosphorus Rule** | If recommended DAP was applied to previous wheat crop, **do NOT add DAP to paddy** (avoids soil toxicity & saves cost). |
| **Harvest Cutoff** | Stop all irrigation **15 days before harvesting**. |

---

## 💧 1. Irrigation Management (ਸਿੰਚਾਈ ਪ੍ਰਬੰਧਨ)

### A. Stage-Wise Irrigation Rules
1. **Transplanting to Day 15 (Establishment Phase):**
   * **Rule:** Keep **continuous standing water (4–5 cm)** for the first 15 days after transplanting to ensure root establishment and prevent early weed germination.
2. **Day 16 to Flowering Stage (Vegetative & Reproductive Phase):**
   * **Rule:** Do **NOT** keep continuous standing water.
   * **AWD Protocol:** Apply irrigation **2 days after** the standing water has completely seeped into the soil.
   * **Caution:** Do not let the soil dry out to the point of developing deep cracks.
3. **Flowering & Grain Filling Stage (Critical Stage):**
   * **Rule:** Moisture stress at panicle emergence and milking causes high chaffiness (empty grains). Ensure irrigation is applied promptly without delay.
4. **Pre-Harvest (Maturity Phase):**
   * **Rule:** Stop all irrigation **15 days prior to harvest** to facilitate uniform grain drying and allow combine harvesters in the field.

---

## 🌱 2. Fertilizer Management (ਖਾਦ ਪ੍ਰਬੰਧਨ)

### Recommended Doses per Acre (Medium Fertility Soils):
* **Nitrogen (N):** ~40–42 kg N per acre $\rightarrow$ **90 kg Urea per acre** (divided into 3 splits).
* **Phosphorus ($P_2O_5$):** 12 kg per acre $\rightarrow$ **27 kg DAP or 75 kg SSP per acre** (Only if soil test indicates deficiency or if not applied in preceding wheat).
* **Potassium ($K_2O$):** 12 kg per acre $\rightarrow$ **20 kg Muriate of Potash (MOP)** per acre (Only in low-potash soils).
* **Zinc ($Zn$):** 10 kg Zinc Sulphate (21%) or 6.5 kg Zinc Sulphate (33%) per acre (if deficiency/yellow patches appear).

### B. Split Schedule for Urea (Nitrogen)

```
┌───────────────────────────┬───────────────────────────────┬───────────────────────────┐
│        1st Dose           │           2nd Dose            │         3rd Dose          │
│ (At Transplanting/Basal)  │     (21 Days / 3 Weeks)       │   (42 Days / 6 Weeks)     │
├───────────────────────────┼───────────────────────────────┼───────────────────────────┤
│       30 kg Urea          │          30 kg Urea           │        30 kg Urea         │
│   (or skipped if green    │     (Crucial for Tillering)   │ (Finish by 35 days for    │
│    manure incorporated)   │                               │  short-duration PR 126)   │
└───────────────────────────┴───────────────────────────────┴───────────────────────────┘
```

> **PAU Golden Rule:** Avoid applying urea after 42 days (or after panicle initiation) as late application causes excessive vegetative growth, lodging, and attracts insect pests like Stem Borer and Brown Planthopper.

---

## 🌦️ 3. Weather & Context-Aware Decision Gates (For AI Logic)

In your AI pipeline, use these programmatic gates before giving advice:

```
[Farmer asks: "Should I irrigate today?"]
   │
   ├─► Check Weather API: Is rain > 5mm forecasted in next 48 hrs?
   │     ├─► YES: "Withhold irrigation. Expected rainfall will meet water demand."
   │     └─► NO: Proceed to AWD check.
   │
   ├─► Check Crop Stage & Field: Did standing water drain 2 days ago?
         ├─► YES: "Apply 5 cm irrigation today."
         └─► NO (Water still present or drained yesterday): "Wait 1 more day before irrigating."
```

```
[Farmer asks: "Can I spray/apply Urea today?"]
   │
   ├─► Check Weather API: Rain forecast in 24 hrs or high wind (>15 km/h)?
         ├─► YES: "Hold off on urea/spraying. Rain will wash nitrogen away (leaching loss)."
         └─► NO: "Apply urea in standing moist soil (not deep standing water)."
```

---

## 🐛 4. Major Pests & Economic Threshold Levels (ETL)

* **Leaf Folder (ਪੱਤਾ ਲਪੇਟ):**
  * *Symptom:* White streaks and folded leaves.
  * *ETL Trigger:* Spray only if **more than 10% damaged leaves** are observed.
* **Stem Borer (ਤਣਾ ਛੇਦਕ):**
  * *Symptom:* Dead hearts at vegetative stage or white ears at panicle stage.
  * *ETL Trigger:* Spray if **>5% dead hearts** are visible.
* **Zinc Deficiency (ਖਹਿਰਾ ਰੋਗ / Khaira Disease):**
  * *Symptom:* Lower leaves develop rusty-brown pigmentation, plant stunted.
  * *Action:* Foliar spray of 0.5% Zinc Sulphate (1 kg Zinc Sulphate 21% + 0.5 kg unslaked lime in 200 L water per acre).

---

## 🗂️ 5. Sample Structured Data Chunk (For RAG Ingestion)

When building your JSON/Postgres Knowledge Base (Phase 1), structure PAU rules like this:

```json
[
  {
    "id": "pau_paddy_irrig_01",
    "crop": "paddy",
    "variety": "all",
    "district": "Ludhiana",
    "growth_stage": "0-15 days after transplanting",
    "topic": "irrigation",
    "rule": "Maintain 4-5 cm continuous standing water for first 15 days.",
    "reasoning": "Ensures root establishment and inhibits weed seed germination.",
    "source": "PAU Package of Practices Kharif 2024"
  },
  {
    "id": "pau_paddy_irrig_02",
    "crop": "paddy",
    "variety": "all",
    "district": "Ludhiana",
    "growth_stage": "16 days to flowering",
    "topic": "irrigation",
    "rule": "Irrigate 2 days after ponded water has completely infiltrated the soil (AWD).",
    "reasoning": "Saves up to 25% irrigation water without any reduction in grain yield.",
    "source": "PAU Package of Practices Kharif 2024"
  },
  {
    "id": "pau_paddy_fert_01",
    "crop": "paddy",
    "variety": "PR 126",
    "district": "Ludhiana",
    "growth_stage": "tillering",
    "topic": "fertilizer",
    "rule": "Complete all 3 split doses of 90 kg urea per acre within 35 days after transplanting.",
    "reasoning": "Short duration variety completes tillering faster; late urea causes pest attacks.",
    "source": "PAU Package of Practices Kharif 2024"
  }
]
```
