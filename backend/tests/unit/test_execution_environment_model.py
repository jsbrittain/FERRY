from app.models.execution_environment import ExecutionEnvironment


class TestExecutionEnvironmentModel:
    def test_create_environment(self):
        env = ExecutionEnvironment(
            identifier="python-3.13-scientific",
            name="Python 3.13 Scientific",
            runtime="python-3.13",
            description="NumPy, SciPy, Pandas",
            status="active",
            image_reference="ferry/python-3.13-scientific:latest",
        )
        assert env.identifier == "python-3.13-scientific"
        assert env.name == "Python 3.13 Scientific"
        assert env.runtime == "python-3.13"
        assert env.description == "NumPy, SciPy, Pandas"
        assert env.status == "active"
        assert env.image_reference == "ferry/python-3.13-scientific:latest"

    def test_default_status(self):
        env = ExecutionEnvironment(
            identifier="r-4.5-tidyverse",
            name="R 4.5 Tidyverse",
            runtime="r-4.5",
        )
        assert env.status is None  # server_default, not in-memory

    def test_default_image_reference(self):
        env = ExecutionEnvironment(
            identifier="test-env",
            name="Test",
            runtime="python-3.13",
        )
        assert env.image_reference is None  # server_default, not in-memory

    def test_default_definition_path(self):
        env = ExecutionEnvironment(
            identifier="test-env",
            name="Test",
            runtime="python-3.13",
        )
        assert env.definition_path is None  # nullable, no default

    def test_definition_path_set(self):
        env = ExecutionEnvironment(
            identifier="python-3.14",
            name="Python 3.14",
            runtime="python-3.14",
            definition_path="python-3.14",
        )
        assert env.definition_path == "python-3.14"

    def test_default_description(self):
        env = ExecutionEnvironment(
            identifier="test-env",
            name="Test",
            runtime="python-3.13",
        )
        assert env.description is None  # server_default, not in-memory
