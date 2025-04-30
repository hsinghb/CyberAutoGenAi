"""Test scenarios for Security Analysis UI."""
from typing import Dict, List

class UITestScenarios:
    """Test scenarios for the Security Analysis UI."""
    
    @staticmethod
    def get_url_test_cases() -> List[Dict[str, str]]:
        """Test cases for URL analysis."""
        return [
            {
                "name": "Basic URL Security Check",
                "type": "URL",
                "input": "Analyze https://example.com for security vulnerabilities",
                "expected_sections": ["Risk Level", "Key Threats", "Vulnerabilities", "Recommendations"]
            },
            {
                "name": "Malicious URL Detection",
                "type": "URL",
                "input": "Check if http://suspicious-looking-domain.com is malicious",
                "expected_sections": ["Threat Assessment", "Malicious Indicators"]
            },
            {
                "name": "SSL/TLS Analysis",
                "type": "URL",
                "input": "Analyze SSL configuration of https://banking-site.com",
                "expected_sections": ["SSL/TLS Status", "Certificate Analysis"]
            }
        ]

    @staticmethod
    def get_ip_test_cases() -> List[Dict[str, str]]:
        """Test cases for IP analysis."""
        return [
            {
                "name": "IP Reputation Check",
                "type": "IP",
                "input": "Check reputation of IP 8.8.8.8",
                "expected_sections": ["Reputation Score", "Known Activities"]
            },
            {
                "name": "IP Threat Intelligence",
                "type": "IP",
                "input": "Get threat intelligence for 192.168.1.1",
                "expected_sections": ["Threat Intel", "Geographic Location"]
            },
            {
                "name": "IP Service Analysis",
                "type": "IP",
                "input": "Analyze open ports and services on 10.0.0.1",
                "expected_sections": ["Open Ports", "Service Analysis"]
            }
        ]

    @staticmethod
    def get_domain_test_cases() -> List[Dict[str, str]]:
        """Test cases for domain analysis."""
        return [
            {
                "name": "Domain Reputation",
                "type": "Domain",
                "input": "Analyze reputation of example.com",
                "expected_sections": ["Domain Age", "Reputation Score"]
            },
            {
                "name": "DNS Security",
                "type": "Domain",
                "input": "Check DNS security configuration of google.com",
                "expected_sections": ["DNS Records", "DNSSEC Status"]
            },
            {
                "name": "Domain Infrastructure",
                "type": "Domain",
                "input": "Analyze mail server security for microsoft.com",
                "expected_sections": ["Mail Servers", "SPF Records"]
            }
        ]

    @staticmethod
    def get_file_test_cases() -> List[Dict[str, str]]:
        """Test cases for file analysis."""
        return [
            {
                "name": "Malware Analysis",
                "type": "File",
                "input": "Analyze suspicious.exe for malware",
                "expected_sections": ["Malware Detection", "File Behavior"]
            },
            {
                "name": "Document Security",
                "type": "File",
                "input": "Check security of confidential.pdf",
                "expected_sections": ["Document Analysis", "Metadata Review"]
            },
            {
                "name": "Script Analysis",
                "type": "File",
                "input": "Analyze script.py for security issues",
                "expected_sections": ["Code Review", "Security Issues"]
            }
        ]

    @staticmethod
    def get_code_test_cases() -> List[Dict[str, str]]:
        """Test cases for code analysis."""
        return [
            {
                "name": "Python Security Review",
                "type": "Code",
                "input": """Review this code for security issues:
                def process_user_input(user_input):
                    result = eval(user_input)
                    return result""",
                "expected_sections": ["Vulnerabilities", "Security Fixes"]
            },
            {
                "name": "SQL Injection Check",
                "type": "Code",
                "input": """Check for SQL injection:
                query = f"SELECT * FROM users WHERE id = {user_id}";""",
                "expected_sections": ["SQL Injection Risks", "Secure Alternatives"]
            },
            {
                "name": "API Security Review",
                "type": "Code",
                "input": """Review API endpoint security:
                @app.route('/api/user/<id>')
                def get_user(id):
                    return db.query(f"SELECT * FROM users WHERE id={id}")""",
                "expected_sections": ["API Vulnerabilities", "Security Best Practices"]
            }
        ]

    @staticmethod
    def get_chat_test_cases() -> List[Dict[str, str]]:
        """Test cases for chat interactions."""
        return [
            {
                "name": "Security Best Practices",
                "type": "Other",
                "input": "What are the best practices for securing a web application?",
                "expected_sections": ["Web Security", "OWASP Guidelines"]
            },
            {
                "name": "Threat Modeling",
                "type": "Other",
                "input": "Help me create a threat model for my cloud application",
                "expected_sections": ["Threat Model", "Risk Assessment"]
            },
            {
                "name": "Security Framework",
                "type": "Other",
                "input": "Explain the NIST cybersecurity framework",
                "expected_sections": ["Framework Overview", "Implementation Steps"]
            }
        ]

def run_ui_tests():
    """Manual test execution guide."""
    print("Security Analysis UI Test Guide")
    print("\nTest Categories:")
    
    test_categories = {
        "URL Analysis": UITestScenarios.get_url_test_cases(),
        "IP Analysis": UITestScenarios.get_ip_test_cases(),
        "Domain Analysis": UITestScenarios.get_domain_test_cases(),
        "File Analysis": UITestScenarios.get_file_test_cases(),
        "Code Analysis": UITestScenarios.get_code_test_cases(),
        "Chat Interactions": UITestScenarios.get_chat_test_cases()
    }
    
    for category, tests in test_categories.items():
        print(f"\n{category}:")
        for test in tests:
            print(f"\nTest: {test['name']}")
            print(f"Type: {test['type']}")
            print(f"Input: {test['input']}")
            print("Expected sections:", ", ".join(test['expected_sections']))
            print("-" * 50)

if __name__ == "__main__":
    run_ui_tests() 