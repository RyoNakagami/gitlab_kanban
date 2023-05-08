from gitlab_kanban import __version__
from gitlab_kanban import Kanban
import json
import pytest

def test_version():
    assert __version__ == '0.1.0'

@pytest.fixture()
def kanban():
    with open('./SECRET_TOKEN/secret.json', 'r') as f:
        secret = json.load(f)
    return Kanban(secret['gitlab_url'], 
                  secret['gitlab_projectname'], 
                  secret['access_token'])

    
def test_valid_instance(kanban):
    kanban.df
