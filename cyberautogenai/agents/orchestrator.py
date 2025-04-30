from typing import Dict, Any, Optional, List
import asyncio
import threading
import nest_asyncio
from openai import AsyncOpenAI
from ..utils.logger import logger
import json
from datetime import datetime
from .abuseipdb_agent import AbuseIPDBAgent
from .shodan_agent import ShodanAgent
from .mcp_agent_base import MCPAgentBase
from ..mcp.server import MCPServer
from ..mcp.client import MCPClient
from ..mcp.message import Message
import re
import logging
import shodan
import aiohttp
from .chat_agent import ChatAgent
import streamlit as st
from .virustotal_agent import VirusTotalAgent
print("DEBUG: VirusTotalAgent class loaded from:", VirusTotalAgent, VirusTotalAgent.__module__)
import inspect
print("DEBUG: VirusTotalAgent source file:", inspect.getfile(VirusTotalAgent))

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Set to DEBUG for more detailed logs

# Example mapping: input key -> (agent_key, type_for_agent)
INPUT_AGENT_MAP = {
    "ips":      ("abuseipdb", "ip"),
    "domains":  ("virustotal", "domain"),
    "urls":     ("virustotal", "url"),
    # Add more as needed
}

class SecurityOrchestrator:
    def __init__(self, api_keys: Dict[str, str]):
        """Initialize the Security Orchestrator.
        
        Args:
            api_keys: Dictionary containing API keys for various services
                     Expected keys: OPENAI_API_KEY, ABUSEIPDB_API_KEY, SHODAN_API_KEY
        """
        self.api_keys = api_keys
        self.agents = {}
        self.chat_agent = ChatAgent()
        self.openai_client = None
        if self.api_keys.get('OPENAI_API_KEY'):
            self.openai_client = AsyncOpenAI(api_key=self.api_keys['OPENAI_API_KEY'])
        # Do NOT call self._init_agents() here

    async def start(self):
        """Initialize and start the security orchestrator."""
        try:
            await self._init_agents()
            logger.info(f"Initialized agents: {list(self.agents.keys())}")
        except Exception as e:
            logger.error(f"Failed to start orchestrator: {e}")
            raise

    async def _init_agents(self):
        """Initialize security analysis agents."""
        logger.info("Starting _init_agents...")

        # Initialize AbuseIPDB agent
        if self.api_keys.get('ABUSEIPDB_API_KEY'):
            logger.info("Attempting to initialize AbuseIPDB agent...")
            self.agents['abuseipdb'] = AbuseIPDBAgent(self.api_keys['ABUSEIPDB_API_KEY'])
            logger.info("✅ AbuseIPDB agent initialized")

        # Initialize Shodan agent
        if self.api_keys.get('SHODAN_API_KEY'):
            logger.info("Attempting to initialize Shodan agent...")
            self.agents['shodan'] = ShodanAgent(self.api_keys['SHODAN_API_KEY'])
            logger.info("✅ Shodan agent initialized")

        # Initialize VirusTotal agent with error logging and debug print
        try:
            vt_key = self.api_keys.get('VIRUSTOTAL_API_KEY')
            logger.info(f"VIRUSTOTAL_API_KEY in _init_agents: {vt_key}")
            if vt_key:
                logger.info("Attempting to initialize VirusTotal agent...")
                self.agents['virustotal'] = VirusTotalAgent(vt_key)
                logger.info("✅ VirusTotal agent initialized")
            else:
                logger.warning("VIRUSTOTAL_API_KEY not found; VirusTotal agent not initialized")
        except Exception as e:
            logger.error(f"Failed to initialize VirusTotal agent: {e}")
            import traceback
            traceback.print_exc()

    async def stop(self):
        """Stop the orchestrator and clean up resources."""
        self.agents = {}
        if self.openai_client:
            await self.openai_client.close()
        logger.info("Security orchestrator stopped")

    async def analyze_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process security analysis request."""
        raw_input = request.get("raw_input", "")
        # If input is a string, extract entities
        if isinstance(raw_input, str):
            entities = await self.extract_entities(raw_input)
            # Only keep non-empty, valid values
            raw_input = {k: [v for v in vals if v and isinstance(v, str)] for k, vals in entities.items() if vals}

        if isinstance(raw_input, dict) and "raw_input" in raw_input:
            raw_input = raw_input["raw_input"]

        st.write("harpreet")
        st.write(f"Raw input: {raw_input}")
        tool_results = {}

        if isinstance(raw_input, dict):
            for key, value in raw_input.items():
                if key == "ips":
                    for agent_key in ["abuseipdb", "shodan"]:
                        agent = self.agents.get(agent_key)
                        if agent:
                            logger.info(f"Routing {key} to {agent_key} agent: {value}")
                            if isinstance(value, list):
                                result = {}
                                for v in value:
                                    result[v] = await agent.analyze({"type": "ip", "value": v})
                                tool_results[agent_key] = result
                            else:
                                tool_results[agent_key] = await agent.analyze({"type": "ip", "value": value})
                elif key in ["domains", "urls"]:
                    agent_key, agent_type = INPUT_AGENT_MAP[key]
                    agent = self.agents.get(agent_key)
                    if agent:
                        logger.info(f"Routing {key} to {agent_key} agent: {value}")
                        if isinstance(value, list):
                            result = {}
                            for v in value:
                                result[v] = await agent.analyze({"type": agent_type, "value": v})
                            tool_results[agent_key] = result
                        else:
                            tool_results[agent_key] = await agent.analyze({"type": agent_type, "value": value})
                elif key in INPUT_AGENT_MAP:
                    agent_key, agent_type = INPUT_AGENT_MAP[key]
                    agent = self.agents.get(agent_key)
                    if agent:
                        logger.info(f"Routing {key} to {agent_key} agent: {value}")
                        if isinstance(value, list):
                            result = {}
                            for v in value:
                                result[v] = await agent.analyze({"type": agent_type, "value": v})
                            tool_results[agent_key] = result
                        else:
                            tool_results[agent_key] = await agent.analyze({"type": agent_type, "value": value})
        elif isinstance(raw_input, list):
            input_type = request.get("type")
            if input_type:
                for key, (agent_key, agent_type) in INPUT_AGENT_MAP.items():
                    if input_type == agent_type:
                        agent = self.agents.get(agent_key)
                        if agent:
                            logger.info(f"Routing list to {agent_key} agent: {raw_input}")
                            result = {}
                            for v in raw_input:
                                result[v] = await agent.analyze({"type": agent_type, "value": v})
                            tool_results[agent_key] = result
        elif isinstance(raw_input, str):
            input_type = request.get("type")
            if input_type:
                for key, (agent_key, agent_type) in INPUT_AGENT_MAP.items():
                    if input_type == agent_type:
                        agent = self.agents.get(agent_key)
                        if agent:
                            logger.info(f"Routing string to {agent_key} agent: {raw_input}")
                            tool_results[agent_key] = await agent.analyze({"type": agent_type, "value": raw_input})
        else:
            logger.warning("Unrecognized input format for raw_input.")

        logger.info(f"Final tool_results: {tool_results}")

        # Compose a human-readable target string
        if isinstance(raw_input, dict) and "ips" in raw_input:
            target = ", ".join(str(ip) for ip in raw_input["ips"])
        elif isinstance(raw_input, str):
            target = raw_input
        else:
            target = str(raw_input)

        # Compose type based on input
        if isinstance(raw_input, dict):
            if "urls" in raw_input:
                input_type = "url_analysis"
            elif "domains" in raw_input:
                input_type = "domain_analysis"
            elif "ips" in raw_input:
                input_type = "ip_analysis"
            else:
                input_type = request.get("type", "analysis")
        else:
            input_type = request.get("type", "analysis")

        # Try OpenAI summary, fallback to basic summary if needed
        summary = None
        if self.openai_client and tool_results:
            try:
                custom_prompt = request.get("custom_prompt")
                summary = await self._generate_security_summary({
                    "target": target,
                    "results": tool_results
                }, custom_prompt=custom_prompt)
                # Fallback if OpenAI returns empty or whitespace
                if not summary or not summary.strip():
                    summary = self._create_basic_summary(target, tool_results)
            except Exception as e:
                logger.error(f"Failed to generate OpenAI summary: {e}")
                summary = self._create_basic_summary(target, tool_results)
        else:
            summary = self._create_basic_summary(target, tool_results)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "target": target,
            "type": input_type,
            "summary": summary,
            "results": tool_results
        }

    async def _generate_summary(self, query: str, results: Dict[str, Any]) -> str:
        """Generate a summary of the findings."""
        if not results:
            return "No security findings available. Please check API configurations."

        summary_parts = [f"Security analysis for {query}:"]
        
        # AbuseIPDB summary
        if 'AbuseIPDB' in results:
            abuse_data = results['AbuseIPDB']
            if 'error' in abuse_data:
                summary_parts.append(f"AbuseIPDB: Error - {abuse_data['error']}")
            else:
                score = abuse_data.get('abuseConfidenceScore', 0)
                is_public = abuse_data.get('isPublic', 'unknown')
                total_reports = abuse_data.get('totalReports', 0)
                summary_parts.append(
                    f"AbuseIPDB: Score {score}%, "
                    f"Public: {is_public}, "
                    f"Total Reports: {total_reports}"
                )

        # Shodan summary
        if 'Shodan' in results:
            shodan_data = results['Shodan']
            if 'error' in shodan_data:
                summary_parts.append(f"Shodan: Error - {shodan_data['error']}")
            else:
                ports = len(shodan_data.get('ports', []))
                vulns = len(shodan_data.get('vulns', []))
                summary_parts.append(
                    f"Shodan: {ports} open ports, "
                    f"{vulns} vulnerabilities"
                )

        return "\n".join(summary_parts)

    def _detect_input_type(self, value: str) -> str:
        """Detect the type of input using regex patterns."""
        import re
        import ipaddress
        
        try:
            # Try to parse as IP address
            try:
                ipaddress.ip_address(value)
                return "ip"
            except ValueError:
                pass
            
            # URL pattern
            url_pattern = r'^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$'
            if re.match(url_pattern, value, re.IGNORECASE):
                return "url"
            
            # Domain pattern
            domain_pattern = r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z]{2,6})+$'
            if re.match(domain_pattern, value):
                return "domain"
            
            return "unknown"
            
        except Exception as e:
            logger.error(f"Error in type detection: {e}")
            return "unknown"

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.utcnow().isoformat()

    @classmethod
    async def create(cls, api_keys: Dict[str, str]):
        self = cls(api_keys)
        await self._init_agents()
        return self

    @classmethod
    def create_sync(cls, **kwargs) -> 'SecurityOrchestrator':
        """Synchronous factory method for creating orchestrator."""
        try:
            # Handle different threading contexts
            if threading.current_thread().name == 'ScriptRunner.scriptThread':
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                nest_asyncio.apply()
            else:
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            
            # Create and initialize orchestrator
            instance = cls(**kwargs)
            loop.run_until_complete(instance.start())
            return instance
            
        except Exception as e:
            logger.error(f"Failed to create orchestrator: {e}")
            raise

    async def _handle_response(self, message: Message):
        """Handle incoming response messages."""
        try:
            # Process response
            response_content = await self.process_response(message.content)
            
            # Send response
            response = message.create_response(response_content)
            await self.mcp_server.send_message(response)
            
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            error_response = message.create_response(
                {
                    "error": str(e),
                    "status": "error"
                },
                message_type="error"
            )
            await self.mcp_server.send_message(error_response)

    async def process_response(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Process a response and return a processed result."""
        # This method should be implemented by subclasses to process the response
        raise NotImplementedError("Subclasses must implement process_response")

    async def process_request(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request and return a response.
        
        This method should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement process_request")

    async def _handle_request(self, message: Message):
        """Handle incoming request messages."""
        try:
            # Process request
            response_content = await self.process_request(message.content)
            
            # Send response
            response = message.create_response(response_content)
            await self.mcp_server.send_message(response)
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            error_response = message.create_response(
                {
                    "error": str(e),
                    "status": "error"
                },
                message_type="error"
            )
            await self.mcp_server.send_message(error_response)

    def _init_security_agents(self):
        """Initialize security agents with API keys."""
        # Initialize AbuseIPDB
        if self.api_keys.get('ABUSEIPDB_API_KEY'):
            try:
                self.agents['abuseipdb'] = AbuseIPDBAgent(self.api_keys['ABUSEIPDB_API_KEY'])
                logger.info("AbuseIPDB agent initialized")
            except Exception as e:
                logger.error(f"Failed to initialize AbuseIPDB agent: {e}")

        # Initialize Shodan
        if self.api_keys.get('SHODAN_API_KEY'):
            try:
                self.agents['shodan'] = ShodanAgent(self.api_keys['SHODAN_API_KEY'])
                logger.info("Shodan agent initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Shodan agent: {e}")

    def _create_basic_summary(self, ip: str, results: Dict[str, Any]) -> str:
        """Create a basic summary without AI assistance."""
        summary_parts = [f"Security analysis results for IP: {ip}"]
        
        if 'abuseipdb' in results:  # Updated to use lowercase key
            abuse_data = results['abuseipdb']
            if 'error' not in abuse_data:
                summary_parts.append(
                    f"AbuseIPDB Score: {abuse_data.get('abuseConfidenceScore', 'N/A')}% "
                    f"({abuse_data.get('totalReports', '0')} reports)"
                )
        
        if 'shodan' in results:  # Updated to use lowercase key
            shodan_data = results['shodan']
            if 'error' not in shodan_data:
                ports = shodan_data.get('ports', [])
                summary_parts.append(
                    f"Shodan found {len(ports)} open ports. "
                    f"Organization: {shodan_data.get('org', 'N/A')}"
                )
        
        return ' | '.join(summary_parts)

    async def analyze_ip(self, ip: str) -> Dict[str, Any]:
        """Analyze an IP address using available security tools."""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'target': ip,
            'type': 'ip_analysis',
            'results': {}
        }

        try:
            # Initialize agents if not already done
            if not self.agents:
                await self._init_agents()

            # Get AbuseIPDB results
            if 'abuseipdb' in self.agents:
                abuse_result = await self.agents['abuseipdb'].check_ip(ip)
                logger.info(f"AbuseIPDB result status: {abuse_result.get('status')}")
                
                if abuse_result['status'] == 'success':
                    results['results']['abuseipdb'] = abuse_result['data']
                else:
                    logger.error(f"AbuseIPDB check failed: {abuse_result.get('error')}")
                    results['results']['abuseipdb'] = {'error': abuse_result.get('error')}

            # Get Shodan results
            if 'shodan' in self.agents:
                try:
                    shodan_result = await self.agents['shodan'].lookup_ip(ip)
                    if isinstance(shodan_result, dict) and not shodan_result.get('error'):
                        results['results']['shodan'] = shodan_result
                    else:
                        error_msg = shodan_result.get('error', 'Unknown error')
                        logger.error(f"Shodan lookup failed: {error_msg}")
                        results['results']['shodan'] = {'error': error_msg}
                except Exception as e:
                    logger.error(f"Shodan lookup error: {e}")
                    results['results']['shodan'] = {'error': str(e)}

            # Generate AI summary if available
            if self.openai_client and results['results']:
                try:
                    summary = await self._generate_security_summary(results)
                    results['summary'] = summary
                except Exception as e:
                    logger.error(f"Failed to generate AI summary: {e}")
                    results['summary'] = self._create_basic_summary(ip, results['results'])
            else:
                results['summary'] = self._create_basic_summary(ip, results['results'])

            return results

        except Exception as e:
            error_msg = str(e)
            logger.error(f"IP analysis failed: {error_msg}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'target': ip,
                'type': 'ip_analysis',
                'results': {},
                'summary': f"Analysis failed: {error_msg}"
            }

    async def _generate_security_summary(self, analysis_results: Dict[str, Any], custom_prompt: str = None) -> str:
        """Generate a detailed security analysis summary using AI."""
        if not self.openai_client:
            return self._create_basic_summary(analysis_results['target'], analysis_results['results'])

        try:
            prompt = custom_prompt if custom_prompt else self._create_analysis_prompt(analysis_results)
            logger.info(f"OpenAI prompt:\n{prompt}")  # Log the prompt for debugging

            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a senior cybersecurity analyst. "
                            "Given the following results from multiple security tools, "
                            "write a comprehensive, multi-paragraph report. "
                            "Your report should include:\n"
                            "- An executive summary of the findings\n"
                            "- Technical details and context for each tool's results\n"
                            "- A risk assessment (Low/Medium/High) with justification\n"
                            "- Key security findings and their implications\n"
                            "- Actionable recommendations for remediation or further investigation\n"
                            "Use clear, professional, and technical language suitable for both technical and management audiences."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=600  # Increased for richer output
            )
            summary = response.choices[0].message.content.strip()
            logger.info(f"OpenAI summary:\n{summary}")  # Log the summary for debugging
            return summary if summary else self._create_basic_summary(analysis_results['target'], analysis_results['results'])
        except Exception as e:
            logger.error(f"AI summary generation failed: {str(e)}")
            return self._create_basic_summary(analysis_results['target'], analysis_results['results'])

    def _create_analysis_prompt(self, analysis_results: Dict[str, Any]) -> str:
        target = analysis_results.get('target', 'N/A')
        results = analysis_results.get('results', {})
        prompt_parts = [
            f"Target for analysis: {target}\n",
            "Below are the results from various security tools. Please analyze them in detail:\n"
        ]

        for agent, agent_results in results.items():
            prompt_parts.append(f"{agent.upper()} Results:\n{json.dumps(agent_results, indent=2)}\n")

        prompt_parts.append(
            "Please provide:\n"
            "1. An executive summary of the overall security posture.\n"
            "2. Technical findings and context for each tool.\n"
            "3. A risk assessment (Low/Medium/High) with justification.\n"
            "4. Key security findings and their implications.\n"
            "5. Actionable recommendations for remediation or further investigation.\n"
            "Write in a clear, professional, and technical style."
        )
        return "\n".join(prompt_parts)

    async def process_chat(self, message: str) -> Dict[str, Any]:
        """
        Process a chat message and orchestrate security analysis.
        
        Args:
            message: Natural language message from user
            
        Returns:
            Dict containing analysis results
        """
        try:
            # Process message through chat agent
            chat_result = await self.chat_agent.process_message(message)
            
            # Initialize analysis request
            request = {
                'timestamp': datetime.utcnow().isoformat(),
                'raw_input': message,
                'type': chat_result['analysis_type'],
                'entities': chat_result['entities']
            }
            
            # Perform security analysis based on extracted information
            analysis_result = await self.analyze_request(request)
            
            return {
                **request,
                'results': analysis_result
            }
            
        except Exception as e:
            logger.error(f"Error processing chat message: {e}", exc_info=True)
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e),
                'raw_input': message
            }

    async def process_inputs(self, user_inputs: list[str]) -> dict:
        """
        Process a list of user inputs (e.g., IP addresses or strings containing multiple IPs)
        and return analysis results for each.
        """
        results = {}
        for user_input in user_inputs:
            ip_list = extract_ips(user_input)
            if not ip_list:
                results[user_input] = {"error": "No valid IP address found"}
                continue
            for ip in ip_list:
                for agent_name, agent in self.agents.items():
                    request = {"type": "ip", "value": ip}
                    agent_result = await agent.analyze(request)
                    # Store results by user_input, then agent, then ip
                    if user_input not in results:
                        results[user_input] = {}
                    if agent_name not in results[user_input]:
                        results[user_input][agent_name] = {}
                    results[user_input][agent_name][ip] = agent_result
        return results

    def _extract_ip(self, text: str) -> str:
        import re
        match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text)
        return match.group(0) if match else None

    def _task_keys(self, user_inputs):
        # Helper to yield (agent_name, ip_address, user_input) for each task
        for user_input in user_inputs:
            ip_address = self._extract_ip(user_input)
            if not ip_address:
                continue
            for agent_name in self.agents.keys():
                yield (agent_name, ip_address, user_input)

    async def _run_agent(self, agent_name, agent, ip_address, user_input):
        try:
            return await agent.analyze(ip_address)
        except Exception as e:
            return {"status": "error", "error": str(e), "source": agent_name}

    async def process_json_input(self, input_json: dict) -> dict:
        results = {}
        # Map input keys to agent types and agent instances
        type_agent_map = {
            "ips": {"type": "ip", "agent": self.agents.get("abuseipdb")},
            "domains": {"type": "domain", "agent": self.agents.get("virustotal")},
            "urls": {"type": "url", "agent": self.agents.get("urlscan")},
            # Add more as needed
        }
        for key, config in type_agent_map.items():
            values = input_json.get(key)
            agent = config["agent"]
            if values and agent:
                if isinstance(values, list):
                    result = {}
                    for v in values:
                        result[v] = await agent.analyze({"type": config["type"], "value": v})
                    results[key] = result
                else:
                    results[key] = await agent.analyze({"type": config["type"], "value": values})
        return results

    async def _analyze(self, query: str, user_prompt: str):
        # ... existing code ...
        return await self.analyze_request({"raw_input": query, "custom_prompt": user_prompt})

    async def _analyze_and_display(self, query: str):
        if st.button("Analyze"):
            if query:
                try:
                    results = asyncio.run(self._analyze(query, user_prompt))
                    self.display_analysis_results(results)
                except Exception as e:
                    st.error(f"Analysis failed: {str(e)}")
                    logger.error("Analysis error", exc_info=True)
            else:
                st.warning("Please enter an IP address to analyze.")

    async def extract_entities(self, user_input: str) -> dict:
        """
        Use OpenAI to extract IPs, domains, and URLs from a human-readable string.
        Returns a dict like {"ips": [...], "domains": [...], "urls": [...]}
        """
        if not self.openai_client:
            # Fallback: simple regex extraction
            import re
            ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', user_input)
            domains = re.findall(r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b', user_input)
            urls = re.findall(r'https?://[^\s]+', user_input)
            return {"ips": ips, "domains": domains, "urls": urls}

        prompt = (
            "Extract all IP addresses, domain names, and URLs from the following text. "
            "Return a JSON object with keys 'ips', 'domains', and 'urls'. "
            "If a category is empty, use an empty list. Only return the JSON.\n\n"
            f"Text: {user_input}"
        )
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting entities from text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=300
            )
            import json as pyjson
            content = response.choices[0].message.content.strip()
            # Try to parse the JSON from the response
            entities = pyjson.loads(content)
            return entities
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            # Fallback to regex
            import re
            ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', user_input)
            domains = re.findall(r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b', user_input)
            urls = re.findall(r'https?://[^\s]+', user_input)
            return {"ips": ips, "domains": domains, "urls": urls}