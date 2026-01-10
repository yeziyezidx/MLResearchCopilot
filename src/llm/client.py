"""
LLM Client - OpenAI / Papyrus (Bing Internal)
"""
from typing import Optional, Dict, Any, List
import json
import threading
import time


class LLMClient:
    """LLM Client for OpenAI Azure or Papyrus endpoint (Azure/Bing internal)"""
    
    def __init__(
        self,
        provider: str = "openai",  # "openai" or "papyrus"
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        base_url: Optional[str] = None,
        papyrus_quota_id: Optional[str] = None,
        papyrus_timeout_ms: str = "100000",
        papyrus_verify_scope: str = "api://5fe538a8-15d5-4a84-961e-be66cd036687/.default",
    ):
        """
        Initialize LLM client.
        
        Args:
            api_key: API key for OpenAI provider (optional if using papyrus)
            model: model name for OpenAI provider
            base_url: API base URL for OpenAI or full papyrus endpoint (optional)
            provider: "openai" or "papyrus"
            azure_credential: an Azure credential object (DefaultAzureCredential recommended) or None
            papyrus_quota_id: quota id header for papyrus
            papyrus_model_name: papyrus model name header
            papyrus_timeout_ms: papyrus timeout header (ms)
            papyrus_verify_scope: scope used to request Azure access token for papyrus
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.provider = provider.lower()
        self.client = None
        self._requests = None
        self._papyrus_quota_id = papyrus_quota_id
        self._papyrus_model_name = model
        self._papyrus_timeout_ms = papyrus_timeout_ms
        self._papyrus_verify_scope = papyrus_verify_scope

        # sensible papyrus default endpoint if using papyrus and none provided
        if self.provider == "papyrus":
            self.base_url = self.base_url or "https://westus2.papyrus.binginternal.com/chat/completions"
        else:
            self.base_url = self.base_url or "https://api.openai.com/v1"
        # Rate limiting settings
        self.REQUEST_DELAY = 0.5  # Seconds to wait between API requests (adjust as needed)
        self._rate_limit_lock = threading.Lock()
        self._last_request_time = 0.0

        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize underlying client/session for the selected provider."""
        if self.provider == "openai":
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            except Exception:
                # fall back to mock if openai not available
                print("Warning: openai client not available, will use mock client")
                self.client = None
        elif self.provider == "papyrus":
            try:
                import requests  # local import so caller can run without requests if not needed
                self._requests = requests
            except Exception:
                print("Warning: requests library not installed, will use mock client")
                self._requests = None

            # ensure we have an Azure credential
            if self.provider == "papyrus":
                try:
                    from azure.identity import DefaultAzureCredential
                    self._azure_credential = DefaultAzureCredential()
                    # Default headers (static, won't change)
                    self.DEFAULT_HEADERS = {
                        "Content-Type": "application/json",
                        "papyrus-quota-id": self._papyrus_quota_id,
                        "papyrus-timeout-ms": self._papyrus_timeout_ms,
                        "x-policy-id": "nil",
                    }
                except Exception:
                    # credential not available; papyrus will not work
                    print("Warning: azure.identity can't be imported, Papyrus mode unavailable, will use mock client")
                    self._azure_credential = None
        else:
            # unknown provider -> mock
            print(f"Warning: unknown provider {self.provider}, will use mock client")
            self.client = None



    def _rate_limit_wait(self):
        """Enforce rate limiting between API requests."""
        with self._rate_limit_lock:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            if time_since_last < self.REQUEST_DELAY:
                time.sleep(self.REQUEST_DELAY - time_since_last)
            self._last_request_time = time.time()

    def _get_papyrus_headers(self) -> Dict[str, str]:
        """Construct papyrus headers, refreshing token if possible."""
        cur_headers = self.DEFAULT_HEADERS.copy()
        # get fresh access token
        token = None
        if self._azure_credential:
            try:
                token = self._azure_credential.get_token(self._papyrus_verify_scope).token
            except Exception as e:
                print(f"Failed to get Papyrus access token: {e}")
                token = None
        if token:
            cur_headers["Authorization"] = "Bearer " + token
            cur_headers["papyrus-model-name"] = self._papyrus_model_name

        return cur_headers

    def call(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        output_format: str = "text",
    ) -> str:
        """
        Call LLM (OpenAI or Papyrus).
        Returns a string response (or mock if no client available).
        """
        if self.provider == "openai":
            if not self.client:
                return self._mock_response(prompt)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens or 2000,
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"LLM Calling Failed: {e}")
                return self._mock_response(prompt)

        elif self.provider == "papyrus":
            if not self._requests or not self._azure_credential:
                return self._mock_response(prompt)
            headers = self._get_papyrus_headers()
            body = {
                "messages": [],
                "max_tokens": max_tokens or 2000,
                "temperature": temperature,
            }
            if system_prompt:
                body["messages"].append({"role": "system", "content": system_prompt})
            body["messages"].append({"role": "user", "content": prompt})
            try:
                self._rate_limit_wait()
                resp = self._requests.post(self.base_url, headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"Papyrus LLM Calling Failed: {e}")
                return self._mock_response(prompt)
        else:
            return self._mock_response(prompt)
    
    def call_with_function(
        self,
        prompt: str,
        functions: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Call LLM with function definitions. Supports OpenAI and Papyrus (if Papyrus supports functions).
        Returns a dict describing either a function call or text response.
        """
        if self.provider == "openai":
            if not self.client:
                return {"type": "text", "content": self._mock_response(prompt)}
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    functions=functions,
                    function_call="auto",
                )
                choice = response.choices[0]
                if choice.message.function_call:
                    return {
                        "type": "function_call",
                        "function_name": choice.message.function_call.name,
                        "arguments": json.loads(choice.message.function_call.arguments),
                    }
                else:
                    return {"type": "text", "content": choice.message.content}
            except Exception as e:
                print(f"LLM Function Calling Failed: {e}")
                return {"type": "text", "content": self._mock_response(prompt)}

        elif self.provider == "papyrus":
            if not self._requests or not self._azure_credential:
                return {"type": "text", "content": self._mock_response(prompt)}
            headers = self._get_papyrus_headers()
            body = {
                "messages": [],
                "functions": functions,
                "function_call": "auto",
            }
            if system_prompt:
                body["messages"].append({"role": "system", "content": system_prompt})
            body["messages"].append({"role": "user", "content": prompt})
            try:
                self._rate_limit_wait()
                resp = self._requests.post(self.base_url, headers=headers, json=body, timeout=int(self._papyrus_timeout_ms) / 1000)
                resp.raise_for_status()
                data = resp.json()
                choice = data["choices"][0]["message"]
                # Papyrus structure may differ; try to detect function_call
                function_call = choice.get("function_call") or (choice.get("function") if "function" in choice else None)
                if function_call:
                    # argument string may be in different key names
                    args_str = function_call.get("arguments") or function_call.get("args") or "{}"
                    try:
                        args = json.loads(args_str)
                    except Exception:
                        args = {"raw": args_str}
                    return {
                        "type": "function_call",
                        "function_name": function_call.get("name"),
                        "arguments": args,
                    }
                else:
                    return {"type": "text", "content": choice.get("content")}
            except Exception as e:
                print(f"Papyrus LLM Function Calling Failed: {e}")
                return {"type": "text", "content": self._mock_response(prompt)}
        else:
            return {"type": "text", "content": self._mock_response(prompt)}
    
    @staticmethod
    def _mock_response(prompt: str) -> str:
        """Generate mock response (used when real client not available)."""
        return "This is a mock response. Please configure a real LLM API key or enable Papyrus credentials."
# ...existing code...
