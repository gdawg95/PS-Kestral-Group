# Benchmarks for the Wave 5 value model

**Produced by:** Research agent (w1_research). Brief: `agents/briefs/w1_research.md`. Run report: `agents/reports/w1_research.md`.
**Version:** v2, 30 Oct 2026. Revised at the owner's request to use sources from **2023–2026** and to widen the scope to automotive retail generally and cross-industry customer-experience research. Sources older than 2023 are no longer used in any range. They are kept in Appendix A for cross-checking only, and each is marked as older.
**Status:** draft, awaiting owner review. Unblocks D-025 (value benchmarks and assumptions, low/mid/high). The owner picks the final values (gate G7). This file supplies the evidence.
**Scope:** public sources only. No Kestrel feedback data was used. The only project file read was `monthly_revenue.csv` (aggregate dollars, no personal data), used in §5.

---

## 0. Read this first

1. **No source puts a dollar value on a 1–5 rating.** The newest peer-reviewed evidence (Mittal et al. 2023, a 40-year meta-analysis) finds satisfaction is strongly linked to stated intent to stay (r = 0.65) but only weakly to actual retention behaviour (r = 0.21). Any Wave 5 dollar figure therefore rests on an **assumption** about how a Kestrel 1–2 rating translates into lost business. See §4 and §6.
2. **Recent Australian loyalty data is scarce.** Recent Australian *financial* benchmarks exist: Deloitte 2025/2026 and AADA 2026. Recent Australian *behaviour* data is limited to the Australian slice of the Qualtrics XM Institute 2025 study. The retention and loyalty figures otherwise come from the US (J.D. Power 2026, Cox Automotive 2025) and global studies (Qualtrics 2025). US dollar figures are quoted in **US$ and not converted**.
3. **Two gaps could not be filled with 2023+ data:** dealer service share by car age in Australia, and repurchase probability by satisfaction level. Appendix A shows the older figures for these. Wave 5 should either use them with the "older source" flag or treat the input as an assumption.
4. **Weights:**
   - **High:** industry body, peer-reviewed work, or a large published survey with a stated method, recent and Australian.
   - **Medium:** large published survey with a stated method, recent but foreign, or vendor research with a published method.
   - **Low:** press report, unpublished method, or a figure read off a chart.
   - **Do not use:** could not be traced to a primary source.

---

## 1. Automotive service retention

### 1a. Share of owners who service at a dealership

| # | Figure | Source | Fieldwork / year | Market | Weight |
|---|---|---|---|---|---|
| R1 | Dealer share of all service visits: **29%** in 2025, down from 33% in 2018 | Cox Automotive, *2025 Service Industry Study* [S1] | 2025 | US | **Medium.** Large recent industry study, behavioural. All vehicle ages, US only. |
| R2 | **80%** of new-vehicle buyers say they are likely to return to the dealer for service, but only about a quarter had their first appointment booked at purchase | Cox Automotive 2025 press release [S2] | 2025 | US | **Medium.** Intent, not behaviour. |
| R3 | Service labour sales per new retail unit per month ("retention: relative service size"): **A$2,751** volume, A$3,904 luxury | Deloitte Australia, *2026 Dealership Benchmarks* [S3] | 2025 trading | Australia | **High** as a benchmark Kestrel can compute for itself. Not a customer-share figure. Comes from the top 30% of dealers. |

**Range: share of a dealership's own buyers it keeps for servicing**

| | Value | Basis |
|---|---|---|
| Low | **29%** | US all-age dealer share of visits, behavioural (R1) |
| Mid | **55%** | **Arithmetic midpoint, not a sourced figure.** Cross-check: the older Australian survey (A-1, 2018) shows 57–62% for cars aged 3–5 years. |
| High | **80%** | US new-vehicle buyers' intent to return (R2) |

### 1b. What happens after a poor experience

| # | Figure | Source | Fieldwork / year | Market | Weight |
|---|---|---|---|---|---|
| R4 | After a very poor experience with an **auto dealer**, **23%** of consumers stop spending with it entirely and **38%** decrease spending. Auto dealers lose the highest share of customers of all 20 industries surveyed. | Qualtrics XM Institute, *2025 Global Consumer Trends: Bad Experiences by Industry* (n = 23,730, 23 countries, online panel) [S4][S5] | Q3 2024, published Oct 2024 | Global (incl. Australia) | **Medium.** Large, method stated, auto-dealer-specific, recent. Vendor research institute. Auto-dealer chart values read from the PDF text layout. |
| R5 | **11%** of Australian consumers report a bad experience with an auto dealer (Australia overall: 10%). After bad experiences generally, Australians decrease spending 38% of the time and stop 16% of the time. | Qualtrics XMI 2025 [S5] | Q3 2024 | Australia (n ≈ 1,200) | **Medium.** Australian, but the spending-cut figures are all industries, not auto dealers. |
| R6 | 41% of Australian consumers "will reduce or completely stop spending with a company after a negative experience". About A$66 billion of sales at risk. | Qualtrics XMI analysis via iTWire [S6] | published Nov 2025 | Australia | **Low.** Press report. Study not named, no sample given. |
| R7 | 12% of US dealer repairs are not fixed on the first visit. Of those customers, **only 50%** returned or planned to return to the dealer. | J.D. Power, *2025 U.S. Customer Service Index Study* (n = 55,210) [S7] | Jul–Dec 2024 | US | **Medium.** Large, primary J.D. Power release. Measures one failure type. |
| R8 | At overall satisfaction ≥ 950/1,000, **86%** of mass-market and **88%** of premium customers say they "definitely will" return for paid service. No figures for lower bands are published. | J.D. Power, *2026 U.S. CSI Study* (n = 51,228) [S8][S9] | Jan–Dec 2025, published 12 Mar 2026 | US | **Medium.** Current, large. Top band only, intent. |
| R9 | 88% of consumers say the service experience affects their likelihood to buy again from that dealer | Cox Automotive 2025 [S1][S2] | 2025 | US | **Low** for modelling. Attitude only. |

**Range: share of customers a dealer loses (or loses spend from) after a poor experience**

| | Value | Basis |
|---|---|---|
| Low | **23%** | Stop spending entirely, auto dealers (R4) |
| Mid | **50%** | Did not return after a repair that wasn't fixed (R7) |
| High | **61%** | Stop or decrease spending, auto dealers (23% + 38%, R4) |

The high value includes customers who *reduce* rather than stop spending, so it overstates customer loss. As a share of revenue lost it is still an upper bound. Satisfied baseline for comparison: 86–88% definite return intent at the top satisfaction band (R8).

---

## 2. Customer lifetime value (CLV) for a dealership customer

No source gives an Australian dealership CLV. The figures below are the components. §5 shows how they combine with Kestrel's own revenue data.

### 2a. Servicing stream

| # | Figure | Source | Year | Market | Weight |
|---|---|---|---|---|---|
| C1 | Average dealer spend per service visit **US$261** (general repair US$275). **2.4** visits per year | Cox Automotive 2025 [S1][S2] | 2025 | US | **Medium** (spend). **Low** (visits; read off an unlabelled chart). |
| C2 | Losing a service customer "can represent more than **US$12,000** in potential lifetime service spend" | Cox Automotive 2025 [S2] | 2025 | US | **Low.** No method, horizon or discounting stated. Ceiling check only. |
| C3 | Nearly two-thirds of US owners keep their vehicle five years or more, up from 54% in 2024 | Cox Automotive 2025 [S2] | 2025 | US | **Medium** |
| C4 | Service gross margin **63–65%** (volume), 64–66% (luxury). Parts GP 21–23% | Deloitte 2026 [S3] | 2025 trading | Australia | **High** |
| C5 | Service is **32–34%** of dealer gross profit, parts 12–13%. Back end is 44–47% of GP | Deloitte 2026 [S3]; AADA *Dealernomics 2026* via CarExpert [S10] | 2025–26 | Australia | **High.** Two independent Australian sources agree. |
| C6 | Average Australian passenger vehicle age **11.3 years** (2025). 27% of owners drive a car more than 10 years old, and 51% one six years old or less. | AADA via CarExpert [S10]; Compare the Market survey (n = 1,010, Feb 2025) [S11] | 2025 | Australia | **Medium.** This is vehicle age, **not** how long one owner keeps a car. |

**Not found (2023+):** Australian service visits per customer per year, how long Australian customers stay with one dealer, and the average Australian repair-order value. Kestrel's own revenue per service job (§5) replaces the third.

**Do not use:** "Aussies own their vehicles for an average of 11 years 3 months (BITRE 2023)", from Finder [S12]. BITRE publishes fleet age, not ownership length, so the figure is mislabelled.

### 2b. Repurchase stream

| # | Figure | Source | Year | Market | Weight |
|---|---|---|---|---|---|
| C7 | Total gross profit per **new** vehicle: **A$4,250–4,750** (volume), A$5,500–6,000 (luxury). Used: A$3,000–3,500 | Deloitte 2026 [S3] | 2025 trading | Australia | **High** |
| C8 | Customers who return to the dealer for service are "**30 points** more likely to repurchase" from it | Cox Automotive 2025 [S2] | 2025 | US | **Low–Medium.** Unit and method not stated. |
| C9 | 76% of new-vehicle buyers were highly satisfied with the buying process (a record) and 81% with the dealership. 44% rated it better than their previous purchase, 6% worse. | Cox Automotive, *2025 Car Buyer Journey* (n = 2,300) [S13] | fall 2025, published Jan 2026 | US | **Medium** context. No loyalty figures. |
| C10 | Higher service satisfaction "increases the likelihood customers will purchase another vehicle from the same brand". No figures published. | J.D. Power 2026 CSI [S8] | 2025 | US | **Low.** Direction only. |

**Not found (2023+):** any published repurchase probability by satisfaction level, for any market. The best available is J.D. Power UK 2019: 78% "definitely will" buy from the same dealer at satisfaction 901+, against 43% at 751–900 (Appendix A-3, older source).

**Range: probability a customer buys their next car from the same dealer.** All three values rest on the older UK 2019 source and are flagged as such.

| | Value | Basis |
|---|---|---|
| Low | **43%** | UK 2019, satisfaction 751–900 (A-3). *Older source.* |
| Mid | **60.5%** | **Arithmetic midpoint, not sourced** |
| High | **78%** | UK 2019, satisfaction 901+ (A-3). *Older source.* |

**Range: gross profit per repurchase (A$)**

| | Value | Basis |
|---|---|---|
| Low | **A$3,000** | Used-vehicle GP, bottom of range (C7) |
| Mid | **A$4,500** | Midpoint of the new volume range (C7) |
| High | **A$6,000** | Top of the new luxury range (C7) |

---

## 3. The cost of a lost customer

### 3a. Revenue forgone

This is the CLV from §2 that a customer would have delivered and does not. No independent recent benchmark exists for an Australian dealer. See §5 for the Kestrel-specific arithmetic. Cox's US$12,000 lifetime service figure (C2) is the only recent per-customer number, and its weight is Low.

### 3b. Acquisition cost to replace a customer

| # | Figure | Source | Year | Market | Weight |
|---|---|---|---|---|---|
| L1 | Advertising per new retail unit: **A$179** (volume, 3.7% of gross), A$265 (luxury). Per used unit: A$281 / A$268 | Deloitte 2026 [S3] | 2025 trading | Australia | **High** |
| L2 | Advertising is **5.0%** of gross profit for the benchmark A$100m dealership | AADA *Dealernomics 2026* via CarExpert [S10] | 2026 | Australia | **High** |
| L3 | **US$705** advertising per new vehicle sold (US$543,539 per dealership per year) | NADA Data 2024, via TVB [S14] | 2024 | US | **Medium.** Shows Australian advertising per unit is far lower than US. |

**Range: advertising cost to win one replacement vehicle buyer (A$)**

| | Value | Basis |
|---|---|---|
| Low | **A$179** | Volume, new (L1) |
| Mid | **A$265** | Luxury, new (L1) |
| High | **A$281** | Volume, used (L1) |

These are advertising costs per *sale*. They exclude sales staff time, discounting and CRM, and say nothing about acquiring a *service* customer. **Not found:** a credible acquisition cost for an Australian service customer.

**Do not use:** "acquiring a customer costs 5–25× more than keeping one". It could not be traced to primary data. The Bain page usually cited [S15] states only that "a 5% increase in customer retention produces more than a 25% increase in profit", with a financial-services example and no sample.

---

## 4. Satisfaction score → retention

| # | Finding | Source | Weight |
|---|---|---|---|
| S-1 | Meta-analysis of 535 correlations from 245 studies (combined n ≈ 1.16 million). Satisfaction and retention correlate at **r = 0.60** (95% CI 0.56–0.63; k = 191, n = 738,861). The link is much weaker for **actual behaviour (r = 0.21)** than for **stated intent (r = 0.65)**. The authors could not test whether the relationship is nonlinear. | Mittal, Han, Frennea, Blut, Shaik, Bosukonda & Sridhar (2023), "Customer satisfaction, loyalty behaviors, and firm financial performance: what 40 years of research tells us", *Marketing Letters* 34, 171–187 [S16] | **High.** Peer-reviewed, recent, cross-industry. |
| S-2 | Dealer service satisfaction moves sharply with process basics. Meeting all 10 of J.D. Power's service KPIs gives a score of **979**/1,000. Meeting only 3 gives **632**. Only 26% of customers experience 9 or 10. | J.D. Power 2026 CSI [S8] | **Medium.** Useful for linking Kestrel *themes* to satisfaction. |
| S-3 | At the top satisfaction band, 86–88% "definitely will" return for paid service (R8). After a very poor experience, 23% of auto-dealer customers leave entirely (R4). | [S8][S4] | **Medium** |

**Plain finding:** the literature **does not support converting a 1–5 rating into dollars**. It supports three narrower claims:
1. Satisfaction and retention are strongly associated (r = 0.60), consistently, across 40 years of research.
2. The association with **real** behaviour is much weaker (r = 0.21) than with stated intent. Intent-based gaps such as R2 and R8 overstate the effect.
3. After a very poor experience, auto dealers lose customers at a higher rate than any other industry measured (23% stop outright; Qualtrics 2025).

No published mapping exists from Kestrel's 1–5 scale to J.D. Power or Qualtrics categories. The defensible approach is to treat a **1–2 rating as a proxy for a "poor experience"** (D-004 already defines negative this way), apply the §1b loss range as a scenario, and **label the result as a scenario, not a measurement**.

---

## 5. Applying the benchmarks to Kestrel (worked components for Wave 5)

Kestrel's own aggregates, from `monthly_revenue.csv` (24 dealers × 12 months, Oct 2025 – Sep 2026, all sites incl. the closed VIC09):

| Measure | Value | How calculated |
|---|---:|---|
| Service revenue | A$83,209,460 | sum of `service_revenue_aud` |
| Service jobs | 200,249 | sum of `service_jobs` |
| **Revenue per service job** | **A$415.53** | revenue ÷ jobs |
| Vehicles sold | 16,011 | sum of `vehicles_sold` |
| Sales revenue per vehicle | A$46,463 | `sales_revenue_aud` ÷ vehicles |
| Service jobs per vehicle sold | 12.5 | jobs ÷ vehicles |

These are Kestrel's figures, not benchmarks. Wave 5 should recompute them in code so each number traces to the pipeline.

**Illustrative per-customer components.** This is arithmetic on the ranges above, not new evidence.

| Component | Low | Mid | High | Inputs |
|---|---:|---:|---:|---|
| Service visits per year (**A3, assumption**) | 1.0 | 1.7 | 2.4 | Low: one scheduled service a year (assumption). High: Cox US (C1). Mid: midpoint. |
| Annual service revenue | A$416 | A$706 | A$997 | visits × A$415.53 |
| Annual service gross profit (64%, C4) | A$266 | A$452 | A$638 | revenue × 0.64 |
| Years retained (**A4, assumption**) | 3 | 5 | 6 | Low: typical warranty/capped-price period. Mid: US owners keeping cars 5+ years (C3). High: assumption. |
| Lifetime service GP, undiscounted | A$798 | A$2,260 | A$3,830 | annual GP × years |
| Repurchase GP × probability | A$1,290 | A$2,723 | A$4,680 | §2b ranges, e.g. 43% × A$3,000 |

A Wave 5 "value of fixing X" estimate would then be roughly:
`(customers giving 1–2 ratings about X) × (loss rate, §1b) × (per-customer value above)`.

The owner sets each term under D-025. The customer count must come from the cleaned dataset, and it is a lower bound because only some customers leave feedback (D-006).

---

## 6. Assumptions needed to apply these figures to 24 Australian dealerships

| # | Assumption | Shaky? | Why |
|---|---|---|---|
| A1 | A Kestrel rating of 1–2 is equivalent to a "very poor experience" in Qualtrics' terms, and to a low J.D. Power band. | **Yes, the most important one** | No published mapping exists (§4). |
| A2 | Stated intent to return predicts actual return. | **Yes** | Behaviour correlates with satisfaction at r = 0.21 against 0.65 for intent (S-1). R2 and R8 overstate the effect. |
| A3 | Service visits per customer per year (1.0 / 1.7 / 2.4). | **Yes** | No Australian figure found. The high value is US and read off a chart. |
| A4 | Years a service customer stays (3 / 5 / 6). | **Yes** | No 2023+ Australian source. Mid rests on US ownership data. |
| A5 | Repurchase probabilities from UK 2019 still hold for Australia in 2026. | **Yes** | No 2023+ banded repurchase data found for any market. |
| A6 | Global and US loss rates (Qualtrics, J.D. Power) apply to Australian dealer customers. | Moderate | Qualtrics covers Australia, and Australians report auto-dealer bad experiences at a similar rate (11% vs 13% globally). The auto-dealer *spending-cut* figure is global only. |
| A7 | Kestrel's brands sit in the "volume" segment for Deloitte figures. | Moderate | Brands are fictional with no segment. |
| A8 | Kestrel's service revenue is mostly labour, so the 63–65% service GP margin applies. | Moderate | `monthly_revenue.csv` reports parts separately, which supports this. |
| A9 | US dollar figures are not used directly. | Low | Context only. If used, convert at a stated rate and caveat. |
| A10 | Feedback respondents are representative of all customers. | **Yes** | Coverage is partial, and some collection is selective (D-006, D-020 caveats). |

---

## 7. What Wave 5 can and cannot claim from this

**Can claim:**
- After a very poor experience, car dealers lose customers at the highest rate of 20 industries: 23% stop dealing with the dealer entirely and a further 38% spend less (Qualtrics XM Institute 2025, 23 countries incl. Australia).
- Satisfaction and retention are strongly linked, and the link is consistent across 40 years of research. Its effect on actual behaviour is smaller than surveys of intent suggest (Mittal et al. 2023).
- Service is about a third of an Australian dealer's gross profit (32–34%) at 63–65% margins (Deloitte 2026, AADA 2026). Losing service customers matters financially.
- A **scenario range** (low/mid/high) for the value of reducing negative feedback in one area, provided every input is listed and the result is called a scenario.

**Cannot claim:**
- A measured dollar value per 1-star rating or per negative comment.
- That a rating improvement *will* deliver a given revenue change. The evidence is correlational and largely intent-based.
- An Australian CLV figure as though it were sourced. It is arithmetic on assumptions A3–A5.
- The "5–25× acquisition cost" claim, or the "average Australian ownership of 11 years" claim.
- US dollar figures as Kestrel dollars.

---

## Appendix A. Older sources (pre-2023): cross-check only

User instruction (30 Oct 2026): sources older than 2023 are too old to rely on. They are listed here only where no 2023+ equivalent was found, so Wave 5 can see what the older evidence says.

| # | Figure | Source | Year | Market | Why kept |
|---|---|---|---|---|---|
| A-1 | Dealer share of last service by car age: 84% (1 yr), 72% (2), 62% (3), 60% (4), 57% (5), 50% (6), 27% (7), 24% (8), 28% (9), 12% (10+). 37% of all last services were at a dealer. | AAAA / The Klein Partnership, *Consumer Insights Report* (n = 1,499) [S17] | 2018 | Australia | Only Australian data on dealer share by car age. Commissioned by the independent-repairer lobby. Values read off a chart. |
| A-2 | "Definitely would" return for post-warranty service: 85% highly satisfied vs 10% highly dissatisfied (n = 4,421) | J.D. Power Australia CSI 2013, via GoAuto [S18] | 2013 | Australia | Only Australian satisfaction-band loyalty data found |
| A-3 | "Definitely will" buy or lease from the same dealer: 78% (satisfaction 901+) vs 43% (751–900). Return for paid work: 82% vs 53%. | J.D. Power UK CSI 2019 (n = 6,759) [S19] | 2019 | UK | Newest banded repurchase data found. Used in §2b with a flag. |
| A-4 | Satisfaction ratings and repurchase: the same rating gives different repurchase rates across customer groups, and in one group there is no link at all (n = 100,040 automotive customers) | Mittal & Kamakura (2001), *JMR* 38(1), 131–142 [S20] | 2001 | US | Classic study. Its finding is consistent with S-1 (2023). |

---

## Sources

- [S1] Cox Automotive, *2025 Service Industry Study*. https://www.coxautoinc.com/wp-content/uploads/2025/10/2025-Service-Industry-Study-FINAL.pdf
- [S2] Cox Automotive, "Dealerships capture record fixed ops revenue but lose market share…", 2025. https://www.coxautoinc.com/retail/resources/dealerships-capture-record-fixed-ops-revenue-but-lose-market-share-as-customers-drift-to-general-repair-according-to-cox-automotive-study/
- [S3] Deloitte Australia, *2026 Dealership Benchmarks Report*. https://www.deloitte.com/content/dam/assets-zone1/au/en/docs/industries/2026-Dealership-Benchmarks-Report-Australia.pdf
- [S4] Qualtrics XM Institute, "$3.8 Trillion of Global Sales are at Risk Due to Bad Customer Experiences in 2025", Oct 2024. https://www.qualtrics.com/articles/customer-experience/trillion-sales-at-risk-2025/
- [S5] Qualtrics XM Institute, *2025 Global Consumer Trends: Bad Experiences by Industry* (data snapshot PDF). https://www.qualtrics.com/m/www.xminstitute.com/wp-content/uploads/2024/10/XMI_RR-DS_GlobalBadExperiences20Industry-2025.pdf
- [S6] iTWire, "Poor customer experiences cost Australian businesses $66 billion this peak season", 28 Nov 2025. https://itwire.com/guest-articles/guest-research/poor-customer-experiences-cost-australian-businesses-$66-billion-this-peak-season.html
- [S7] J.D. Power, *2025 U.S. Customer Service Index Study* press release. https://jdpower.com/business/press-releases/2025-us-customer-service-index-csi-study
- [S8] J.D. Power, *2026 U.S. Customer Service Index Study* press release, 12 Mar 2026. https://resolve.jdpower.com/business/press-releases/2026-us-customer-service-index-csi-study
- [S9] J.D. Power, *2026 U.S. CSI Study* (PDF release). https://www.jdpower.com/sites/default/files/file/2026-03-11/2026013%20U.S.%20Customer%20Service%20Index%20%28CSI%29%20Study.pdf
- [S10] CarExpert, "Australians are keeping their cars longer as dealer margins stay thin…", 18 Mar 2026 (citing AADA *Dealernomics 2026*). https://www.carexpert.com.au/car-news/australians-are-keeping-their-cars-longer-as-dealer-margins-stay-thin-and-ev-demand-remains-patchy
- [S11] Compare the Market, *Car ownership and insurance report 2025*. https://www.comparethemarket.com.au/car-insurance/features/car-ownership-and-insurance-report/
- [S12] Finder, "Car statistics" (cited only to reject a figure). https://www.findershopping.com.au/car-statistics/
- [S13] Cox Automotive, *2025 Car Buyer Journey* press release, 13 Jan 2026. https://www.coxautoinc.com/wp-content/uploads/2026/01/2025-Cox-Automotive-Car-Buyer-Journey-Press-Release.pdf
- [S14] TVB, "Data Into Dollars: Key Insights From 2024 NADA Data". https://www.tvb.org/news/industry-news/data-into-dollars-key-insights-from-2024-nada-data/
- [S15] F. Reichheld, Bain & Company, "Prescription for cutting costs". https://www.media.bain.com/Images/BB_Prescription_cutting_costs.pdf
- [S16] V. Mittal et al. (2023), "Customer satisfaction, loyalty behaviors, and firm financial performance: what 40 years of research tells us", *Marketing Letters* 34, 171–187. Record: https://dro.dur.ac.uk/38096. Full text: https://durham-repository.worktribe.com/OutputFile/1904040
- [S17] AAAA / The Klein Partnership, *Consumer Insights Report*, 2018. https://www.aaaa.com.au/wp-content/uploads/2018/10/AAAA-Consumer-Insights-Report_Website-LR.pdf
- [S18] GoAuto, J.D. Power Australia CSI 2013. https://goauto.com.au/amp/22174/dealers-need-to-better-connect-with-customers-study.html
- [S19] J.D. Power, *2019 UK Customer Service Index Study*. https://europe.jdpower.com/node/286
- [S20] V. Mittal & W. A. Kamakura (2001), *Journal of Marketing Research* 38(1), 131–142. https://doi.org/10.1509/jmkr.38.1.131.18832
