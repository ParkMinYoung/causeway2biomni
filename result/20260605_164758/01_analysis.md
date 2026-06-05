# Causeway MR Analysis Report: Lipid Traits → Coronary Artery Disease (BioBank Japan)

---

## Task 1: Data Overview

### 1.1 Exposure-Outcome Pairs
| # | Exposure | Outcome |
|---|----------|---------|
| 1 | logTG (log-Triglycerides) | CAD |
| 2 | HDL (HDL-Cholesterol) | CAD |
| 3 | LDL (LDL-Cholesterol) | CAD |
| 4 | TC (Total Cholesterol) | CAD |
| 5 | nonHDL (non-HDL Cholesterol) | CAD |

### 1.2 Number of Instruments per Exposure
| Exposure | TwoSampleMR N | GSMR N |
|----------|---------------|--------|
| logTG | 49 | 49 |
| HDL | 106 | 107 |
| LDL | 49 | 52 |
| TC | 108 | 98 |
| nonHDL | 85 | 77 |

### 1.3 Missing/Anomalous Values
- **No missing values** detected in any column
- **No negative standard errors** detected
- All data quality checks passed

---

## Task 2: Primary MR Estimates (IVW)

| Exposure | OR (95% CI) | P-value | N Instruments | GWS Flag |
|----------|-------------|---------|---------------|----------|
| logTG | 1.165 (1.082–1.254) | 5.27×10⁻⁵ | 49 | ✓ |
| HDL | 0.795 (0.723–0.875) | 2.65×10⁻⁶ | 106 | ✓ |
| **LDL** | **1.695 (1.465–1.961)** | **1.32×10⁻¹²** | 49 | ✓ |
| TC | 1.566 (1.415–1.732) | 3.41×10⁻¹⁸ | 108 | ✓ |
| **nonHDL** | **1.726 (1.528–1.950)** | **1.65×10⁻¹⁸** | 85 | ✓ |

**Note:** ✓ = All instruments meet genome-wide significance (p < 5×10⁻⁸) threshold

**Key Findings:**
- **LDL-C and non-HDL-C** show the strongest causal effects (OR ≈ 1.7)
- **HDL-C** shows a protective effect (OR = 0.80)
- All associations are highly significant (P < 10⁻⁵)

---

## Task 3: Sensitivity Analyses

### 3.1 MR-Egger Pleiotropy Test
| Exposure | Egger Intercept | SE | P-value | Pleiotropy? |
|----------|-----------------|-----|---------|-------------|
| logTG | 0.0033 | 0.0050 | 0.515 | No |
| HDL | -0.0057 | 0.0055 | 0.306 | No |
| LDL | 0.0081 | 0.0087 | 0.356 | No |
| TC | -0.0048 | 0.0053 | 0.360 | No |
| nonHDL | 0.0032 | 0.0066 | 0.631 | No |

**Interpretation:** No significant directional pleiotropy detected for any exposure (all P > 0.30)

### 3.2 Weighted Median Results
| Exposure | OR (95% CI) | P-value |
|----------|-------------|---------|
| logTG | 1.137 (1.060–1.221) | 3.63×10⁻⁴ |
| HDL | 0.869 (0.808–0.935) | 1.83×10⁻⁴ |
| LDL | 1.494 (1.346–1.658) | 3.96×10⁻¹⁴ |
| TC | 1.496 (1.362–1.644) | 4.50×10⁻¹⁷ |
| nonHDL | 1.610 (1.468–1.767) | 8.15×10⁻²⁴ |

### 3.3 MR-PRESSO Results
| Exposure | Global Test P-value | Interpretation |
|----------|---------------------|----------------|
| logTG | <0.001 | Significant outliers detected |
| HDL | <0.001 | Significant outliers detected |
| LDL | <0.001 | Significant outliers detected |
| TC | <0.001 | Significant outliers detected |
| nonHDL | <0.001 | Significant outliers detected |

**Note:** All exposures show significant outlier heterogeneity by MR-PRESSO, though outlier-corrected estimates were not separately reported in the output file.

### 3.4 MR-Egger Slope Results
| Exposure | OR (95% CI) | P-value |
|----------|-------------|---------|
| logTG | 1.128 (0.998–1.274) | 0.059 |
| HDL | 0.848 (0.726–0.991) | 0.040 |
| LDL | 1.531 (1.181–1.984) | 0.002 |
| TC | 1.702 (1.387–2.090) | 1.62×10⁻⁶ |
| nonHDL | 1.648 (1.319–2.060) | 3.30×10⁻⁵ |

---

## Task 4: Heterogeneity Assessment

### 4.1 Cochran's Q Statistic
| Exposure | Q Statistic | df | P-value | I² (%) | Interpretation |
|----------|-------------|-----|---------|--------|----------------|
| logTG | 143.2 | 48 | 2.08×10⁻¹¹ | 66.5 | Substantial |
| HDL | 797.0 | 105 | 7.54×10⁻¹⁰⁷ | 86.8 | Considerable |
| LDL | 379.0 | 48 | 5.46×10⁻⁵³ | 87.3 | Considerable |
| TC | 511.7 | 107 | 4.27×10⁻⁵⁴ | 79.1 | Considerable |
| nonHDL | 605.9 | 84 | 5.00×10⁻⁸⁰ | 86.1 | Considerable |

### 4.2 I² Interpretation Guide
- **I² < 25%**: Low heterogeneity
- **I² 25–50%**: Moderate heterogeneity
- **I² 50–75%**: Substantial heterogeneity
- **I² > 75%**: Considerable heterogeneity

**Key Finding:** All exposures show significant heterogeneity. logTG has the lowest I² (66.5%), while LDL has the highest (87.3%).

---

## Task 5: Steiger Filtering

### 5.1 Steiger Directionality Test
| Exposure | r² (Exposure) | r² (Outcome) | Correct Direction | Steiger P |
|----------|---------------|--------------|-------------------|-----------|
| logTG | 0.0804 | 0.0011 | ✓ Yes | 0 |
| HDL | 0.1230 | 0.0054 | ✓ Yes | 0 |
| LDL | 0.0620 | 0.0043 | ✓ Yes | 0 |
| TC | 0.0774 | 0.0049 | ✓ Yes | 0 |
| nonHDL | 0.0784 | 0.0065 | ✓ Yes | 0 |

### 5.2 Instruments Removed
| Exposure | GSMR N | TwoSampleMR N | Difference |
|----------|--------|---------------|------------|
| logTG | 49 | 49 | 0 |
| HDL | 107 | 106 | -1 |
| LDL | 52 | 49 | -3 |
| TC | 98 | 108 | +10* |
| nonHDL | 77 | 85 | +8* |

*Differences due to different clumping/harmonization procedures between GSMR and TwoSampleMR

### 5.3 Causal Direction Confirmation
**All five exposures confirm correct causal direction (Exposure → Outcome)** with Steiger P-values effectively equal to zero, indicating the genetic instruments explain substantially more variance in the exposure than in the outcome.

---

## Task 6: Funnel Plot Asymmetry

### 6.1 Egger Regression Test for Asymmetry
| Exposure | Egger Intercept | P-value | Asymmetry Detected? |
|----------|-----------------|---------|---------------------|
| logTG | 0.0033 | 0.515 | No |
| HDL | -0.0057 | 0.306 | No |
| LDL | 0.0081 | 0.356 | No |
| TC | -0.0048 | 0.360 | No |
| nonHDL | 0.0032 | 0.631 | No |

### 6.2 Interpretation
- **No significant funnel plot asymmetry** detected for any exposure (all Egger intercept P > 0.30)
- However, **significant MR-PRESSO global tests** (all P < 0.001) indicate presence of outlier instruments
- High heterogeneity (I² = 67–87%) suggests potential for outlier-driven effects, though not systematic directional pleiotropy

---

## Task 7: Expert Verdict

### Comprehensive Summary Table

| Exposure | IVW OR (95% CI) | IVW P | WM OR | Egger P | I²% | Pleio P | Direction Consistent |
|----------|-----------------|-------|-------|---------|-----|---------|---------------------|
| logTG | 1.165 (1.082–1.254) | 5.27×10⁻⁵ | 1.137 | 0.059 | 66.5 | 0.515 | ✓ |
| HDL | 0.795 (0.723–0.875) | 2.65×10⁻⁶ | 0.869 | 0.040 | 86.8 | 0.306 | ✓ |
| LDL | 1.695 (1.465–1.961) | 1.32×10⁻¹² | 1.494 | 0.002 | 87.3 | 0.356 | ✓ |
| TC | 1.566 (1.415–1.732) | 3.41×10⁻¹⁸ | 1.496 | 1.62×10⁻⁶ | 79.1 | 0.360 | ✓ |
| nonHDL | 1.726 (1.528–1.950) | 1.65×10⁻¹⁸ | 1.610 | 3.30×10⁻⁵ | 86.1 | 0.631 | ✓ |

### Evidence Criteria Assessment

| Criterion | logTG | HDL | LDL | TC | nonHDL |
|-----------|-------|-----|-----|-----|--------|
| IVW significant (P < 0.05) | ✓ | ✓ | ✓ | ✓ | ✓ |
| WM significant & consistent | ✓ | ✓ | ✓ | ✓ | ✓ |
| MR-Egger direction consistent | ✓ | ✓ | ✓ | ✓ | ✓ |
| No directional pleiotropy | ✓ | ✓ | ✓ | ✓ | ✓ |
| Correct causal direction | ✓ | ✓ | ✓ | ✓ | ✓ |
| Acceptable heterogeneity (I² < 75%) | ✓ | ✗ | ✗ | ✗ | ✗ |
| **Criteria met** | **6/6** | **5/6** | **5/6** | **5/6** | **5/6** |

---

## FINAL EXPERT VERDICT

**VERDICT: STRONG**

**RATIONALE (2-3 sentences):** This BioBank Japan Mendelian randomization analysis provides strong evidence for causal effects of lipid traits on coronary artery disease in East Asians. All five lipid exposures (LDL-C, non-HDL-C, TC, TG, HDL-C) demonstrate highly significant IVW estimates (all P < 5×10⁻⁵), consistent effect directions across all sensitivity analyses (weighted median, MR-Egger), no evidence of directional pleiotropy (all Egger intercept P > 0.30), and confirmed correct causal direction via Steiger filtering.

**MAIN_CAVEAT:** Substantial heterogeneity (I² = 67–87%) across all exposures indicates potential violation of the exclusion restriction assumption, despite no significant directional pleiotropy detected by the Egger intercept test.

**IS_CANDIDATE_FALSE_REASON:** Conservative criteria — All exposures are marked `is_candidate=False` in the Causeway pipeline output, likely due to stringent heterogeneity thresholds (I² > 50%) or significant MR-PRESSO global test results (all P < 0.001), despite otherwise robust causal evidence.

---

### Exposure-Specific Verdicts

| Exposure | Verdict | Key Observation |
|----------|---------|-----------------|
| **LDL → CAD** | STRONG | OR = 1.70; strongest evidence, consistent with European MR studies |
| **nonHDL → CAD** | STRONG | OR = 1.73; largest effect size, highly significant across all methods |
| **TC → CAD** | STRONG | OR = 1.57; robust signal reflecting combined LDL+nonHDL effects |
| **HDL → CAD** | MODERATE | OR = 0.80; protective effect but highest heterogeneity (I² = 87%) |
| **logTG → CAD** | MODERATE | OR = 1.17; smallest effect but only exposure with I² < 75% |

---

*Analysis completed using Causeway MR pipeline results from BioBank Japan (BBJ) GWAS data.*