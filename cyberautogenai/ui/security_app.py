import streamlit as st
from typing import Dict, Any
import asyncio
from dotenv import load_dotenv
import os
import sys
from pathlib import Path
import logging
import json
from datetime import datetime
import openai
import nest_asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from cyberautogenai.agents.orchestrator import SecurityOrchestrator
from cyberautogenai.agents.base_agent import BaseAgent
from cyberautogenai.utils.logger import logger

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def setup_event_loop():
    """Set up the event loop for the current thread."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

def run_async_in_thread(coro):
    """Run an async coroutine in a new thread with its own event loop."""
    result = None
    error = None
    
    def run_coro():
        nonlocal result, error
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(coro)
        except Exception as e:
            error = e
        finally:
            loop.close()
    
    # Run in a new thread
    thread = threading.Thread(target=run_coro)
    thread.start()
    thread.join()
    
    if error:
        raise error
    return result

class SecurityApp:
    def __init__(self):
        # Load environment variables from .env before anything else
        load_dotenv(override=True)  # Ensures .env is loaded

        # Debug: Print the VirusTotal API key to verify it's loaded
        print("VIRUSTOTAL_API_KEY:", os.getenv('VIRUSTOTAL_API_KEY'))

        # Get API keys
        self.api_keys = {
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'ABUSEIPDB_API_KEY': os.getenv('ABUSEIPDB_API_KEY'),
            'SHODAN_API_KEY': os.getenv('SHODAN_API_KEY'),
            'VIRUSTOTAL_API_KEY': os.getenv('VIRUSTOTAL_API_KEY'),
        }
        
        # Debug: Print masked API keys
        for key_name, key_value in self.api_keys.items():
            if key_value:
                masked_key = f"{key_value[:4]}...{key_value[-4:]}" if len(key_value) > 8 else "***"
                st.sidebar.info(f"{key_name}: {masked_key}")
                logger.info(f"{key_name} loaded with length: {len(key_value)}")
            else:
                st.sidebar.error(f"{key_name} not found in environment")
                logger.error(f"{key_name} not found in environment")
        
        # Initialize orchestrator asynchronously
        self.orchestrator = run_async_in_thread(SecurityOrchestrator.create(self.api_keys))

    async def _analyze(self, query: str, user_prompt: str):
        """Run analysis asynchronously with debug info."""
        st.info("Starting analysis...")
        st.write("Checking APIs:")

        if 'abuseipdb' in self.orchestrator.agents:
            st.success("✅ AbuseIPDB agent initialized")
        else:
            st.error("❌ AbuseIPDB agent not initialized")

        if 'shodan' in self.orchestrator.agents:
            st.success("✅ Shodan agent initialized")
        else:
            st.error("❌ Shodan agent not initialized")

        # Detect if query is a batch (comma-separated or JSON list)
        try:
            # Try to parse as JSON list
            values = json.loads(query)
            if isinstance(values, list):
                # Batch input
                return await self.orchestrator.analyze_request({"raw_input": {"ips": values}})
        except Exception:
            pass

        # If comma-separated, treat as batch
        if "," in query:
            ip_list = [ip.strip() for ip in query.split(",") if ip.strip()]
            return await self.orchestrator.analyze_request({"raw_input": {"ips": ip_list}})

        # Otherwise, treat as single IP
        return await self.orchestrator.analyze_request({"raw_input": query, "type": "ip"})

    def run(self):
        st.title("Security Analysis Tool")
        
        # Show current configuration
        st.sidebar.title("Configuration Status")
        for key_name, key_value in self.api_keys.items():
            if key_value:
                st.sidebar.success(f"✅ {key_name} configured")
            else:
                st.sidebar.error(f"❌ {key_name} not configured")
        
        # Show agent initialization status
        st.sidebar.title("Agent Initialization")
        for agent_key in ["abuseipdb", "shodan", "virustotal"]:
            if agent_key in self.orchestrator.agents:
                st.sidebar.success(f"✅ {agent_key.capitalize()} agent initialized")
            else:
                st.sidebar.error(f"❌ {agent_key.capitalize()} agent not initialized")
        
        # Initialize session state for results and prompt
        if "results" not in st.session_state:
            st.session_state["results"] = None
        if "last_prompt" not in st.session_state:
            st.session_state["last_prompt"] = None

        query = st.text_input("Enter IP address, domain, or URL to analyze:", "")
        
        # Prompt engineering UI
        default_prompt = (
            "You are a senior cybersecurity analyst. Given the following results from multiple security tools, "
            "write a comprehensive, multi-paragraph report. Your report should include:\n"
            "- An executive summary of the findings\n"
            "- Technical details and context for each tool's results\n"
            "- A risk assessment (Low/Medium/High) with justification\n"
            "- Key security findings and their implications\n"
            "- Actionable recommendations for remediation or further investigation\n"
            "Be verbose, detailed, and use at least 3 paragraphs. "
            "Use clear, professional, and technical language suitable for both technical and management audiences.\n"
            "Your response must be at least 300 words."
        )
        st.subheader("Customize AI Summary Prompt (optional)")
        user_prompt = st.text_area(
            "Edit the prompt for OpenAI (leave as is for default):",
            value=st.session_state.get("last_prompt", default_prompt),
            height=200
        )
        
        if st.button("Analyze"):
            if query:
                try:
                    results = asyncio.run(self._analyze(query, user_prompt))
                    st.session_state["results"] = results
                    st.session_state["last_prompt"] = user_prompt
                    self.display_analysis_results(results)
                except Exception as e:
                    st.error(f"Analysis failed: {str(e)}")
                    logger.error("Analysis error", exc_info=True)
            else:
                st.warning("Please enter an IP address to analyze.")

        st.subheader("Ask a follow-up question about the analysis")
        followup_question = st.text_input("Your follow-up question:", "")

        if st.button("Ask AI"):
            if followup_question:
                if st.session_state["results"] is not None:
                    followup_response = self.ask_followup(followup_question, st.session_state["results"])
                    st.markdown("**AI's Response:**")
                    st.write(followup_response)
                else:
                    st.warning("Please run an analysis first before asking a follow-up question.")
            else:
                st.warning("Please enter a follow-up question.")

    def _format_value(self, value: Any) -> str:
        """Convert any value to a string representation."""
        if isinstance(value, bool):
            return "Yes" if value else "No"
        elif isinstance(value, (dict, list)):
            return json.dumps(value)
        elif value is None:
            return "N/A"
        else:
            return str(value)

    def display_analysis_results(self, results: Dict[str, Any]) -> None:
        """Display security analysis results."""
        st.header("Analysis Results")
        st.write(f"**Target:** {results.get('target', 'N/A')}")
        st.write(f"**Type:** {results.get('type', 'N/A')}")
        st.write(f"**Timestamp:** {results.get('timestamp', 'N/A')}")

        st.subheader("Analysis Summary")
        st.write(results.get('summary', 'No summary available'))
        
        # Display detailed results
        st.subheader("Detailed Results")
        detailed_results = results.get('results', {})
        
        if detailed_results:
            # AbuseIPDB Results
            if 'abuseipdb' in detailed_results:
                with st.expander("🔍 AbuseIPDB Results", expanded=True):
                    st.write(detailed_results['abuseipdb'])
            # Shodan Results
            if 'shodan' in detailed_results:
                with st.expander("🔍 Shodan Results", expanded=True):
                    st.write(detailed_results['shodan'])
            # VirusTotal Results
            if 'virustotal' in detailed_results:
                with st.expander("🔍 VirusTotal Results", expanded=True):
                    vt_data = detailed_results['virustotal']
                    if isinstance(vt_data, dict):
                        for k, v in vt_data.items():
                            st.write(f"- **{k.replace('_', ' ').capitalize()}:** {v}")
                    else:
                        st.write(vt_data)
        else:
            st.warning("No detailed results available")
            logger.warning("No detailed results found in the response")

        # Display any errors at the bottom
        if results.get('error'):
            st.error(f"Analysis Error: {results['error']}")

    def process_chat_input(self, user_input: str) -> Dict[str, Any]:
        """Process chat input through the orchestrator."""
        logger.info(f"Processing chat input: {user_input}")
        try:
            if not st.session_state.orchestrator_initialized:
                raise RuntimeError("Orchestrator not initialized")

            # Use orchestrator's analyze_request method for chat analysis
            results = run_async_in_thread(
                st.session_state.orchestrator.analyze_request({"raw_input": user_input})
            )
            
            if results:
                st.session_state.analysis_results.append(results)
            
            return results

        except Exception as e:
            logger.error(f"Error processing chat input: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "type": "chat_analysis"
            }

    def process_ip_input(self, ip_address: str) -> Dict[str, Any]:
        """Process IP input through the orchestrator."""
        logger.info(f"Processing IP input: {ip_address}")
        try:
            if not st.session_state.orchestrator_initialized:
                raise RuntimeError("Orchestrator not initialized")

            # Use orchestrator's analyze_request method for IP analysis
            results = run_async_in_thread(
                st.session_state.orchestrator.analyze_request({"raw_input": ip_address})
            )
            
            if results:
                st.session_state.analysis_results.append(results)
            
            return results

        except Exception as e:
            logger.error(f"Error processing IP input: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "type": "ip_analysis"
            }

    def _get_secret(self, key: str) -> str:
        """Get secret from Streamlit secrets or environment variables."""
        try:
            return st.secrets.get(key, "")
        except Exception:
            # Fallback to environment variables or empty string
            return os.getenv(key, "")

    def ask_followup(self, question: str, last_results: dict) -> str:
        # Check if OpenAI client is initialized
        if not self.orchestrator.openai_client:
            return "OpenAI client is not initialized. Please check your API key."
        # Compose a prompt that includes the last analysis summary and results
        context = last_results.get("summary", "") + "\n\n" + json.dumps(last_results.get("results", {}), indent=2)
        prompt = (
            f"You are a cybersecurity analyst. Here is the previous analysis:\n{context}\n\n"
            f"User follow-up question: {question}\n"
            "Please answer in detail, referencing the analysis above."
        )
        # Call OpenAI synchronously or asynchronously as appropriate
        try:
            response = run_async_in_thread(
                self.orchestrator.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful cybersecurity assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5,
                    max_tokens=500
                )
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error getting AI response: {e}" 