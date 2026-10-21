"""
Frontend API Client: Encapsulates REST API calls to the FastAPI backend using httpx.
Never touches the database directly.
"""
import os
from typing import Dict, Any, List, Optional
import httpx


class FinanceAPIClient:
    """HTTP Client wrapper for Personal Finance Agent Backend API."""

    def __init__(self, base_url: Optional[str] = None):
        backend_env = os.getenv("BACKEND_API_URL")
        if not backend_env:
            try:
                import streamlit as st
                if "BACKEND_API_URL" in st.secrets:
                    backend_env = str(st.secrets["BACKEND_API_URL"])
            except Exception:
                pass
        raw_url = (base_url or backend_env or "http://127.0.0.1:8000/api/v1").strip()
        if not raw_url.startswith(("http://", "https://")):
            if "localhost" in raw_url or "127.0.0.1" in raw_url:
                raw_url = f"http://{raw_url}"
            else:
                raw_url = f"https://{raw_url}"
        raw_url = raw_url.rstrip("/")
        if not raw_url.endswith("/api/v1"):
            raw_url = f"{raw_url}/api/v1"
        self.base_url = raw_url
        self.token: Optional[str] = None

    def check_health(self) -> bool:
        """Returns True if the backend service is reachable and responsive."""
        try:
            root_url = self.base_url.rsplit("/api/v1", 1)[0]
            resp = httpx.get(f"{root_url}/health", timeout=3.0)
            return resp.status_code == 200
        except Exception:
            return False

    def set_token(self, token: Optional[str]):
        self.token = token

    def _headers(self) -> Dict[str, str]:
        h = {"Accept": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """Internal helper to dispatch HTTP requests with normalized error handling."""
        url = f"{self.base_url}{endpoint}" if endpoint.startswith("/") else f"{self.base_url}/{endpoint}"
        try:
            resp = httpx.request(method, url, **kwargs)
            resp.raise_for_status()
            return resp
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            raise ConnectionError(
                f"Cannot connect to Backend API server at '{self.base_url}'. "
                "Please verify that the FastAPI backend is running (run 'launch.bat' or click 'Start Backend Server')."
            ) from e
        except httpx.HTTPStatusError as e:
            msg = str(e)
            try:
                data = e.response.json()
                if isinstance(data, dict) and "detail" in data:
                    msg = str(data["detail"])
            except Exception:
                pass
            raise RuntimeError(msg) from e

    # Auth Methods
    def signup(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/auth/signup", json=data, timeout=10.0).json()

    def login(self, email: str, password: str) -> Dict[str, Any]:
        return self._request("POST", "/auth/login", json={"email": email, "password": password}, timeout=10.0).json()

    def login_with_google(self, email: Optional[str] = None, id_token: Optional[str] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if email:
            payload["email"] = email
        if id_token:
            payload["id_token"] = id_token
        return self._request("POST", "/auth/google", json=payload, timeout=10.0).json()

    def get_profile(self) -> Dict[str, Any]:
        return self._request("GET", "/auth/me", headers=self._headers(), timeout=10.0).json()

    def update_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PUT", "/auth/me", json=data, headers=self._headers(), timeout=10.0).json()

    # Ingestion & Trace Methods
    def upload_statement(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        files = {"file": (filename, file_bytes, "text/csv")}
        return self._request("POST", "/ingestion/upload", files=files, headers=self._headers(), timeout=60.0).json()

    def get_agent_trace(self, execution_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/orchestrator/trace/{execution_id}", headers=self._headers(), timeout=10.0).json()

    # Transactions Methods
    def get_transactions(self, category: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {}
        if category:
            params["category"] = category
        if search:
            params["search"] = search
        return self._request("GET", "/transactions", params=params, headers=self._headers(), timeout=10.0).json()

    def update_transaction_category(self, txn_id: str, new_category: str) -> Dict[str, Any]:
        return self._request(
            "PUT",
            f"/transactions/{txn_id}/category",
            json={"new_category": new_category, "apply_to_future": True},
            headers=self._headers(),
            timeout=10.0
        ).json()

    # Alerts Methods
    def get_alerts(self) -> List[Dict[str, Any]]:
        return self._request("GET", "/alerts", headers=self._headers(), timeout=10.0).json()

    def submit_alert_feedback(self, alert_id: str, feedback: str) -> Dict[str, Any]:
        return self._request(
            "POST",
            f"/alerts/{alert_id}/feedback",
            json={"feedback": feedback},
            headers=self._headers(),
            timeout=10.0
        ).json()

    # Budgets Methods
    def get_budgets(self) -> List[Dict[str, Any]]:
        return self._request("GET", "/budgets", headers=self._headers(), timeout=10.0).json()

    def update_budgets(self, targets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return self._request("PUT", "/budgets", json=targets, headers=self._headers(), timeout=10.0).json()

    # Advisor Methods
    def get_weekly_advice(self) -> Dict[str, Any]:
        return self._request("GET", "/advisor/weekly", headers=self._headers(), timeout=15.0).json()

    def accept_weekly_recommendations(self, summary_id: str) -> Dict[str, Any]:
        return self._request("POST", f"/advisor/weekly/{summary_id}/accept", headers=self._headers(), timeout=10.0).json()

    # Privacy & Consent Methods
    def get_consent(self) -> Dict[str, Any]:
        return self._request("GET", "/privacy/consent", headers=self._headers(), timeout=10.0).json()

    def update_consent(self, storage: bool, llm: bool) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/privacy/consent",
            json={"transaction_storage_consent": storage, "llm_processing_consent": llm},
            headers=self._headers(),
            timeout=10.0
        ).json()

    def export_data(self) -> Dict[str, Any]:
        return self._request("GET", "/privacy/export", headers=self._headers(), timeout=15.0).json()

    def delete_account(self) -> Dict[str, Any]:
        return self._request("DELETE", "/privacy/account", headers=self._headers(), timeout=15.0).json()

    def get_activity_history(self) -> List[Dict[str, Any]]:
        return self._request("GET", "/privacy/activity-history", headers=self._headers(), timeout=10.0).json()

    # Demo Mode
    def seed_demo(self) -> Dict[str, Any]:
        return self._request("POST", "/demo/seed", timeout=15.0).json()
