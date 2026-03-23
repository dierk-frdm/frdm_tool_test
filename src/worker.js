export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/api/company-search" && (request.method === "POST" || request.method === "OPTIONS")) {
      return handleCompanySearch(request, env);
    }

    if (url.pathname === "/api/supplier-enrichment" && (request.method === "POST" || request.method === "OPTIONS")) {
      return handleSupplierEnrichment(request, env);
    }

    if (url.pathname === "/api/document-search" && (request.method === "POST" || request.method === "OPTIONS")) {
      return handleDocumentSearch(request, env);
    }

    return env.ASSETS.fetch(request);
  },
};

async function handleCompanySearch(request, env) {
  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };

  if (request.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return new Response(JSON.stringify({ error: "Invalid JSON" }), {
      status: 400,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  const company = (body.company || "").trim();
  if (!company) {
    return new Response(JSON.stringify({ error: "Company name is required" }), {
      status: 400,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  const apiKey = env.FRDM_ANTHROPIC_API_KEY;
  if (!apiKey) {
    return new Response(JSON.stringify({ error: "API key not configured" }), {
      status: 500,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  const prompt = `You are a supply chain and ESG risk research assistant. Provide a concise company profile for: "${company}"

Return ONLY valid JSON in this exact structure (no markdown, no extra text):
{
  "name": "Official company name",
  "industry": "Primary industry/sector",
  "headquarters": "City, Country",
  "founded": "Year or approximate",
  "employees": "Approximate employee count or range",
  "description": "2-3 sentence overview of what the company does",
  "products_services": ["product or service 1", "product or service 2", "product or service 3"],
  "supply_chain_notes": "1-2 sentences about supply chain relevance, sourcing regions, or manufacturing",
  "esg_highlights": "1-2 sentences on known ESG commitments, controversies, or risk factors",
  "risk_level": "Low | Medium | High",
  "risk_rationale": "One sentence explaining the risk level"
}

If the company is not well known or you are uncertain, still return the JSON with your best estimates and note uncertainty in the description field.`;

  let claudeResponse;
  try {
    claudeResponse = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: "claude-haiku-4-5-20251001",
        max_tokens: 1024,
        messages: [{ role: "user", content: prompt }],
      }),
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: "Failed to reach Claude API" }), {
      status: 502,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  if (!claudeResponse.ok) {
    const errText = await claudeResponse.text();
    return new Response(JSON.stringify({ error: `Claude API error: ${claudeResponse.status}`, detail: errText }), {
      status: 502,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  const claudeData = await claudeResponse.json();
  const rawText = claudeData.content?.[0]?.text || "";

  let companyData;
  try {
    companyData = JSON.parse(rawText);
  } catch {
    // Try to extract JSON from the response if wrapped in markdown
    const match = rawText.match(/\{[\s\S]*\}/);
    if (match) {
      try {
        companyData = JSON.parse(match[0]);
      } catch {
        return new Response(JSON.stringify({ error: "Failed to parse Claude response", raw: rawText }), {
          status: 502,
          headers: { "Content-Type": "application/json", ...corsHeaders },
        });
      }
    }
  }

  return new Response(JSON.stringify(companyData), {
    headers: { "Content-Type": "application/json", ...corsHeaders },
  });
}

async function handleSupplierEnrichment(request, env) {
  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };

  if (request.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return new Response(JSON.stringify({ error: "Invalid JSON" }), {
      status: 400,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  const company = (body.company || "").trim();
  if (!company) {
    return new Response(JSON.stringify({ error: "Company name is required" }), {
      status: 400,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  const apiKey = env.FRDM_ANTHROPIC_API_KEY;
  if (!apiKey) {
    return new Response(JSON.stringify({ error: "API key not configured" }), {
      status: 500,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  const hints = [];
  if (body.country) hints.push(`Known country: ${body.country}`);
  if (body.industry) hints.push(`Known industry: ${body.industry}`);
  const hintText = hints.length ? `\nAdditional context: ${hints.join(". ")}` : "";

  const prompt = `You are a corporate intelligence research assistant. Enrich the following company with detailed firmographic data.

Company: "${company}"${hintText}

Return ONLY valid JSON in this exact structure (no markdown, no extra text):
{
  "input_name": "${company}",
  "legal_name": "Official registered legal name",
  "trade_name": "Trade or brand name if different, otherwise same as legal_name",
  "headquarters_address": "Full street address if known, otherwise null",
  "headquarters_city": "City",
  "headquarters_state": "State or province, or null",
  "headquarters_country": "Country",
  "website": "Primary website URL or null",
  "industry": "Primary industry",
  "sector": "Broader sector (e.g. Manufacturing, Technology, Retail)",
  "employee_count": "Approximate employee count or range (e.g. '5,000-10,000') or null",
  "revenue": "Approximate annual revenue (e.g. '$2B') or null",
  "founded_year": "Year founded as a number, or null",
  "stock_ticker": "Stock ticker symbol and exchange (e.g. 'AAPL - NASDAQ') or null if private",
  "parent_company": "Name of ultimate parent company, or null if independent",
  "ownership_type": "Public | Private | Subsidiary | Government | NGO | Unknown",
  "key_officers": [
    {"role": "CEO", "name": "Full name or null if unknown"},
    {"role": "CFO", "name": "Full name or null if unknown"},
    {"role": "COO", "name": "Full name or null if unknown"}
  ],
  "notable_subsidiaries": ["Subsidiary 1", "Subsidiary 2"],
  "confidence": "High | Medium | Low",
  "notes": "Any caveats, disambiguation notes, or important context"
}

If a field is unknown, use null. For key_officers, include the top executives you are confident about — skip roles you don't know. For notable_subsidiaries, include up to 5 well-known ones only. Set confidence to Low if the company is obscure or ambiguous.`;

  let claudeResponse;
  try {
    claudeResponse = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: "claude-haiku-4-5-20251001",
        max_tokens: 1024,
        messages: [{ role: "user", content: prompt }],
      }),
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: "Failed to reach Claude API" }), {
      status: 502,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  if (!claudeResponse.ok) {
    const errText = await claudeResponse.text();
    return new Response(JSON.stringify({ error: `Claude API error: ${claudeResponse.status}`, detail: errText }), {
      status: 502,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  const claudeData = await claudeResponse.json();
  const rawText = claudeData.content?.[0]?.text || "";

  let enriched;
  try {
    enriched = JSON.parse(rawText);
  } catch {
    const match = rawText.match(/\{[\s\S]*\}/);
    if (match) {
      try {
        enriched = JSON.parse(match[0]);
      } catch {
        return new Response(JSON.stringify({ error: "Failed to parse Claude response", raw: rawText }), {
          status: 502,
          headers: { "Content-Type": "application/json", ...corsHeaders },
        });
      }
    } else {
      return new Response(JSON.stringify({ error: "No JSON in Claude response", raw: rawText }), {
        status: 502,
        headers: { "Content-Type": "application/json", ...corsHeaders },
      });
    }
  }

  return new Response(JSON.stringify(enriched), {
    headers: { "Content-Type": "application/json", ...corsHeaders },
  });
}

async function handleDocumentSearch(request, env) {
  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };

  if (request.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return new Response(JSON.stringify({ error: "Invalid JSON" }), {
      status: 400,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  const supplierName = (body.supplier_name || "").trim();
  const businessEntityId = (body.business_entity_id || "").trim();
  const documentTypes = Array.isArray(body.document_types) ? body.document_types : [];

  if (!supplierName) {
    return new Response(JSON.stringify({ error: "supplier_name is required" }), {
      status: 400,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  const apiKey = env.FRDM_ANTHROPIC_API_KEY;
  if (!apiKey) {
    return new Response(JSON.stringify({ error: "API key not configured" }), {
      status: 500,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  const typesList = documentTypes.length > 0
    ? documentTypes.map(t => `- ${t}`).join("\n")
    : "- Annual Sustainability Report\n- Modern Slavery Statement\n- Code of Conduct\n- GHG Inventory\n- Human Rights Policy";

  const prompt = `You are a corporate sustainability document research assistant. Use web search to find actual documents published by "${supplierName}" — sustainability reports, certifications, policies, and compliance documents.

Search strategy:
1. Search for "${supplierName} sustainability report" to find annual/ESG reports
2. Search for "${supplierName} ISO 14001 certificate" and other certifications listed below
3. Search for "${supplierName} modern slavery statement", "${supplierName} code of conduct", "${supplierName} human rights policy", and similar policy documents
4. Search the company's official website sustainability or responsibility section for document links

Document types to classify against (use the closest match, or "No Type Match"):
${typesList}

Rules:
- Only include documents you actually found via web search with a real, working URL
- The URL must point directly to the PDF or the specific page hosting the document — not just the company homepage
- Do not fabricate or guess URLs
- Include both documents matching the known types AND other relevant ESG/sustainability documents you find
- If the same document covers multiple types, list it once under the most specific type

Return ONLY valid JSON (no markdown, no extra text):
{
  "documents": [
    {
      "document_type": "Type from the list above, or 'No Type Match'",
      "document_name": "Full document title",
      "document_url": "Direct URL to the PDF or the page hosting the document"
    }
  ]
}`;

  let claudeResponse;
  try {
    claudeResponse = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: "claude-sonnet-4-6",
        max_tokens: 4096,
        tools: [{ type: "web_search_20260209", name: "web_search" }],
        messages: [{ role: "user", content: prompt }],
      }),
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: "Failed to reach Claude API" }), {
      status: 502,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  if (!claudeResponse.ok) {
    const errText = await claudeResponse.text();
    return new Response(JSON.stringify({ error: `Claude API error: ${claudeResponse.status}`, detail: errText }), {
      status: 502,
      headers: { "Content-Type": "application/json", ...corsHeaders },
    });
  }

  const claudeData = await claudeResponse.json();

  // With web search, content may have multiple blocks (tool_use, tool_result, text).
  // Extract all text blocks and join them to find the JSON output.
  const rawText = (claudeData.content || [])
    .filter(block => block.type === "text")
    .map(block => block.text)
    .join("");

  let parsed;
  try {
    parsed = JSON.parse(rawText);
  } catch {
    const match = rawText.match(/\{[\s\S]*\}/);
    if (match) {
      try {
        parsed = JSON.parse(match[0]);
      } catch {
        return new Response(JSON.stringify({ error: "Failed to parse Claude response", raw: rawText }), {
          status: 502,
          headers: { "Content-Type": "application/json", ...corsHeaders },
        });
      }
    } else {
      return new Response(JSON.stringify({ error: "No JSON in Claude response", raw: rawText }), {
        status: 502,
        headers: { "Content-Type": "application/json", ...corsHeaders },
      });
    }
  }

  return new Response(JSON.stringify({
    supplier_name: supplierName,
    business_entity_id: businessEntityId,
    documents: parsed.documents || [],
  }), {
    headers: { "Content-Type": "application/json", ...corsHeaders },
  });
}
