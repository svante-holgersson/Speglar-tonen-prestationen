# Speglar tonen prestationen?

This repository contains the code used in the bachelor's thesis "Speglar tonen prestationen?".

The data used in the study are publicly available from their respective sources and must be downloaded separately.

The repository contains scripts for data collection, data processing, sentiment analysis, and statistical analysis.





# Reproducibility Package – “Speglar tonen prestationen?”

This repository contains the complete empirical implementation used in the master’s thesis *“Speglar tonen prestationen?”*. The project combines textual analysis of CEO letters with financial statement data to construct a unified dataset for econometric analysis.

The code is fully reproducible conditional on access to the same external data sources and properly specified file paths.

---

## 1. Textual Tone Analysis (`tone_analysis.py`)

The script `tone_analysis.py` implements the textual analysis framework used to construct tone measures from CEO letters.

### Data requirements

The analysis requires:

- CEO letters in PDF format (manually collected from external databases such as Business Retriever and similar sources)
- Predefined sentiment dictionaries:
  - Loughran & McDonald word lists
  - Henry word lists
- User-defined file paths for input and output directories

### Methodological procedure

The script implements a standard bag-of-words framework and performs:

- Text preprocessing and document construction
- Term frequency (TF) and document frequency calculations
- Construction of weighted and unweighted tone measures
- Sentiment classification using two alternative dictionaries (Loughran & McDonald; Henry)
- Construction of first-differences (Δ-tone) to capture temporal variation

---

### Output structure

The main output is a CSV file containing company-year observations with the following categories:

#### Loughran & McDonald-based measures
- Tone indices (weighted and unweighted)
- Positive and negative tone components
- Sentiment scores
- First-differenced tone measures (Δ-tone)

#### Henry-based measures
- Equivalent tone, sentiment, and Δ-tone measures based on the Henry dictionary

---

### Additional output: keyword structure

The function `write_top_words_structured()` generates a supplementary dataset containing the most influential words per observation, including:

- word identity
- term frequency
- corresponding weight

This enables interpretability of the constructed tone measures at the lexical level.

---

## 2. Financial Data Construction (`financial_analysis.py`)

Financial data is imported from external proprietary databases (e.g., Business Retriever and Refinitiv/Eikon, depending on availability) and must be manually downloaded prior to execution.

The script performs:

- Data cleaning and normalization of financial variables
- Construction of a balanced/unbalanced panel dataset
- Computation of standard financial indicators, including:
  - Total assets and growth measures
  - Sales growth
  - Leverage ratios
  - Profitability (ROA)
  - Firm age
  - CEO tenure and CEO turnover indicators
  - Market capitalization
  - Book-to-market ratio

The resulting dataset is structured at the firm-year level.

---

## 3. Dataset integration (`merge.py`)

The textual and financial datasets are merged using firm and year identifiers, producing the final empirical dataset used in the econometric analysis.

---

## 4. Empirical analysis

The final dataset is exported as a CSV file and used for statistical analysis in external software (R), including panel regressions and robustness checks.

---

## 5. Reproducibility and research design

All scripts are designed to ensure computational reproducibility under the assumption that:

- identical input data is used
- directory structures are correctly specified
- sentiment dictionaries remain unchanged

The repository implements a modular pipeline separating data collection, textual analysis, financial construction, and econometric preparation.
