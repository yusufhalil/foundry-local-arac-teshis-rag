from foundry_local_sdk import FoundryLocalManager

manager = FoundryLocalManager("qwen2.5-1.5b")
print("Endpoint:", manager.endpoint)
print("API Key:", manager.api_key)
print("Model ID:", manager.get_model_info("qwen2.5-1.5b").id)