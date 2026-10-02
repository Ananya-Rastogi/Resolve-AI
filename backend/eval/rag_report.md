# Week 2 RAG Retrieval Evaluation Report

## Executive Summary
- **Benchmark Dataset**: 30 realistic paraphrased queries based on Kaggle FAQ knowledge
- **Indexed Documents**: 30 deduplicated canonical FAQ records
- **Embedding Model**: `all-MiniLM-L6-v2` (384-dimensional dense vectors)
- **Vector Store**: `ChromaDB` (persistent local storage in `data/chroma/`)
- **Topic Filtering**: Active (Hybrid Coarse-to-Granular Mapping)

## Core Retrieval Metrics
| Metric | Result | Target Benchmark | Status |
|---|---|---|---|
| **Recall@1** | **86.7%** (26/30) | >= 70.0% | PASS |
| **Recall@3** | **96.7%** (29/30) | >= 85.0% | PASS |
| **Recall@5** | **100.0%** (30/30) | >= 90.0% | PASS |
| **Avg Retrieval Latency** | **27.81 ms** | < 50.0 ms | PASS |
| **P95 Retrieval Latency** | **68.41 ms** | < 100.0 ms | PASS |

## Detailed Query Retrieval Breakdown
| # | Query | Expected FAQ | Retrieved Top-1 | Rank | Latency |
|---|---|---|---|---|---|
| 1 | What cards or digital wallets can I use to pay for my order? | `FAQ_001` | `FAQ_001` ✓ | 1 | 17.64 ms |
| 2 | I would like to send back an item I purchased recently. | `FAQ_002` | `FAQ_002` ✓ | 1 | 14.23 ms |
| 3 | Why does my bill have extra fees and taxes added to it? | `FAQ_003` | `FAQ_003` ✓ | 1 | 14.83 ms |
| 4 | Am I responsible for the postage costs when returning a product? | `FAQ_004` | `FAQ_004` ✓ | 1 | 17.16 ms |
| 5 | I need help from a support engineer to troubleshoot an issue. | `FAQ_005` | `FAQ_005` ✓ | 1 | 33.33 ms |
| 6 | Is there warranty coverage or manufacturer protection on this gadget? | `FAQ_006` | `FAQ_006` ✓ | 1 | 19.92 ms |
| 7 | What are the delivery fees for standard home shipping? | `FAQ_007` | `FAQ_008` ✗ | 4 | 21.69 ms |
| 8 | How many business days will it take for my package to arrive? | `FAQ_008` | `FAQ_008` ✓ | 1 | 23.09 ms |
| 9 | The website is stuck on a blank screen and won't finish loading. | `FAQ_009` | `FAQ_009` ✓ | 1 | 20.27 ms |
| 10 | I see two charges for the same purchase on my bank statement. | `FAQ_010` | `FAQ_010` ✓ | 1 | 20.7 ms |
| 11 | My parcel is late and I don't know where it currently is. | `FAQ_011` | `FAQ_020` ~ | 2 | 20.87 ms |
| 12 | Is this item currently in stock or sold out? | `FAQ_012` | `FAQ_012` ✓ | 1 | 22.53 ms |
| 13 | I forgot my sign-in credentials and need to change my password. | `FAQ_013` | `FAQ_013` ✓ | 1 | 21.97 ms |
| 14 | How do I change the credit card saved on my profile for future bills? | `FAQ_014` | `FAQ_014` ✓ | 1 | 21.38 ms |
| 15 | I am unable to sign into my profile and it says login failed. | `FAQ_015` | `FAQ_015` ✓ | 1 | 20.41 ms |
| 16 | How many days do I have to return an item according to the rules? | `FAQ_016` | `FAQ_002` ~ | 2 | 25.25 ms |
| 17 | I am not satisfied with customer care and want to speak to a manager. | `FAQ_017` | `FAQ_027` ~ | 3 | 45.04 ms |
| 18 | I want my money back for an order I canceled. | `FAQ_018` | `FAQ_018` ✓ | 1 | 127.86 ms |
| 19 | Where can I view updates on the grievance ticket I submitted? | `FAQ_019` | `FAQ_019` ✓ | 1 | 33.15 ms |
| 20 | Has the warehouse dispatched my package yet? | `FAQ_020` | `FAQ_020` ✓ | 1 | 22.92 ms |
| 21 | Can I pay extra for next-day or overnight courier shipping? | `FAQ_021` | `FAQ_021` ✓ | 1 | 68.41 ms |
| 22 | The mobile application keeps freezing and crashing on launch. | `FAQ_022` | `FAQ_022` ✓ | 1 | 20.94 ms |
| 23 | Where are the technical dimensions and hardware specs listed? | `FAQ_023` | `FAQ_023` ✓ | 1 | 23.13 ms |
| 24 | Customer service declined my return and refund request. Why? | `FAQ_024` | `FAQ_024` ✓ | 1 | 21.28 ms |
| 25 | My credit card was declined during the checkout process. | `FAQ_025` | `FAQ_025` ✓ | 1 | 25.48 ms |
| 26 | I want to permanently remove my personal profile and account data. | `FAQ_026` | `FAQ_026` ✓ | 1 | 22.51 ms |
| 27 | I had a terrible experience and want to lodge an official complaint. | `FAQ_027` | `FAQ_027` ✓ | 1 | 18.36 ms |
| 28 | How long will it take for the refunded money to show up in my account? | `FAQ_028` | `FAQ_028` ✓ | 1 | 22.8 ms |
| 29 | Can you provide the courier tracking link for my recent order? | `FAQ_029` | `FAQ_029` ✓ | 1 | 23.31 ms |
| 30 | I need a PDF receipt or billing invoice for tax purposes. | `FAQ_030` | `FAQ_030` ✓ | 1 | 23.89 ms |

## Evaluation Methodology & Safeguards
1. **Paraphrase Evaluation**: Queries are strictly paraphrased from canonical questions; no literal match cheating.
2. **Semantic Robustness**: Tested across billing, shipping, technical, and general company inquiries.
3. **Hybrid Fallback**: The retriever searches topic-constrained categories first and falls back to global semantic search to prevent false negatives from classification errors.
