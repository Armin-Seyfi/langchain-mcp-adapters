# Lab Proof: Agents that speak MCP fluently

## Project

A LangChain agent connects to HubSpot's hosted MCP server and searches CRM
company records. The agent answers from the tool result and does not write
to the CRM.

## Workflow

1. The MCP client connects to `https://mcp.hubspot.com/` over Streamable HTTP.
2. `langchain-mcp-adapters` discovers the server's tools and exposes them as
   LangChain tools.
3. The LangChain agent receives `search_crm_objects` as its only tool.
4. The tool searches the HubSpot test account for a company.
5. The agent returns only the requested company properties.

Authentication uses a HubSpot OAuth access token loaded locally from `.env`.
The token is not included in this submission.

## Query

> Find the company named HubSpot. Report its name and domain. If the CRM search
> returns no matching record, say so.

## Tool call

Tool: `search_crm_objects`

Input:

```json
{
  "objectType": "companies",
  "query": "HubSpot",
  "properties": ["name", "domain"]
}
Retrieved evidence
The MCP tool returned one matching record:
{
  "name": "HubSpot",
  "domain": "hubspot.com"
}

Internal CRM IDs and record URLs are omitted.
Final output
The company named HubSpot has the following properties:
- Name: HubSpot
- Domain: hubspot.com

Grounding check
The final answer's name and domain match the values returned by
search_crm_objects. No additional company facts were used.
Failure or limitation
A search for test returned zero records. Searching without a text query
returned one company, and searching for HubSpot returned that company.
This demonstrates that an empty search result must not be treated as evidence
that no relevant record exists: the search phrase and searchable properties
affect retrieval.

The Python configuration currently passes a static access token as a bearer
header. HubSpot access tokens expire, so a later run may return 401 Unauthorized until the OAuth connection is refreshed. This implementation
does not automate token refresh.
Scope
This Lab proves that a LangChain agent can discover and call a real remote
MCP tool and produce a response grounded in its result. It does not prove
integration with an on-premises CRM, email server, or SharePoint deployment.
