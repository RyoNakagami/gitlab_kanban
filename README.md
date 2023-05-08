

## Repository構成

```
.
├── gitlab_kanban
│   ├── __init__.py
│   └── __pycache__
│       └── __init__.cpython-39.pyc
├── poetry.lock
├── pyproject.toml
├── README.md
├── example
│   └── quick_start.py
├── SECRET_TOKEN
│   └── secret.json
└── tests
    ├── __init__.py
    ├── __pycache__
    │   ├── __init__.cpython-39.pyc
    │   └── test_gitlab_kanban.cpython-39-pytest-7.3.1.pyc
    └── test_gitlab_kanban.py
```

### SCERET_TOKEN setup

It is assumed that the SECRET_TOKEN directory contains a file in JSON format that stores information on the repository URL, project name, and access token.

```json
{
    "gitlab_url":"https://gitlab.foofoo.com/",
    "gitlab_projectname":"hogehoge/kanban",
    "access_token":"unkounko"
}
```

The file containing repository URL, project name, and access token information in JSON format exists in the SCERET_TOKEN directory. 
As pytest runs using this file, please configure the file in advance for each test.