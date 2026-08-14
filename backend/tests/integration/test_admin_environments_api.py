import pytest

from app.models.execution_environment import ExecutionEnvironment


@pytest.fixture
def seeded_environments(db_session):
    environments = [
        ExecutionEnvironment(
            identifier="python-3.13-scientific",
            name="Python 3.13 Scientific",
            runtime="python-3.13",
            description="NumPy, SciPy, Pandas",
            status="active",
            image_reference="ferry/python-3.13-scientific:latest",
        ),
        ExecutionEnvironment(
            identifier="r-4.5-tidyverse",
            name="R 4.5 Tidyverse",
            runtime="r-4.5",
            description="tidyverse, dplyr, ggplot2",
            status="active",
            image_reference="ferry/r-4.5-tidyverse:latest",
        ),
    ]
    for e in environments:
        db_session.add(e)
    db_session.commit()
    for e in environments:
        db_session.refresh(e)
    return environments


class TestAdminExecutionEnvironments:
    def test_list_empty(self, client, admin_user):
        response = client.get("/api/admin/execution-environments")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_with_data(self, client, admin_user, seeded_environments):
        response = client.get("/api/admin/execution-environments")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        names = {e["name"] for e in data}
        assert "Python 3.13 Scientific" in names
        assert "R 4.5 Tidyverse" in names

    def test_list_returns_fields(self, client, admin_user, seeded_environments):
        response = client.get("/api/admin/execution-environments")
        assert response.status_code == 200
        env = response.json()[0]
        assert "id" in env
        assert "identifier" in env
        assert "name" in env
        assert "runtime" in env
        assert "description" in env
        assert "status" in env
        assert "image_reference" in env
        assert "created_at" in env
        assert "updated_at" in env

    def test_get_by_id(self, client, admin_user, seeded_environments):
        env_id = seeded_environments[0].id
        response = client.get(f"/api/admin/execution-environments/{env_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["identifier"] == "python-3.13-scientific"
        assert data["name"] == "Python 3.13 Scientific"
        assert data["runtime"] == "python-3.13"

    def test_get_not_found(self, client, admin_user):
        url = "/api/admin/execution-environments/00000000-0000-0000-0000-000000000000"
        response = client.get(url)
        assert response.status_code == 404

    def test_ordered_by_name(self, client, admin_user, seeded_environments):
        response = client.get("/api/admin/execution-environments")
        data = response.json()
        names = [e["name"] for e in data]
        assert names == sorted(names)
