## Kanban Dashboard: What is it?


## Requirements
### Gitlab Access Token

To use the `gitlab_kanban`, it is necessary to obtain an access token, which serves as a form of authentication. 
To create an access token, you can open the "Access Tokens" page from your profile on GitLab. From there, you can specify the token's name, scope, and expiration date, and generate the token. Once you have an access token, you can use it in your API requests to authenticate and access GitLab's resources.




## Repository

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

## Features
### Rollup: `every` and `offset`

- see [polars.Expr.dt.truncate](https://pola-rs.github.io/polars/py-polars/html/reference/expressions/api/polars.Expr.dt.truncate.html)


## Appendix: Tips

> Untrack a folder

To exclude a specific folder from being tracked by git, you can use the following command:

```zsh
% git rm -r --cached <target folder>
```