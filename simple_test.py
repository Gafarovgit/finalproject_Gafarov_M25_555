import sys
print("Testing imports...")

try:
    from valutatrade_hub.parser_service.config import ParserConfig
    print("✓ ParserConfig imported")
    
    config = ParserConfig()
    print(f"✓ Config created, API Key: {config.EXCHANGERATE_API_KEY}")
    
    from valutatrade_hub.parser_service.usecases import ParserUseCases
    print("✓ ParserUseCases imported")
    
    usecases = ParserUseCases()
    print("✓ ParserUseCases instantiated")
    
    print("\n✅ All imports successful!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
