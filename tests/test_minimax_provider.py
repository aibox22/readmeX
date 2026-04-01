"""Unit and integration tests for MiniMax provider support."""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure src is on the path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir / "src"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reset_config_cache():
    """Reset the config module's in-process cache between tests."""
    import readmex.config as cfg_module
    cfg_module._config_cache = None
    cfg_module._config_sources = None


# ---------------------------------------------------------------------------
# Unit tests – config.py: MINIMAX_API_KEY auto-detection
# ---------------------------------------------------------------------------

class TestMinimaxAutoDetection:
    """MINIMAX_API_KEY sets LLM provider to MiniMax when no explicit key is given."""

    def setup_method(self):
        _reset_config_cache()

    def teardown_method(self):
        _reset_config_cache()

    def test_minimax_api_key_sets_llm_api_key(self):
        """MINIMAX_API_KEY is used as llm_api_key when LLM_API_KEY is absent."""
        env = {
            "MINIMAX_API_KEY": "test-minimax-key",
        }
        with patch.dict(os.environ, env, clear=False):
            # Remove LLM_API_KEY if present
            os.environ.pop("LLM_API_KEY", None)
            _reset_config_cache()
            from readmex.config import load_config
            cfg = load_config()
        assert cfg["llm_api_key"] == "test-minimax-key"

    def test_minimax_api_key_sets_default_base_url(self):
        """MINIMAX_API_KEY auto-configures https://api.minimax.io/v1 as base URL."""
        env = {"MINIMAX_API_KEY": "test-minimax-key"}
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("LLM_API_KEY", None)
            os.environ.pop("LLM_BASE_URL", None)
            _reset_config_cache()
            from readmex.config import load_config
            cfg = load_config()
        assert cfg["llm_base_url"] == "https://api.minimax.io/v1"

    def test_minimax_api_key_sets_default_model(self):
        """MINIMAX_API_KEY auto-selects MiniMax-M2.7 as default model."""
        env = {"MINIMAX_API_KEY": "test-minimax-key"}
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("LLM_API_KEY", None)
            os.environ.pop("LLM_BASE_URL", None)
            os.environ.pop("LLM_MODEL_NAME", None)
            _reset_config_cache()
            from readmex.config import load_config
            cfg = load_config()
        assert cfg["llm_model_name"] == "MiniMax-M2.7"

    def test_minimax_api_key_does_not_override_explicit_llm_key(self):
        """MINIMAX_API_KEY is ignored when LLM_API_KEY is already set."""
        env = {
            "LLM_API_KEY": "explicit-key",
            "MINIMAX_API_KEY": "test-minimax-key",
        }
        with patch.dict(os.environ, env, clear=False):
            _reset_config_cache()
            from readmex.config import load_config
            cfg = load_config()
        assert cfg["llm_api_key"] == "explicit-key"

    def test_minimax_api_key_does_not_override_explicit_base_url(self):
        """MINIMAX_API_KEY does not overwrite an explicit LLM_BASE_URL."""
        env = {
            "MINIMAX_API_KEY": "test-minimax-key",
            "LLM_BASE_URL": "https://custom.endpoint.com/v1",
        }
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("LLM_API_KEY", None)
            _reset_config_cache()
            from readmex.config import load_config
            cfg = load_config()
        assert cfg["llm_base_url"] == "https://custom.endpoint.com/v1"

    def test_minimax_model_name_can_be_overridden(self):
        """LLM_MODEL_NAME takes precedence over MiniMax default model."""
        env = {
            "MINIMAX_API_KEY": "test-minimax-key",
            "LLM_MODEL_NAME": "MiniMax-M2.7-highspeed",
        }
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("LLM_API_KEY", None)
            os.environ.pop("LLM_BASE_URL", None)
            _reset_config_cache()
            from readmex.config import load_config
            cfg = load_config()
        assert cfg["llm_model_name"] == "MiniMax-M2.7-highspeed"


# ---------------------------------------------------------------------------
# Unit tests – model_client.py: MiniMax detection & temperature clamping
# ---------------------------------------------------------------------------

class TestMiniMaxDetection:
    """_is_minimax correctly identifies MiniMax URLs."""

    def _make_client(self, base_url):
        """Create a ModelClient with a mocked LLM config (no real API calls)."""
        llm_cfg = {
            "base_url": base_url,
            "api_key": "dummy",
            "model_name": "MiniMax-M2.7",
            "max_tokens": 1024,
            "temperature": 0.7,
        }
        t2i_cfg = {
            "base_url": "https://api.openai.com/v1",
            "api_key": "dummy",
            "model_name": "dall-e-3",
            "size": "1024x1024",
            "quality": "standard",
        }
        with patch("readmex.utils.model_client.validate_config"), \
             patch("readmex.utils.model_client.get_llm_config", return_value=llm_cfg), \
             patch("readmex.utils.model_client.get_t2i_config", return_value=t2i_cfg), \
             patch("readmex.utils.model_client.OpenAI"):
            from readmex.utils.model_client import ModelClient
            return ModelClient()

    def test_is_minimax_io_url(self):
        client = self._make_client("https://api.minimax.io/v1")
        assert client._is_minimax("https://api.minimax.io/v1") is True

    def test_is_minimax_chat_url(self):
        client = self._make_client("https://api.minimax.io/v1")
        assert client._is_minimax("https://api.minimax.chat/v1") is True

    def test_is_not_minimax_openai_url(self):
        client = self._make_client("https://api.minimax.io/v1")
        assert client._is_minimax("https://api.openai.com/v1") is False

    def test_is_not_minimax_azure_url(self):
        client = self._make_client("https://api.minimax.io/v1")
        assert client._is_minimax("https://my-res.openai.azure.com/") is False


class TestTemperatureClamping:
    """_get_effective_temperature clamps temperature for MiniMax."""

    def _make_client(self, base_url, temperature):
        llm_cfg = {
            "base_url": base_url,
            "api_key": "dummy",
            "model_name": "MiniMax-M2.7",
            "max_tokens": 1024,
            "temperature": temperature,
        }
        t2i_cfg = {
            "base_url": "https://api.openai.com/v1",
            "api_key": "dummy",
            "model_name": "dall-e-3",
            "size": "1024x1024",
            "quality": "standard",
        }
        with patch("readmex.utils.model_client.validate_config"), \
             patch("readmex.utils.model_client.get_llm_config", return_value=llm_cfg), \
             patch("readmex.utils.model_client.get_t2i_config", return_value=t2i_cfg), \
             patch("readmex.utils.model_client.OpenAI"):
            from readmex.utils.model_client import ModelClient
            client = ModelClient(temperature=temperature)
            client.llm_config = llm_cfg
            return client

    def test_zero_temperature_is_clamped_for_minimax(self):
        client = self._make_client("https://api.minimax.io/v1", 0.0)
        assert client._get_effective_temperature() > 0.0

    def test_negative_temperature_is_clamped_for_minimax(self):
        client = self._make_client("https://api.minimax.io/v1", -0.5)
        assert client._get_effective_temperature() > 0.0

    def test_positive_temperature_unchanged_for_minimax(self):
        client = self._make_client("https://api.minimax.io/v1", 0.7)
        assert client._get_effective_temperature() == pytest.approx(0.7)

    def test_temperature_not_clamped_for_openai(self):
        """For non-MiniMax providers, zero temperature is passed through unchanged."""
        client = self._make_client("https://api.openai.com/v1", 0.0)
        assert client._get_effective_temperature() == pytest.approx(0.0)

    def test_clamped_minimum_is_small_positive(self):
        """Clamped value should be a small positive number (0.01)."""
        client = self._make_client("https://api.minimax.io/v1", 0.0)
        assert 0.0 < client._get_effective_temperature() <= 0.1

    def test_get_current_settings_includes_minimax_flag(self):
        """get_current_settings exposes llm_is_minimax field."""
        client = self._make_client("https://api.minimax.io/v1", 0.7)
        settings = client.get_current_settings()
        assert "llm_is_minimax" in settings
        assert settings["llm_is_minimax"] is True


# ---------------------------------------------------------------------------
# Integration tests – smoke test with mocked HTTP
# ---------------------------------------------------------------------------

class TestMiniMaxIntegration:
    """Smoke tests: ModelClient routes calls correctly when configured for MiniMax."""

    def _make_minimax_client(self, temperature=0.7):
        llm_cfg = {
            "base_url": "https://api.minimax.io/v1",
            "api_key": "minimax-test-key",
            "model_name": "MiniMax-M2.7",
            "max_tokens": 1024,
            "temperature": temperature,
        }
        t2i_cfg = {
            "base_url": "https://api.openai.com/v1",
            "api_key": "dummy-t2i",
            "model_name": "dall-e-3",
            "size": "1024x1024",
            "quality": "standard",
        }
        mock_openai = MagicMock()
        with patch("readmex.utils.model_client.validate_config"), \
             patch("readmex.utils.model_client.get_llm_config", return_value=llm_cfg), \
             patch("readmex.utils.model_client.get_t2i_config", return_value=t2i_cfg), \
             patch("readmex.utils.model_client.OpenAI", return_value=mock_openai):
            from readmex.utils.model_client import ModelClient
            client = ModelClient(temperature=temperature)
            client.llm_config = llm_cfg
            client.llm_client = mock_openai
            return client, mock_openai

    def test_get_answer_uses_minimax_model(self):
        """get_answer passes MiniMax-M2.7 as the model name."""
        client, mock_openai = self._make_minimax_client()
        mock_resp = MagicMock()
        mock_resp.choices[0].message.content = "Hello from MiniMax!"
        mock_openai.chat.completions.create.return_value = mock_resp

        answer = client.get_answer("Say hi")

        assert answer == "Hello from MiniMax!"
        call_kwargs = mock_openai.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "MiniMax-M2.7"

    def test_get_answer_clamps_zero_temperature_for_minimax(self):
        """When temperature=0, get_answer sends a clamped value > 0 to MiniMax."""
        client, mock_openai = self._make_minimax_client(temperature=0.0)
        mock_resp = MagicMock()
        mock_resp.choices[0].message.content = "Response"
        mock_openai.chat.completions.create.return_value = mock_resp

        client.get_answer("Test")

        call_kwargs = mock_openai.chat.completions.create.call_args[1]
        assert call_kwargs["temperature"] > 0.0

    def test_minimax_provider_reported_in_settings(self):
        """Settings dict correctly reports the provider as MiniMax."""
        client, _ = self._make_minimax_client()
        settings = client.get_current_settings()
        assert settings["llm_is_minimax"] is True
        assert settings["llm_base_url"] == "https://api.minimax.io/v1"
        assert settings["llm_model_name"] == "MiniMax-M2.7"
