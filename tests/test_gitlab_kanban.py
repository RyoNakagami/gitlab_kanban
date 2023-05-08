from gitlab_kanban import __version__
from gitlab_kanban import Kanban
import pytest

import json
import polars as pl

def test_version():
    assert __version__ == '0.1.0'

@pytest.fixture()
def kanban():
    with open('./SECRET_TOKEN/secret.json', 'r') as f:
        secret = json.load(f)
    
    return Kanban(secret['gitlab_url'], 
                  secret['gitlab_projectname'], 
                  secret['access_token'])

def test_invalid_token():
    with open('./SECRET_TOKEN/secret.json', 'r') as f:
        secret = json.load(f)
    
    ## GitlabAuthenticationError – If authentication is not correct
    with pytest.raises(Exception) as excinfo:
        Kanban(secret['gitlab_url'], 
               secret['gitlab_projectname'], 
               'hogehoge')  
        
def test_get_df(kanban):
    kanban.get_current_status()
    assert isinstance(kanban.df, pl.DataFrame)
