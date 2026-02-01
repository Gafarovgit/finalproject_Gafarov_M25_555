import sys
print("Python version:", sys.version)
print("\nPython path:")
for p in sys.path[:5]:
    print(f"  {p}")

print("\nTrying imports...")
try:
    from dotenv import load_dotenv
    print("✓ dotenv loaded")
    load_dotenv()
    import os
    print(f"✓ API Key from env: {os.getenv('EXCHANGERATE_API_KEY', 'NOT FOUND')}")
except Exception as e:
    print(f"✗ dotenv error: {e}")

print("\nTrying to import ParserConfig...")
try:
    from valutatrade_hub.parser_service.config import ParserConfig
    print("✓ ParserConfig imported")
    config = ParserConfig()
    print(f"✓ Config created, API Key: {config.EXCHANGERATE_API_KEY[:10]}...")
except Exception as e:
    print(f"✗ ParserConfig error: {e}")
    import traceback
    traceback.print_exc()

print("\nTrying to import ParserUseCases...")
try:
    from valutatrade_hub.parser_service.usecases import ParserUseCases
    print("✓ ParserUseCases imported")
except Exception as e:
    print(f"✗ ParserUseCases error: {e}")
    import traceback
    traceback.print_exc()
