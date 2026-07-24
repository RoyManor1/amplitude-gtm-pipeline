# Clay Configuration Reference

Everything needed to reproduce the Clay side of the pipeline.

## Column 1 — "Company Type" (Claygent, GPT 5.4 Nano · 1 credit/row)

> Your job is to determine if a company is a SaaS (software as a service) company. Things like 'demo request' or 'free trial' are often signs they are a software company. 'Product' or 'platform' in the nav are all good signs. Here is the website: {{website_url}}. Respond 'SaaS' if it's a SaaS company. Otherwise, do your best to label the type of company.

No run condition — runs on every live row.

## Column 2 — "PLG vs SLG" (Claygent, Argon · 3 credits/row)

> Your job is to determine if a SaaS company is product-led or sales-led. Sales-led companies do NOT have a free trial or 'self serve' option on the website. These websites only have a 'contact sales' or 'demo request' or 'book demo' button. If the website only has options to submit a contact form for a sales meeting, the company is 'sales-led.' If the company has a 'free trial' or 'get started' or 'sign up' or 'try for free' button on the website, it's likely a 'product-led' company. Here is the website: {{website_url}}. If the company is sales-led, respond 'Sales-led'. If the company is product-led, respond 'Product-led'. Only respond product-led if you're at least 80% sure. Otherwise, it's probably sales-led.

**Run condition** (only spend on verified SaaS):

```js
{{Company Type}}?.response?.trim()?.toLowerCase()==="saas"
```

Note: the naive formula `{{Company Type}}?.toLowerCase()` fails silently — the token
returns the cell *object*, not its text. Reference the `.response` field explicitly,
and always check the Will run / Will not run preview before saving.

## Column 3 — "Find Employee Headcount by Criteria" (0.5 credits/row, charged only on results)

- Company Identifier: `website_url`
- Job Title Keywords: `product manager`, `head of product`, `VP product`, `chief product officer`, `CPO`
- Output column: **Role Count**
- Same run condition as Column 2.

## Column 4 — "Lead Score" (formula, free)

```js
((p,c,r)=>((p?.response?.toLowerCase()?.startsWith("product-led")?5:0)
 + (c?.response?.trim()?.toLowerCase()==="saas"?3:0)
 + (Number(r)||0)))({{PLG vs SLG}},{{Company Type}},{{Rolecount}})
```

Scoring: **+5** Product-led · **+3** SaaS · **+1 per PM** · threshold for activation: **≥ 8**
