# CyberAutoGenAI Agents Documentation

This document provides in-depth technical documentation for each specialized agent in the CyberAutoGenAI platform. Each agent is responsible for interfacing with a specific security intelligence source, processing input, and returning structured results. AI (OpenAI) is leveraged for summarization, context, and follow-up Q&A.

---

## Orchestrator Agent

### **Purpose**
The Orchestrator Agent is the central intelligence and control component of CyberAutoGenAI. It receives user input (structured or natural language), extracts relevant entities (IPs, domains, URLs), routes them to the appropriate specialized agents, aggregates their results, and leverages AI to generate human-readable summaries and answer follow-up questions.

### **Key Responsibilities**
- **Input Handling:** Accepts both structured (JSON) and unstructured (natural language) input from the UI or API.
- **Entity Extraction:** Uses OpenAI (or regex fallback) to extract IPs, domains, and URLs from free-text input.
- **Agent Routing:** Determines which specialized agents (AbuseIPDB, Shodan, etc.) should process each entity type and dispatches requests accordingly.
- **Result Aggregation:** Collects and merges results from all agents into a unified response.
- **AI Summarization:** Invokes OpenAI to generate a comprehensive, multi-paragraph security summary, including executive summary, technical findings, risk assessment, and recommendations.
- **Follow-up Q&A:** Handles user follow-up questions by providing context-aware answers using OpenAI, referencing previous results and summaries.
- **Prompt Engineering:** Supports user-customizable prompts for AI summary generation, enabling tailored reports for different audiences.

### **Key Methods**
- `analyze_request(request: dict) -> dict`:  
  Main entry point. Handles input parsing, entity extraction, agent routing, result aggregation, and summary generation.
- `extract_entities(user_input: str) -> dict`:  
  Uses OpenAI or regex to extract IPs, domains, and URLs from natural language input.
- `_generate_security_summary(analysis_results: dict, custom_prompt: str = None) -> str`:  
  Calls OpenAI to generate a detailed, security-focused summary.
- `_create_analysis_prompt(analysis_results: dict) -> str`:  
  Builds the prompt for OpenAI, including all agent results and explicit instructions.
- `ask_followup(question: str, last_results: dict) -> str`:  
  Handles follow-up questions by building a context-rich prompt and querying OpenAI.

### **Data Flow**
1. **User Input:** Receives input from the UI (can be a single IP, a list, or a natural language query).
2. **Entity Extraction:** If input is unstructured, extracts entities using OpenAI or regex.
3. **Agent Dispatch:** Routes each entity to the appropriate agent(s) for analysis.
4. **Result Aggregation:** Collects results from all agents.
5. **AI Summary:** Passes results to OpenAI for summary generation.
6. **Response:** Returns a structured response with timestamp, target, type, summary, and detailed results.

### **AI Value Addition**
- **Intelligent Parsing:** Converts human language into actionable, structured data for agents.
- **Rich Summarization:** Produces multi-paragraph, security-specific reports that synthesize findings from all agents.
- **Interactive Q&A:** Enables users to ask follow-up questions and receive context-aware, expert-level answers.
- **Prompt Customization:** Allows users to tailor the AI's summary style and focus.

### **Example Input/Output**
**Input (natural language):**  
`"Check 8.8.8.8 and example.com for threats."`

**Entity Extraction Output:**  
```json
{
  "ips": ["8.8.8.8"],
  "domains": ["example.com"]
}
```

**Final Output:**  
```json
{
  "timestamp": "2025-04-27T12:34:56.789Z",
  "target": "8.8.8.8, example.com",
  "type": "ip_analysis",
  "summary": "The analysis of 8.8.8.8 and example.com reveals ... (multi-paragraph AI summary)",
  "results": {
    "abuseipdb": { ... },
    "shodan": { ... },
    "virustotal": { ... }
  }
}
```

### **Error Handling**
- Handles missing or invalid API keys for agents and OpenAI.
- Returns clear error messages for invalid input or agent failures.
- Falls back to regex extraction and basic summaries if OpenAI is unavailable.

### **Extensibility Notes**
- New agents can be added by implementing an `analyze` method and registering them in the orchestrator.
- Entity extraction can be extended to support new types (e.g., file hashes).
- The AI prompt can be further customized for different reporting needs.

---

## Fine Optimism: Balancing Predictability and Reliability

CyberAutoGenAI is designed with a philosophy of "fine optimism":  
We leverage the creative, predictive power of AI (LLMs) for summarization, entity extraction, and Q&A, while grounding all outputs in reliable, verifiable data from specialized security agents.  
This ensures that users benefit from both the efficiency and insight of AI, and the trustworthiness of authoritative data sources.

- **Predictability:** All core data is gathered from deterministic, specialized agents.
- **Optimism:** AI is used to interpret, summarize, and answer questions, enhancing user understanding and workflow.
- **Reliability:** Raw agent results are always available, and AI outputs are contextualized and traceable.

---

## 1. AbuseIPDB Agent

### **Purpose**
The AbuseIPDB agent queries the [AbuseIPDB](https://www.abuseipdb.com/) API to check if an IP address has been reported for abusive activity. It provides abuse confidence scores, report counts, ISP, country, and other metadata.

### **API Usage**
- **Endpoint:** `https://api.abuseipdb.com/api/v2/check`
- **Authentication:** Requires an API key.
- **Rate Limiting:** Subject to AbuseIPDB's API limits.

### **Key Methods**
- `check_ip(ip: str) -> dict`:  
  Queries AbuseIPDB for a single IP address and returns a structured result.
- `analyze(request: dict) -> dict`:  
  Handles both single and batch IP analysis. Accepts a request like `{"type": "ip", "value": "8.8.8.8"}` or `{"type": "ip", "value": ["8.8.8.8", "1.1.1.1"]}`.

### **Data Flow**
1. Receives a request from the orchestrator with one or more IPs.
2. For each IP, calls `check_ip`.
3. Parses and structures the AbuseIPDB response.
4. Returns a dictionary with status, data, and any errors.

### **AI Value Addition**
- **Summary Generation:**  
  AI summarizes the risk, context, and recommendations based on the AbuseIPDB data.
- **Follow-up Q&A:**  
  AI can answer questions like "What does an abuse confidence score of 80 mean?" or "Is this IP safe to use?"

### **Example Input/Output**
**Input:**  
`{"type": "ip", "value": "8.8.8.8"}`

**Output:**  
```json
{
  "status": "success",
  "data": {
    "abuseConfidenceScore": "0",
    "countryCode": "US",
    "countryName": "United States of America",
    "domain": "google.com",
    "hostnames": ["dns.google"],
    "ipAddress": "8.8.8.8",
    "isPublic": "1",
    "isWhitelisted": "1",
    "isp": "Google LLC",
    "lastReportedAt": "2025-04-27T05:20:00+00:00",
    "totalReports": "225",
    "usageType": "Content Delivery Network",
    "ipVersion": "4"
  }
}
```

### **Error Handling**
- Returns `{"status": "error", "error": "Invalid IP address: ..."}`
- Handles API errors, invalid input, and rate limiting gracefully.

### **Extensibility Notes**
- Can be extended to support additional AbuseIPDB endpoints (e.g., bulk check, blacklist).
- Batch processing is supported natively.

---

## 2. Shodan Agent

### **Purpose**
The Shodan agent queries the [Shodan](https://www.shodan.io/) API to retrieve information about an IP address, such as open ports, vulnerabilities, hostnames, organization, and more.

### **API Usage**
- **Endpoint:** `https://api.shodan.io/shodan/host/{ip}`
- **Authentication:** Requires an API key.
- **Rate Limiting:** Subject to Shodan's API limits.

### **Key Methods**
- `_analyze_ip(ip: str) -> dict`:  
  Queries Shodan for a single IP address.
- `analyze(request: dict) -> dict`:  
  Handles both single and batch IP/domain analysis.

### **Data Flow**
1. Receives a request from the orchestrator with one or more IPs (or domains, if supported).
2. For each IP, calls `_analyze_ip`.
3. Parses and structures the Shodan response.
4. Returns a dictionary with status, data, and any errors.

### **AI Value Addition**
- **Summary Generation:**  
  AI interprets Shodan results, highlights exposed services, and assesses risk.
- **Follow-up Q&A:**  
  AI can answer questions like "What does it mean if port 22 is open?" or "Are there any critical vulnerabilities?"

### **Example Input/Output**
**Input:**  
`{"type": "ip", "value": "1.1.1.1"}`

**Output:**  
```json
{
  "status": "success",
  "data": {
    "ip": "1.1.1.1",
    "ports": [80, 443, 53],
    "hostnames": ["one.one.one.one"],
    "org": "APNIC and Cloudflare DNS Resolver project",
    "country": "Australia",
    "vulns": [],
    "last_update": "2025-04-27T12:14:25.681446",
    "os": null,
    "tags": []
  }
}
```

### **Error Handling**
- Returns `{"status": "error", "error": "Invalid IP"}` for invalid input.
- Handles API errors, invalid input, and rate limiting gracefully.

### **Extensibility Notes**
- Can be extended to support domain lookups, network searches, or other Shodan features.
- Batch processing is supported natively.

---

## MCP (Message Control Protocol)

### **Purpose**
MCP (Message Control Protocol) is the internal messaging and coordination layer of CyberAutoGenAI. It enables decoupled, asynchronous, and potentially distributed communication between the orchestrator and specialized agents. MCP is designed to support scalability, modularity, and future distributed deployments.

### **Key Responsibilities**
- **Message Routing:** Handles the sending and receiving of structured messages (requests and responses) between the orchestrator and agents.
- **Decoupling:** Allows agents and the orchestrator to operate independently, making it easy to add, remove, or update agents without affecting the core system.
- **Asynchronous Operation:** Supports non-blocking, concurrent processing of multiple analysis tasks.
- **Extensibility:** Lays the groundwork for running agents and orchestrator on separate processes, machines, or even across a network.

### **Key Components**
- **MCPServer:**  
  - Runs in the orchestrator.
  - Listens for incoming messages from agents.
  - Dispatches analysis requests and collects results.
- **MCPClient:**  
  - Runs in each agent.
  - Connects to the MCPServer.
  - Sends analysis results and receives tasks.
- **Message:**  
  - Standardized message object for all communication.
  - Contains metadata (type, sender, recipient, timestamp), payload (content), and status.

### **Data Flow**
1. **Task Dispatch:**  
   The orchestrator creates a `Message` containing the analysis request and sends it via MCPServer to the appropriate agent(s).
2. **Agent Processing:**  
   The agent receives the message via MCPClient, processes the request, and prepares a response message.
3. **Result Return:**  
   The agent sends the response message back to the orchestrator via MCP.
4. **Aggregation:**  
   The orchestrator collects all responses, aggregates them, and proceeds with AI summarization and UI output.

### **AI Value Addition**
- **Scalability:**  
  MCP enables the orchestrator to handle many concurrent requests, which is essential for AI-driven, multi-agent analysis.
- **Resilience:**  
  Decoupling via MCP means that if an agent fails or is slow, the orchestrator and other agents can continue operating.
- **Future Distributed AI:**  
  MCP can be extended to support distributed AI agents, such as running heavy AI models on separate hardware.

### **Example Message Structure**
```json
{
  "type": "analysis_request",
  "sender": "orchestrator",
  "recipient": "abuseipdb_agent",
  "timestamp": "2025-04-27T12:34:56.789Z",
  "content": {
    "type": "ip",
    "value": "8.8.8.8"
  },
  "status": "pending"
}
```

### **Error Handling**
- Messages include status fields for error reporting.
- MCP can retry or re-route messages if an agent is unavailable.
- All communication is logged for traceability and debugging.

### **Extensibility Notes**
- MCP can be adapted to use different transport layers (e.g., sockets, HTTP, message queues).
- Supports future features like agent auto-discovery, load balancing, and distributed deployments.
- Message schema can be extended to support new analysis types or agent capabilities.

---

## Next Steps

- [ ] Add documentation for VirusTotal, URLScan, and any other agents.
- [ ] Add a section on MCP usage and AI value addition across the system.
- [ ] Add example workflows and troubleshooting.

---

*This file is auto-generated and should be updated as new agents and features are added.* 