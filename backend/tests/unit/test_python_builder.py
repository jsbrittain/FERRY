import hashlib
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.builders.python import PythonBuilder


class TestPythonBuilder:
    def setup_method(self):
        self.builder = PythonBuilder()

    def test_identifier(self):
        assert self.builder.identifier() == "python"

    def test_default_dependency_filename(self):
        assert self.builder.default_dependency_filename() == "requirements.txt"

    def test_get_template_dockerfile(self):
        path = PythonBuilder.get_template_dockerfile()
        assert path.name == "Dockerfile"
        assert path.exists()

    def test_dependency_hash_with_requirements(self):
        with tempfile.TemporaryDirectory() as tmp:
            req_path = Path(tmp) / "requirements.txt"
            req_path.write_text("numpy>=1.24\npandas>=2.0\n")
            expected = hashlib.sha256(req_path.read_bytes()).hexdigest()
            result = self.builder.dependency_hash(Path(tmp))
            assert result == expected
            assert len(result) == 64

    def test_dependency_hash_missing_requirements(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.builder.dependency_hash(Path(tmp))
            assert result == hashlib.sha256(b"").hexdigest()

    def test_dependency_hash_empty_requirements_is_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "requirements.txt").write_text("")
            result = self.builder.dependency_hash(Path(tmp))
            assert result == hashlib.sha256(b"").hexdigest()

    @patch("app.builders.python.docker.from_env")
    @patch("app.builders.python.shutil.copy2")
    def test_build_copies_template_and_requirements(
        self, mock_copy2, mock_docker_from_env
    ):
        mock_client = MagicMock()
        mock_image = MagicMock()
        mock_image.tags = ["ferry/builds/test:abc"]
        mock_client.images.build.return_value = (mock_image, [])
        mock_client.images.get.return_value = None
        mock_docker_from_env.return_value = mock_client

        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = Path(tmp)
            (bundle_path / "requirements.txt").write_text("numpy")
            dockerfile = PythonBuilder.get_template_dockerfile()

            result = self.builder.build(
                bundle_path=bundle_path,
                dockerfile=dockerfile,
                base_image="ferry/python-3.13:latest",
                image_tag="ferry/builds/test:abc",
            )

        assert result.image_reference == "ferry/builds/test:abc"
        assert result.duration_seconds >= 0
        mock_client.images.build.assert_called_once()

    @patch("app.builders.python.docker.from_env")
    def test_build_handles_docker_exception(self, mock_docker_from_env):
        mock_client = MagicMock()
        from docker.errors import DockerException

        mock_client.images.build.side_effect = DockerException("build failed")
        mock_client.images.get.return_value = None
        mock_docker_from_env.return_value = mock_client

        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = Path(tmp)
            (bundle_path / "requirements.txt").write_text("numpy")
            dockerfile = PythonBuilder.get_template_dockerfile()

            result = self.builder.build(
                bundle_path=bundle_path,
                dockerfile=dockerfile,
                base_image="ferry/python-3.13:latest",
                image_tag="ferry/builds/test:abc",
            )

        assert result.success is False
        assert "build failed" in result.build_log

    def test_build_fails_without_requirements(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = Path(tmp)
            dockerfile = PythonBuilder.get_template_dockerfile()
            result = self.builder.build(
                bundle_path=bundle_path,
                dockerfile=dockerfile,
                base_image="ferry/python-3.13:latest",
                image_tag="ferry/builds/test:abc",
            )
        assert result.success is False
        assert "requirements.txt" in result.build_log

    def test_build_raises_when_dockerfile_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = Path(tmp)
            (bundle_path / "requirements.txt").write_text("numpy")
            missing_dockerfile = Path(tmp) / "nonexistent.Dockerfile"
            with pytest.raises(RuntimeError, match="Dockerfile not found"):
                self.builder.build(
                    bundle_path=bundle_path,
                    dockerfile=missing_dockerfile,
                    base_image="ferry/python-3.13:latest",
                    image_tag="ferry/builds/test:abc",
                )

    @patch("app.builders.python.docker.from_env")
    @patch("app.builders.python.shutil.copy2")
    def test_build_cleans_up_context_on_success(self, mock_copy2, mock_docker_from_env):
        mock_client = MagicMock()
        mock_image = MagicMock()
        mock_image.tags = ["test:tag"]
        mock_client.images.build.return_value = (mock_image, [])
        mock_client.images.get.return_value = None
        mock_docker_from_env.return_value = mock_client

        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = Path(tmp)
            (bundle_path / "requirements.txt").write_text("numpy")
            dockerfile = PythonBuilder.get_template_dockerfile()
            self.builder.build(
                bundle_path=bundle_path,
                dockerfile=dockerfile,
                base_image="ferry/python-3.13:latest",
                image_tag="test:tag",
            )

    @patch("app.builders.python.docker.from_env")
    @patch("app.builders.python.shutil.copy2")
    def test_build_with_custom_dockerfile(self, mock_copy2, mock_docker_from_env):
        mock_client = MagicMock()
        mock_image = MagicMock()
        mock_image.tags = ["ferry/builds/test:custom"]
        mock_client.images.build.return_value = (mock_image, [])
        mock_client.images.get.return_value = None
        mock_docker_from_env.return_value = mock_client

        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = Path(tmp)
            (bundle_path / "requirements.txt").write_text("numpy")
            custom_df = bundle_path / "my.Dockerfile"
            custom_df.write_text("FROM custom-base\nRUN echo hello")

            result = self.builder.build(
                bundle_path=bundle_path,
                dockerfile=custom_df,
                base_image="ferry/python-3.13:latest",
                image_tag="ferry/builds/test:custom",
            )

        assert result.image_reference == "ferry/builds/test:custom"
        assert result.success
        mock_client.images.build.assert_called_once()
