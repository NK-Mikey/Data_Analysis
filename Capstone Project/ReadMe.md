# 🚗 Tesla Fatal Crash Analysis (2013–2023)

This study analyzes Tesla’s fatal crash records to understand safety outcomes between Autopilot and manual driving. The findings indicate no statistical difference in fatality rates, but mode-specific patterns exist. NLP revealed distinct crash themes, offering actionable recommendations for Tesla engineers, regulators, and the public. The project promotes data-driven innovation and better safety design in autonomous systems.

---

## 📊 Key Insights

- **Crash Severity:** No significant statistical difference between Autopilot and Manual driving fatality rates.
- **Thematic Patterns:** NLP and topic modeling uncovered five major root-cause clusters:  
  `Signal Misjudgment`, `Excessive Speed`, `Detection Failure`, `Loss of Control`, and `Lane Departure`.
- **Driving Mode Differences:**  
  - Manual mode is associated with more `Signal Misjudgment` and `Detection Failure`.  
  - Autopilot mode is linked more with `Excessive Speed` and `Loss of Control`.

---

## 📁 Project Structure

- `tesla_analysis.ipynb` – Full Jupyter notebook with EDA, stats, NLP, visualizations
- `Tesla Fatal Crash Report.pdf` – Final report with findings and recommendations
- `figures/` – Visuals and charts used in the report

---

## 📌 Recommendations

- **Tesla (Primary Stakeholder):** Improve Autopilot reliability under high-speed/complex scenarios, enhance in-cabin monitoring, and increase transparency on system limitations.
- **Regulators:** Set clearer standards for autonomous vehicle testing and public reporting.
- **Researchers:** Use exposure-adjusted crash metrics (e.g., deaths per million miles driven).
- **Public:** Be aware of Autopilot’s actual capabilities vs. perceived autonomy.

---

## 🔍 Methods Used

- Descriptive EDA (Temporal, Geographic, Vehicle Model)
- Independent t-test, Poisson regression (Objective 1)
- Topic Modeling (LDA) using NLP (Objective 2)
- Comparative Risk Analysis across Modes (Objective 3)
- Tools: `Python`, `pandas`, `matplotlib`, `scikit-learn`, `nltk`, `gensim`, `seaborn`

---

## 🚧 Limitations

- Fatal crashes only; non-fatal incidents excluded  
- Lack of mileage/time-based exposure data  
- Crash narrative subjectivity  
- Rapid evolution of Autopilot versions  
- External factors (weather, lighting) not captured

---

## 🚀 Next Steps

- Incorporate non-fatal crash data for a broader view
- Add telemetry and weather data for richer context
- Upgrade NLP pipeline using transformers (e.g., BERT)
- Visualize data interactively via `Plotly` or `Dash`

---

## 👤 Author

**Naveen Karan Krishna**  
Graduate – Business Analytics, Seneca College  
[LinkedIn](https://www.linkedin.com/in/naveen-karan-krishna/) | [Email](mailto:naveenxkaran@gmail.com)

---

## 👤 Co-Author

**Mayra Geraldine Reinoso Varon**

**Ato Kwamena Essiem** 

**Charles Ifeanyi Okpala** 

**Jonada Golemaj**

---

## 🙌 Acknowledgements
- Kaggle datasets and open-source datasets used for model training and testing.
- TeslaDeaths.com for the crash data used in the capstone.

---

## Please credit this work when used: © 2025 NK, MIT Licensed.

---
