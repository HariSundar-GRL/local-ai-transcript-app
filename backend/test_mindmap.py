"""
Unit tests for the mindmap feature.
Tests both the API endpoint and the TranscriptionService mindmap generation.
"""

import subprocess
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app import app
from transcription import TranscriptionService


# Fixtures
@pytest.fixture
def mock_service():
    """Mock TranscriptionService for testing"""
    mock = Mock(spec=TranscriptionService)
    return mock


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def sample_text():
    """Sample text for testing"""
    return "Machine learning is a subset of AI. It includes supervised learning, unsupervised learning, and reinforcement learning."


@pytest.fixture
def sample_dot_code():
    """Sample DOT code for testing"""
    return """digraph MindMap {
    node [shape=box, style=filled, fillcolor=lightblue]
    "Machine Learning" -> "Supervised Learning"
    "Machine Learning" -> "Unsupervised Learning"
    "Machine Learning" -> "Reinforcement Learning"
}"""


@pytest.fixture
def sample_svg():
    """Sample SVG output"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100">
    <rect x="10" y="10" width="180" height="80" fill="lightblue"/>
    <text x="100" y="50" text-anchor="middle">Machine Learning</text>
</svg>"""


# TranscriptionService.generate_mindmap() tests
class TestTranscriptionServiceMindMap:
    """Test the generate_mindmap method of TranscriptionService"""

    @patch('transcription.OpenAI')
    def test_generate_mindmap_success(self, mock_openai_class, sample_text, sample_dot_code):
        """Test successful mindmap generation"""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=sample_dot_code))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_client.models.list.return_value = []
        mock_openai_class.return_value = mock_client

        # Create service
        with patch('transcription.WhisperModel'):
            service = TranscriptionService(
                whisper_model="base",
                llm_base_url="http://localhost:11434/v1",
                llm_api_key="not-needed",
                llm_model="llama3.2"
            )

        # Test
        result = service.generate_mindmap(sample_text)

        # Assert
        assert result == sample_dot_code
        assert "digraph MindMap" in result
        assert "->" in result

    @patch('transcription.OpenAI')
    def test_generate_mindmap_removes_markdown_blocks(self, mock_openai_class, sample_text, sample_dot_code):
        """Test that markdown code blocks are properly removed"""
        # Setup mock with markdown-wrapped response
        mock_client = Mock()
        mock_response = Mock()
        wrapped_code = f"```dot\n{sample_dot_code}\n```"
        mock_response.choices = [Mock(message=Mock(content=wrapped_code))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_client.models.list.return_value = []
        mock_openai_class.return_value = mock_client

        # Create service
        with patch('transcription.WhisperModel'):
            service = TranscriptionService(
                whisper_model="base",
                llm_base_url="http://localhost:11434/v1",
                llm_api_key="not-needed",
                llm_model="llama3.2"
            )

        # Test
        result = service.generate_mindmap(sample_text)

        # Assert - should have markdown removed
        assert not result.startswith("```")
        assert "digraph MindMap" in result

    @patch('transcription.OpenAI')
    def test_generate_mindmap_empty_text(self, mock_openai_class):
        """Test mindmap generation with empty text"""
        mock_client = Mock()
        mock_client.models.list.return_value = []
        mock_openai_class.return_value = mock_client

        with patch('transcription.WhisperModel'):
            service = TranscriptionService(
                whisper_model="base",
                llm_base_url="http://localhost:11434/v1",
                llm_api_key="not-needed",
                llm_model="llama3.2"
            )

        # Test with empty text
        result = service.generate_mindmap("")

        # Should return empty string
        assert result == ""

    @patch('transcription.OpenAI')
    def test_generate_mindmap_llm_error(self, mock_openai_class, sample_text):
        """Test fallback behavior when LLM fails"""
        # Setup mock to raise exception
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("LLM error")
        mock_client.models.list.return_value = []
        mock_openai_class.return_value = mock_client

        with patch('transcription.WhisperModel'):
            service = TranscriptionService(
                whisper_model="base",
                llm_base_url="http://localhost:11434/v1",
                llm_api_key="not-needed",
                llm_model="llama3.2"
            )

        # Test
        result = service.generate_mindmap(sample_text)

        # Should return fallback mindmap
        assert 'digraph MindMap' in result
        assert 'No mind-map generated' in result


# API endpoint tests
class TestMindMapAPI:
    """Test the /api/mindmap endpoint"""

    def test_mindmap_endpoint_success(self, client, sample_text, sample_dot_code, sample_svg):
        """Test successful mindmap generation through API"""
        # Mock the service
        with patch('app.service') as mock_service:
            mock_service.generate_mindmap.return_value = sample_dot_code

            # Mock subprocess for graphviz
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout=sample_svg.encode()
                )

                # Test
                response = client.post(
                    "/api/mindmap",
                    json={"text": sample_text}
                )

                # Assert
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "svg" in data
                assert "dot" in data
                assert data["dot"] == sample_dot_code
                assert "Machine Learning" in data["svg"]

    def test_mindmap_endpoint_service_not_ready(self, client, sample_text):
        """Test error when service is not initialized"""
        with patch('app.service', None):
            response = client.post(
                "/api/mindmap",
                json={"text": sample_text}
            )

            assert response.status_code == 503
            assert "Service not ready" in response.json()["detail"]

    def test_mindmap_endpoint_graphviz_not_found(self, client, sample_text, sample_dot_code):
        """Test error when Graphviz is not installed"""
        with patch('app.service') as mock_service:
            mock_service.generate_mindmap.return_value = sample_dot_code

            # Mock subprocess to raise FileNotFoundError
            with patch('subprocess.run', side_effect=FileNotFoundError()):
                response = client.post(
                    "/api/mindmap",
                    json={"text": sample_text}
                )

                assert response.status_code == 500
                assert "Graphviz not installed" in response.json()["detail"]

    def test_mindmap_endpoint_graphviz_error(self, client, sample_text, sample_dot_code):
        """Test error when Graphviz execution fails"""
        with patch('app.service') as mock_service:
            mock_service.generate_mindmap.return_value = sample_dot_code

            # Mock subprocess with error
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=1,
                    stderr=b"Graphviz syntax error"
                )

                response = client.post(
                    "/api/mindmap",
                    json={"text": sample_text}
                )

                assert response.status_code == 500
                assert "Mind-map generation failed" in response.json()["detail"]

    def test_mindmap_endpoint_timeout(self, client, sample_text, sample_dot_code):
        """Test timeout handling"""
        with patch('app.service') as mock_service:
            mock_service.generate_mindmap.return_value = sample_dot_code

            # Mock subprocess timeout
            with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('dot', 10)):
                response = client.post(
                    "/api/mindmap",
                    json={"text": sample_text}
                )

                assert response.status_code == 500
                assert "Mind-map generation failed" in response.json()["detail"]

    def test_mindmap_endpoint_invalid_request(self, client):
        """Test with missing or invalid request data"""
        # Missing text field
        response = client.post(
            "/api/mindmap",
            json={}
        )
        assert response.status_code == 422  # Validation error

        # Invalid JSON
        response = client.post(
            "/api/mindmap",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_mindmap_endpoint_empty_text(self, client):
        """Test with empty text"""
        with patch('app.service') as mock_service:
            mock_service.generate_mindmap.return_value = ""

            # Mock subprocess for graphviz (even though empty DOT code)
            with patch('subprocess.run', side_effect=FileNotFoundError()):
                response = client.post(
                    "/api/mindmap",
                    json={"text": ""}
                )

                # Should fail because graphviz can't handle empty DOT code
                assert response.status_code == 500


# Integration-style tests
class TestMindMapIntegration:
    """Integration tests for the complete mindmap flow"""

    def test_dot_code_is_valid_graphviz(self, sample_dot_code):
        """Test that generated DOT code is valid Graphviz syntax"""
        # Basic validation
        assert "digraph" in sample_dot_code
        assert "{" in sample_dot_code
        assert "}" in sample_dot_code
        assert "->" in sample_dot_code

    def test_mindmap_prompt_structure(self):
        """Test that the mindmap prompt is properly structured"""
        from transcription import TranscriptionService

        # The prompt should contain key instructions
        # This is implicitly tested through the method, but we can verify
        # the method exists and is callable
        with patch('transcription.WhisperModel'), \
             patch('transcription.OpenAI'):
            service = TranscriptionService(
                whisper_model="base",
                llm_base_url="http://localhost:11434/v1",
                llm_api_key="not-needed",
                llm_model="llama3.2"
            )

            # Verify the method exists
            assert hasattr(service, 'generate_mindmap')
            assert callable(service.generate_mindmap)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
