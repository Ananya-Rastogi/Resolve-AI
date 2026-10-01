# FAQ Question-Answer Dataset Analysis for RAG (Week 2 Preparation)

This report provides a comprehensive analysis of `data/faq_question_answer_dataset.csv` to evaluate its structure, data quality, and suitability for Retrieval-Augmented Generation (RAG).

> **Important Note:** In accordance with project instructions, no RAG system, embeddings, vector database, or LangGraph changes were implemented. This document represents an inspection-only analysis.

---

## 1. Dataset Overview

* **File Path:** `data/faq_question_answer_dataset.csv`
* **File Size:** **7,325,517 bytes** (~7.33 MB / 6.99 MiB)
* **Total Records (Rows):** **30,000**
* **Total Features (Columns):** **17**
* **Missing Values:** **0** across all 17 columns (100% complete)
* **Total Exact Duplicate Rows:** **0** (each row has a unique `FAQ_ID` from `FAQ000001` to `FAQ030000`)
* **Duplicate Questions:** **29,940** (only **60 unique questions**)
* **Duplicate Answers:** **29,970** (only **30 unique answers**)
* **Unique (Question, Answer) Pairs:** **60**

---

## 2. Column Schema & Properties

| Column Name | Data Type | Null Count | % Missing | Unique Count | Sample Values |
|:---|:---:|:---:|:---:|:---:|:---|
| **FAQ_ID** | `object` | 0 | 0.00% | 30,000 | `FAQ000001`, `FAQ000002`, `FAQ000003`, `FAQ000004`, `FAQ000005` |
| **Category** | `object` | 0 | 0.00% | 10 | `Payment_Issue`, `Return_Request`, `Billing`, `Technical_Support`, `Shipping_Info` |
| **Subcategory** | `object` | 0 | 0.00% | 4 | `Troubleshooting`, `Process`, `Policy`, `General` |
| **Question** | `object` | 0 | 0.00% | 60 | *"Which payment methods are accepted?"*, *"How do I return an item?"* |
| **Answer** | `object` | 0 | 0.00% | 30 | *"We accept major cards, wallets, and selected bank transfer options."* |
| **Intent** | `object` | 0 | 0.00% | 10 | `Payment_Issue`, `Return_Request`, `Billing`, `Technical_Support`, `Shipping_Info` |
| **Keywords** | `object` | 0 | 0.00% | 60 | `which, payment, methods, accepted`, `return, item`, `charged, this, amount` |
| **Difficulty_Level** | `object` | 0 | 0.00% | 3 | `Medium`, `Hard`, `Easy` |
| **Language** | `object` | 0 | 0.00% | 1 | `English` |
| **Question_Length** | `int64` | 0 | 0.00% | 24 | `18`, `25`, `30`, `38`, `53` |
| **Answer_Length** | `int64` | 0 | 0.00% | 22 | `55`, `63`, `70`, `75`, `84` |
| **Question_Word_Count** | `int64` | 0 | 0.00% | 7 | `4`, `5`, `6`, `7`, `10` |
| **Answer_Word_Count** | `int64` | 0 | 0.00% | 8 | `8`, `10`, `12`, `14`, `15` |
| **Response_Type** | `object` | 0 | 0.00% | 4 | `Instructional`, `Informational`, `Troubleshooting`, `Policy` |
| **Industry** | `object` | 0 | 0.00% | 8 | `Retail`, `E-commerce`, `Technology`, `Banking`, `Healthcare` |
| **Last_Updated** | `object` | 0 | 0.00% | 181 | `2026-01-12`, `2026-03-18`, `2026-05-17`, `2026-06-30` |
| **Verified** | `object` | 0 | 0.00% | 2 | `Yes` (27,574), `No` (2,426) |

---

## 3. Question & Answer Text Analysis

### Character & Word Count Statistics

| Metric | Full Dataset (30,000 rows) | Unique Questions (60) / Answers (30) |
|:---|:---:|:---:|
| **Average Question Length** | **31.92 characters** | **35.80 characters** |
| **Minimum Question Length** | 18 characters | 18 characters |
| **Maximum Question Length** | 53 characters | 53 characters |
| **Average Answer Length** | **74.85 characters** | **74.83 characters** |
| **Minimum Answer Length** | 55 characters | 55 characters |
| **Maximum Answer Length** | 84 characters | 84 characters |
| **Average Question Word Count** | **6.07 words** | **6.67 words** |
| **Minimum Question Word Count** | 4 words | 4 words |
| **Maximum Question Word Count** | 10 words | 10 words |
| **Average Answer Word Count** | **11.66 words** | **11.67 words** |
| **Minimum Answer Word Count** | 8 words | 8 words |
| **Maximum Answer Word Count** | 15 words | 15 words |

### Canonical Knowledge Units Structure
Inspection reveals that every answer maps to **exactly 2 questions**:
1. A canonical concise question (e.g., *"How do I return an item?"*)
2. The same question with `" Please help."` appended (e.g., *"How do I return an item? Please help."*)

### 5 Representative Question $\rightarrow$ Answer Examples

1. **Payment Issue (`Payment_Issue`)**
   - **Question:** *"I was charged twice. What should I do?"*
   - **Answer:** *"Contact support with transaction details so the duplicate charge can be reviewed."*
2. **Return Request (`Return_Request`)**
   - **Question:** *"How do I return an item?"*
   - **Answer:** *"Start a return request from your order history and follow the return instructions."*
3. **Billing Inquiry (`Billing`)**
   - **Question:** *"Why was I charged this amount?"*
   - **Answer:** *"Charges may include product price, taxes, shipping, discounts, or subscription fees."*
4. **Technical Support (`Technical_Support`)**
   - **Question:** *"How do I fix a loading error?"*
   - **Answer:** *"Check your internet connection, refresh the page, or try another browser."*
5. **Shipping Information (`Shipping_Info`)**
   - **Question:** *"How long does shipping take? Please help."*
   - **Answer:** *"Standard shipping usually takes 3 to 7 business days depending on your location."*

---

## 4. Category & Metadata Distributions

### Category Distribution (Total 10 Categories)

| Category | Record Count | % of Dataset | Unique Questions | Unique Answers |
|:---|:---:|:---:|:---:|:---:|
| **Shipping_Info** | 3,093 | 10.31% | 6 | 3 |
| **Billing** | 3,066 | 10.22% | 6 | 3 |
| **Payment_Issue** | 3,032 | 10.11% | 6 | 3 |
| **Refund_Request** | 3,020 | 10.07% | 6 | 3 |
| **Complaint** | 3,010 | 10.03% | 6 | 3 |
| **Order_Status** | 3,001 | 10.00% | 6 | 3 |
| **Account_Access** | 3,000 | 10.00% | 6 | 3 |
| **Product_Inquiry** | 2,973 | 9.91% | 6 | 3 |
| **Technical_Support** | 2,923 | 9.74% | 6 | 3 |
| **Return_Request** | 2,882 | 9.61% | 6 | 3 |

*Key Finding:* `Intent` is **100% identical to `Category`** across all 30,000 rows (`(df['Category'] == df['Intent']).all() == True`).

### Subcategory Distribution (4 Classes)
- **Troubleshooting:** 7,517 (25.06%)
- **Process:** 7,497 (24.99%)
- **Policy:** 7,494 (24.98%)
- **General:** 7,492 (24.97%)

### Response Type Distribution (4 Classes)
- **Instructional:** 7,717 (25.72%)
- **Informational:** 7,567 (25.22%)
- **Troubleshooting:** 7,403 (24.68%)
- **Policy:** 7,313 (24.38%)

### Industry Distribution (8 Sectors)
- **Retail:** 3,846 (12.82%)
- **E-commerce:** 3,801 (12.67%)
- **Technology:** 3,749 (12.50%)
- **Education:** 3,739 (12.46%)
- **Healthcare:** 3,736 (12.45%)
- **Telecom:** 3,725 (12.42%)
- **Banking:** 3,703 (12.34%)
- **Travel:** 3,701 (12.34%)

### Language & Verification Distributions
- **Language:** **100% English** (30,000 rows).
- **Verified:**
  - **Yes:** 27,574 (91.91%)
  - **No:** 2,426 (8.09%)
  - *Note:* All 60 QA pairs appear in both the `Yes` and `No` subsets. `Verified` was synthetically assigned.

---

## 5. Data Quality Findings

1. **Cleanliness:**
   - Zero missing or null values.
   - Zero non-ASCII characters or broken encoding artifacts.
   - Zero whitespace irregularities (no leading or trailing whitespace).
2. **Synthetic Combinatorial Nature:**
   - The dataset consists of **30 canonical FAQ answers**, each associated with **2 question phrasings** (60 total questions).
   - The 30,000 rows were generated by multiplying these 60 QA items with synthetic permutations of `Industry`, `Subcategory`, `Response_Type`, `Difficulty_Level`, `Last_Updated`, and `Verified`.
   - The question and answer text **never changes** regardless of `Industry` or `Response_Type`.

---

## 6. RAG Suitability Assessment

### 1. Is this dataset suitable for RAG?
**Yes.** The 30 core answers represent well-formulated, authoritative responses to standard customer support issues (billing disputes, duplicate charges, return shipping policies, order tracking, app crashes, account recovery). They align directly with the domain of our customer support routing system.

### 2. Which columns should become searchable text?
* Primary: `Question` and `Answer`.
* Secondary: `Keywords` can be appended to the searchable text to bolster keyword matching (BM25 / lexical search).

### 3. Which columns should become metadata?
* `Category` (e.g. `Payment_Issue`, `Technical_Support`, `Billing`)
* `Subcategory` (e.g. `Troubleshooting`, `Policy`)
* `Intent`
* `Response_Type`
* `Industry`
* `Difficulty_Level`
* `Keywords`
* `FAQ_ID`

### 4. Should we use all 30,000 rows?
**ABSOLUTELY NOT.**
- Embedding 30,000 rows would index ~500 exact copies of each question and ~1,000 exact copies of each answer.
- Top-$k$ vector retrieval would return redundant, duplicate chunks from the same answer, degrading context quality, inflating token costs, and increasing latency by orders of magnitude.
- The knowledge corpus must be **deduplicated prior to indexing**.

### 5. Recommended Deduplication Strategy:
- Deduplicate into **30 canonical documents** (grouped by unique answer, consolidating both question variants into one document), or **60 unique QA documents** (grouped by unique Question + Answer).
- Grouping into 30 canonical documents yields a clean, zero-redundancy knowledge base of 30 documents.

### 6. Should we filter by Language or Verified?
- **Language:** Not required; the dataset is 100% English.
- **Verified:** Filtering `Verified == 'Yes'` is not strictly necessary for deduplication because all 60 QA pairs exist in the `Verified == 'Yes'` subset anyway.

### 7. Should Category / Intent be used as metadata filters?
**Yes, highly recommended.**
Our Week 1 classification pipeline predicts the ticket topic (`billing`, `shipping`, `technical`, `other`). The RAG retriever can use metadata pre-filtering on `Category` / `Intent` to eliminate out-of-domain chunks (e.g. billing tickets only search `Billing`, `Payment_Issue`, and `Refund_Request` chunks).

---

## 7. Concrete RAG Data Design Recommendation

When ingesting this dataset in Week 2, convert the deduplicated FAQs into documents following this structure:

### Document Text Representation
```text
Question: {Question}
Alternative Query: {Alternative_Question}
Answer: {Answer}
Keywords: {Keywords}
```

### Document Metadata Schema
```json
{
  "faq_id": "FAQ_CANONICAL_01",
  "category": "Payment_Issue",
  "subcategory": "Process",
  "intent": "Payment_Issue",
  "response_type": "Instructional",
  "difficulty_level": "Medium",
  "language": "English",
  "industries": ["Banking", "E-commerce", "Retail", "Technology", "Telecom", "Healthcare", "Education", "Travel"],
  "verified": true,
  "canonical_answer_id": 6
}
```

### Example Consolidated Document
```text
Question: I was charged twice. What should I do?
Alternative Query: I was charged twice. What should I do? Please help.
Category: Payment_Issue
Answer: Contact support with transaction details so the duplicate charge can be reviewed.
Keywords: charged, twice, transaction, duplicate
```

---

## 8. Summary Checklist

- [x] Basic dataset statistics extracted (30,000 rows, 17 columns, 7.33 MB).
- [x] Missing values analyzed (0% missing).
- [x] Duplicate structure discovered (30 unique answers, 60 unique questions, 29,940 synthetic repetitions).
- [x] Question & answer text length distributions computed.
- [x] Category, Subcategory, Intent, Response Type, Industry, Language, and Verified distributions analyzed.
- [x] RAG suitability assessed with concrete deduplication recommendation.
- [x] Target document text and metadata schema designed.
- [x] No modifications made to `data/faq_question_answer_dataset.csv`.
- [x] Existing Week 0 and Week 1 test suite verified.
