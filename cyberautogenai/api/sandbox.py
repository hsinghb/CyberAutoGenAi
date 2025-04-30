"""Sandbox API Integration for Malware Analysis."""
from typing import Dict, Any
import aiohttp
import os
from dotenv import load_dotenv

class SandboxAPI:
    """Integration with malware analysis sandbox."""
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("SANDBOX_API_KEY")
        self.base_url = os.getenv("SANDBOX_API_URL")
        self.session = None

    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.api_key}"}
            )

    async def analyze_file(self, file_hash: str) -> Dict[str, Any]:
        """Submit file for sandbox analysis."""
        await self._ensure_session()
        
        try:
            # Submit file for analysis
            async with self.session.post(
                f"{self.base_url}/analyze",
                json={"hash": file_hash}
            ) as response:
                if response.status == 200:
                    submission = await response.json()
                    
                    # Get analysis results
                    return await self._get_analysis_results(
                        submission["task_id"]
                    )
                else:
                    return {
                        "error": f"Submission failed: {response.status}"
                    }
                    
        except Exception as e:
            return {"error": str(e)}

    async def _get_analysis_results(self, task_id: str) -> Dict[str, Any]:
        """Get analysis results from sandbox."""
        try:
            async with self.session.get(
                f"{self.base_url}/results/{task_id}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {
                        "error": f"Failed to get results: {response.status}"
                    }
        except Exception as e:
            return {"error": str(e)}

    async def close(self):
        """Close the API session."""
        if self.session:
            await self.session.close()
            self.session = None 