try:
    print("Testing imports...")
    
    print("1. Testing main package import...")
    import cyberautogenai
    print("✓ Main package import successful")
    
    print("\n2. Testing orchestrator import...")
    from cyberautogenai.agents.orchestrator import SecurityOrchestrator
    print("✓ Orchestrator import successful")
    
    print("\n3. Testing UI import...")
    from cyberautogenai.ui.app import SecurityDashboard
    print("✓ UI import successful")
    
    print("\nAll imports successful!")
except Exception as e:
    print(f"\n❌ Import error: {str(e)}") 