# Global Supply Chain Regulations — Interactive Map Data
### FRDM.ai | Source Document for Lesson 7: Legislation and Guidelines
*Last Updated: March 2025 | Prepared for interactive web build*

---

> **Document Notes for Web Build:**
> - This dataset powers the interactive map in Lesson 7 (Legislation and Guidelines)
> - Each row is one "pin" or region on the map — clicking it should expand the regulation details
> - Consider color-coding pins by category (see Category column below) or by status (Active vs. Proposed)
> - "Ongoing" entries have no fixed end date — display as active/evergreen
> - The "Simplification Omnibus Proposal" (EU, 2025) is proposed but not enacted — flag visually as "Proposed"
> - PFAS Regulations and Scope 3 Emissions are environmental/climate regulations, not specific to modern slavery — consider whether to include, filter separately, or note the distinction in the UI
> - Map should be filterable by: Region, Category, Year/Status
> - 21 regulations total across 10+ countries/regions

---

## Regulation Dataset

### European Union

**Corporate Sustainability Due Diligence Directive (CSDDD)**
- Year: 2024
- Status: Active
- Category: Human Rights Due Diligence
- Description: Mandates EU companies to identify and mitigate adverse human rights and environmental impacts across supply chains. Larger companies must comply by 2027; others by 2028.

---

**Corporate Sustainability Reporting Directive (CSRD)**
- Year: 2024
- Status: Active
- Category: Sustainability Reporting
- Description: Expands reporting obligations to ~50,000 companies, requiring detailed ESG (Environmental, Social, Governance) disclosures. Effective January 2024.

---

**Simplification Omnibus Proposal**
- Year: 2025
- Status: Proposed *(not yet enacted)*
- Category: Regulatory Reform
- Description: Proposed February 2025 to ease certain sustainability reporting requirements in order to enhance global competitiveness. Impact on CSDDD and CSRD obligations is still being determined.

---

### United States

**California Transparency in Supply Chains Act (CTSCA)**
- Year: 2010
- Status: Active
- Category: Modern Slavery / Forced Labor Disclosure
- Description: Requires large retailers and manufacturers doing business in California to disclose efforts to eradicate slavery and human trafficking from their direct supply chains.

---

**Uyghur Forced Labor Prevention Act (UFLPA)**
- Year: 2021
- Status: Active
- Category: Forced Labor / Trade Enforcement
- Description: Trade ban presuming all goods from Xinjiang, China are made with forced labor. Importers must prove otherwise to avoid U.S. border detention.

---

**Withhold Release Order (WRO)**
- Year: Ongoing
- Status: Active / Evergreen
- Category: Forced Labor / Trade Enforcement
- Description: U.S. Customs and Border Protection (CBP) enforcement action detaining imported goods when there is reasonable suspicion of forced labor. Importers must demonstrate compliance to secure release of detained goods.

---

**PFAS Regulations**
- Year: Ongoing
- Status: Active / Evolving
- Category: Environmental (not modern slavery-specific)
- Description: Increasingly stringent regulations on per- and polyfluoroalkyl substances ("forever chemicals") due to their environmental persistence and associated health risks.
- ⚠️ *Note for web build: This is an environmental regulation, not directly related to modern slavery or forced labor. Consider filtering separately or adding a category label in the UI.*

---

**Customs Trade Partnership Against Terrorism (CTPAT)**
- Year: 2001
- Status: Active
- Category: Supply Chain Security
- Description: U.S. CBP-led supply chain security program requiring importers and trade partners to implement robust security practices against terrorism and smuggling. Some overlap with forced labor prevention.

---

### United States / Canada / Mexico

**United States-Mexico-Canada Agreement (USMCA)**
- Year: 2020
- Status: Active
- Category: Forced Labor / Trade Agreement
- Description: Obligates all three countries to prohibit importation of goods produced with forced or compulsory labor, requiring rigorous supply chain due diligence from businesses operating across all three markets.
- *(Map note: Pin should span or link to all three countries)*

---

### United Kingdom

**UK Modern Slavery Act**
- Year: 2015
- Status: Active
- Category: Modern Slavery Reporting
- Description: Requires commercial organizations operating in the UK with annual turnover of GBP £36M or more to publish annual statements on the steps taken to ensure no slavery or human trafficking exists in their supply chains or business operations.

---

### Germany

**Supply Chain Act (Lieferkettengesetz / LkSG)**
- Year: 2023
- Status: Active
- Category: Human Rights Due Diligence
- Description: Obliges companies with significant German operations to conduct due diligence on human rights and environmental standards throughout their supply chains, including both direct suppliers and indirect supply chain tiers.

---

### France

**French Duty of Vigilance Law (Loi de Vigilance)**
- Year: 2017
- Status: Active
- Category: Human Rights Due Diligence
- Description: Mandates large French companies (5,000+ employees in France or 10,000+ globally) to develop and publicly disclose a vigilance plan identifying and mitigating human rights and environmental harm across their value chains.

---

### Norway

**Norwegian Transparency Act**
- Year: 2022
- Status: Active
- Category: Human Rights Due Diligence
- Description: Effective July 1, 2022. Mandates companies operating in Norway with 50 or more employees to conduct human rights and decent working conditions due diligence across all tiers of their supply chains.

---

### Switzerland

**Swiss Ordinance on Due Diligence and Transparency (VSoTr)**
- Year: 2022
- Status: Active
- Category: Human Rights Due Diligence / Child Labor
- Description: Effective January 1, 2022. Mandates companies in Switzerland to conduct risk-based due diligence and report on child labor prevention and responsible sourcing of conflict minerals.

---

### Japan

**Human Rights Due Diligence Guidance**
- Year: 2022
- Status: Active (Non-binding)
- Category: Human Rights Due Diligence
- Description: Non-binding but comprehensive expectations for businesses in Japan to identify, prevent, and mitigate human rights risks across their supply chains. Aligned with the UN Guiding Principles on Business and Human Rights (UNGPs).
- *(Note: Non-binding — flag differently in UI if distinguishing voluntary vs. mandatory frameworks)*

---

### Australia

**Australian Modern Slavery Act**
- Year: 2018
- Status: Active
- Category: Modern Slavery Reporting
- Description: Requires entities operating in Australia with annual consolidated revenue of AUD $100M or more to submit annual Modern Slavery Statements detailing the actions taken to assess and address modern slavery risks in their operations and supply chains.

---

**NSW Modern Slavery Act (New South Wales)**
- Year: 2018
- Status: Active
- Category: Modern Slavery / Procurement
- Description: Mandates NSW government agencies and state-owned corporations to implement procurement practices that prevent modern slavery. Heightened obligations apply to contracts valued over AUD $150,000.
- *(Map note: State-level regulation within Australia — may need a sub-pin or callout within the Australia marker)*

---

### Canada

**Fighting Against Forced Labour and Child Labour in Supply Chains Act (Bill S-211)**
- Year: 2024
- Status: Active
- Category: Forced Labor / Child Labor Reporting
- Description: Enacted January 1, 2024. Mandates Canadian government and qualifying private-sector entities to annually report on measures taken to identify and mitigate the risks of forced and child labour in their operations and supply chains.

---

### Global

**Scope 3 Emissions Reporting**
- Year: Ongoing
- Status: Active / Evolving
- Category: Environmental (not modern slavery-specific)
- Description: Requires companies to measure and disclose indirect greenhouse gas emissions across the full value chain, including purchased goods, transportation, waste, and product use and disposal.
- ⚠️ *Note for web build: This is a climate/environmental regulation, not directly related to modern slavery. Consider filtering separately or adding a category label in the UI.*

---

## Quick Reference Table

| Region / Country | Regulation | Year | Category | Status |
|---|---|---|---|---|
| European Union | CSDDD | 2024 | Human Rights Due Diligence | Active |
| European Union | CSRD | 2024 | Sustainability Reporting | Active |
| European Union | Simplification Omnibus Proposal | 2025 | Regulatory Reform | Proposed |
| United States | California Transparency in Supply Chains Act (CTSCA) | 2010 | Modern Slavery Disclosure | Active |
| United States | Uyghur Forced Labor Prevention Act (UFLPA) | 2021 | Forced Labor / Trade | Active |
| US / Canada / Mexico | USMCA | 2020 | Forced Labor / Trade Agreement | Active |
| United States | Withhold Release Order (WRO) | Ongoing | Forced Labor / Trade | Active |
| United States | PFAS Regulations | Ongoing | Environmental | Active |
| United States | CTPAT | 2001 | Supply Chain Security | Active |
| United Kingdom | UK Modern Slavery Act | 2015 | Modern Slavery Reporting | Active |
| Germany | Supply Chain Act (LkSG) | 2023 | Human Rights Due Diligence | Active |
| France | Duty of Vigilance Law | 2017 | Human Rights Due Diligence | Active |
| Norway | Norwegian Transparency Act | 2022 | Human Rights Due Diligence | Active |
| Switzerland | Swiss Ordinance (VSoTr) | 2022 | Human Rights Due Diligence | Active |
| Japan | Human Rights Due Diligence Guidance | 2022 | Human Rights Due Diligence | Active (Non-binding) |
| Australia | Australian Modern Slavery Act | 2018 | Modern Slavery Reporting | Active |
| Australia (NSW) | NSW Modern Slavery Act | 2018 | Modern Slavery / Procurement | Active |
| Canada | Bill S-211 | 2024 | Forced Labor / Child Labor | Active |
| Global | Scope 3 Emissions Reporting | Ongoing | Environmental | Active |

---

## Category Legend (for map color-coding)

| Category | Suggested Color | Includes |
|---|---|---|
| Modern Slavery Reporting | Red / Coral | UK MSA, Australian MSA, NSW MSA |
| Human Rights Due Diligence | Orange | CSDDD, LkSG, Duty of Vigilance, Norwegian Transparency Act, VSoTr, Japan HRDD |
| Forced Labor / Trade Enforcement | Dark Red | UFLPA, USMCA, WRO, Bill S-211, CTSCA |
| Sustainability Reporting | Blue | CSRD |
| Environmental | Green | PFAS, Scope 3 |
| Supply Chain Security | Grey | CTPAT |
| Regulatory Reform / Proposed | Yellow / Dashed | Simplification Omnibus |
