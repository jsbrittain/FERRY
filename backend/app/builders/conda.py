import hashlib
import logging
import shutil
import tempfile
import time
from pathlib import Path

import docker
import requests
from docker.errors import DockerException, ImageNotFound

from app.builders.base import BuildResult, EnvironmentBuilder

logger = logging.getLogger("builders.conda")

TEMPLATE_DIR = (
    Path(__file__).resolve().parent.parent.parent / "builder_templates" / "conda"
)
DOCKERFILE_NAME = "Dockerfile"
DEPENDENCY_FILES = ["environment.yml", "environment.yaml"]
TEMPLATE_DEPENDENCY_NAME = "environment.yml"


class CondaBuilder(EnvironmentBuilder):
    def identifier(self) -> str:
        return "conda"

    def dependency_hash(self, bundle_path: Path) -> str:
        for name in DEPENDENCY_FILES:
            dep_file = bundle_path / name
            if dep_file.exists() and dep_file.is_file():
                return hashlib.sha256(dep_file.read_bytes()).hexdigest()
        return hashlib.sha256(b"").hexdigest()

    def default_dependency_filename(self) -> str:
        return DEPENDENCY_FILES[0]

    @classmethod
    def get_template_dockerfile(cls) -> Path:
        return TEMPLATE_DIR / DOCKERFILE_NAME

    def build(
        self,
        *,
        bundle_path: Path,
        dockerfile: Path,
        base_image: str,
        image_tag: str,
        timeout: int = 3600,
    ) -> BuildResult:
        if not dockerfile.exists():
            raise RuntimeError(f"Dockerfile not found: {dockerfile}")

        dep_path: Path | None = None
        for name in DEPENDENCY_FILES:
            candidate = bundle_path / name
            if candidate.exists() and candidate.is_file():
                dep_path = candidate
                break
        if dep_path is None:
            names = " or ".join(DEPENDENCY_FILES)
            return BuildResult(
                success=False,
                build_log=(
                    f"The selected Conda runtime requires the Analysis Bundle to "
                    f"include a {names} file. "
                    f"An empty file is valid if no additional packages are required."
                ),
            )

        context_dir = Path(tempfile.mkdtemp(prefix="ferry-build-"))
        try:
            shutil.copy2(str(dockerfile), str(context_dir / DOCKERFILE_NAME))
            shutil.copy2(str(dep_path), str(context_dir / TEMPLATE_DEPENDENCY_NAME))

            client = docker.from_env()
            try:
                client.images.get(base_image)
            except ImageNotFound:
                logger.info("Pulling base image: %s", base_image)
                client.images.pull(base_image)

            start = time.time()
            build_log_lines: list[str] = []
            try:
                image, log_gen = client.images.build(
                    path=str(context_dir),
                    tag=image_tag,
                    buildargs={"BASE_IMAGE": base_image},
                    rm=True,
                    forcerm=True,
                    timeout=timeout,
                )
                for chunk in log_gen:
                    if isinstance(chunk, dict):
                        msg = chunk.get("stream", "")
                        if msg:
                            build_log_lines.append(msg.strip())
            except DockerException as e:
                duration = time.time() - start
                build_log = (
                    "\n".join(build_log_lines + [f"ERROR: {e}"])
                    if build_log_lines
                    else str(e)
                )
                return BuildResult(
                    success=False,
                    build_log=build_log,
                    duration_seconds=duration,
                )
            except requests.exceptions.Timeout:
                duration = time.time() - start
                return BuildResult(
                    success=False,
                    build_log=f"Build timed out after {timeout} seconds",
                    duration_seconds=duration,
                )

            duration = time.time() - start
            ref = image.tags[0] if image.tags else image_tag
            return BuildResult(
                image_reference=ref,
                build_log="\n".join(build_log_lines),
                duration_seconds=duration,
            )
        finally:
            shutil.rmtree(context_dir, ignore_errors=True)
