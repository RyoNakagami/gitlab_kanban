
#%%
from gitlab_kanban import Kanban
import json

with open('./SECRET_TOKEN/secret.json', 'r') as f:
        data = json.load(f)


kanban = Kanban(data['gitlab_url'], 
                data['gitlab_projectname'], 
                data['access_token'])


kanban.get_current_status()
kanban.df

#%%
kanban.visualize()


#%%
Kanban(data['gitlab_url'], 
                data['gitlab_projectname'], 
                'hoge')