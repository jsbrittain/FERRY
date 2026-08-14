import uuid

from app.models.execution_image import ExecutionImage


class TestExecutionImageModel:
    def test_create_execution_image(self):
        img = ExecutionImage(
            execution_environment_id=uuid.uuid4(),
            dependency_hash="a" * 64,
            image_reference="ferry/builds/python-3.13:abc123",
            builder_type="python",
        )
        assert img.execution_environment_id is not None
        assert img.dependency_hash == "a" * 64
        assert img.image_reference == "ferry/builds/python-3.13:abc123"
        assert img.builder_type == "python"

    def test_default_build_log(self):
        img = ExecutionImage(
            execution_environment_id=uuid.uuid4(),
            dependency_hash="a" * 64,
            image_reference="ferry/builds/python-3.13:abc123",
            builder_type="python",
        )
        assert img.build_log is None  # server_default, not in-memory

    def test_unique_constraint_defined(self):
        assert len(ExecutionImage.__table_args__) == 1
        constraint = ExecutionImage.__table_args__[0]
        assert str(constraint.name) == "uq_execution_image_env_hash"
