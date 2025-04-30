"""VirusTotal API integration module."""
from typing import Dict, Any, Optional, List
import os
import json
import hashlib
import aiohttp
from ..utils.logger import logger
from ..exceptions import APIKeyError, ValidationError, ProcessingError

class VirusTotalAPI:
    """VirusTotal API client for malware analysis."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize VirusTotal API client."""
        self.api_key = api_key or os.getenv('VIRUSTOTAL_API_KEY')
        if not self.api_key:
            logger.warning("VirusTotal API key not found. Some functionality will be limited.")
        
        self.base_url = "https://www.virustotal.com/api/v3"
        self.headers = {
            "x-apikey": self.api_key,
            "accept": "application/json"
        }

    async def scan_file(self, file_path: str) -> Dict[str, Any]:
        """
        Scan a file using VirusTotal API.
        
        Args:
            file_path: Path to the file to scan
            
        Returns:
            Dict containing scan results
        """
        if not self.api_key:
            raise APIKeyError("VirusTotal API key not configured")

        try:
            # Calculate file hash
            file_hash = self._calculate_file_hash(file_path)
            
            # First check if the file has been previously scanned
            try:
                return await self._get_file_report(file_hash)
            except ProcessingError:
                # File hasn't been scanned before, proceed with new scan
                pass

            # Upload and scan file
            async with aiohttp.ClientSession() as session:
                # Get upload URL
                upload_url = await self._get_upload_url(session)
                
                # Upload file
                with open(file_path, 'rb') as file:
                    data = aiohttp.FormData()
                    data.add_field('file', file)
                    
                    async with session.post(upload_url, data=data, headers=self.headers) as response:
                        if response.status != 200:
                            raise ProcessingError(f"File upload failed: {response.status}")
                        
                        result = await response.json()
                        analysis_id = result.get('data', {}).get('id')
                        
                        if not analysis_id:
                            raise ProcessingError("Failed to get analysis ID")
                        
                        # Get analysis results
                        return await self._get_analysis_results(session, analysis_id)

        except Exception as e:
            logger.error(f"Error scanning file with VirusTotal: {str(e)}")
            raise ProcessingError(f"VirusTotal scan failed: {str(e)}")

    async def scan_url(self, url: str) -> Dict[str, Any]:
        """
        Scan a URL using VirusTotal API.
        
        Args:
            url: URL to scan
            
        Returns:
            Dict containing scan results
        """
        if not self.api_key:
            raise APIKeyError("VirusTotal API key not configured")

        try:
            async with aiohttp.ClientSession() as session:
                # Submit URL for scanning
                data = {"url": url}
                async with session.post(
                    f"{self.base_url}/urls",
                    data=data,
                    headers=self.headers
                ) as response:
                    if response.status != 200:
                        raise ProcessingError(f"URL scan submission failed: {response.status}")
                    
                    result = await response.json()
                    analysis_id = result.get('data', {}).get('id')
                    
                    if not analysis_id:
                        raise ProcessingError("Failed to get analysis ID")
                    
                    # Get analysis results
                    return await self._get_analysis_results(session, analysis_id)

        except Exception as e:
            logger.error(f"Error scanning URL with VirusTotal: {str(e)}")
            raise ProcessingError(f"VirusTotal URL scan failed: {str(e)}")

    async def _get_file_report(self, file_hash: str) -> Dict[str, Any]:
        """Get existing file report."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/files/{file_hash}",
                headers=self.headers
            ) as response:
                if response.status == 404:
                    raise ProcessingError("File not previously scanned")
                if response.status != 200:
                    raise ProcessingError(f"Failed to get file report: {response.status}")
                
                return await response.json()

    async def _get_upload_url(self, session: aiohttp.ClientSession) -> str:
        """Get file upload URL."""
        async with session.get(
            f"{self.base_url}/files/upload_url",
            headers=self.headers
        ) as response:
            if response.status != 200:
                raise ProcessingError("Failed to get upload URL")
            
            result = await response.json()
            return result.get('data', '')

    async def _get_analysis_results(
        self,
        session: aiohttp.ClientSession,
        analysis_id: str,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Get analysis results, with retry logic."""
        for _ in range(max_retries):
            async with session.get(
                f"{self.base_url}/analyses/{analysis_id}",
                headers=self.headers
            ) as response:
                if response.status != 200:
                    raise ProcessingError(f"Failed to get analysis results: {response.status}")
                
                result = await response.json()
                status = result.get('data', {}).get('attributes', {}).get('status')
                
                if status == 'completed':
                    return result
                
                await asyncio.sleep(15)  # Wait before retrying
        
        raise ProcessingError("Analysis timed out")

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest() 