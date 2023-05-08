
#%%
from gitlab_kanban import Kanban
import polars as pl
from datetime import datetime
import json

with open('./SECRET_TOKEN/secret.json', 'r') as f:
        data = json.load(f)


kanban = Kanban(data['gitlab_url'], 
                data['gitlab_projectname'], 
                data['access_token'])


kanban.get_current_status()

kanban.visualize()

#%%
kanban.df_burndown_cum.filter(
                                (pl.col('time_index') >= datetime.strptime('2020-04-01')) &
                                (pl.col('time_index') <= datetime.strptime('2023-05-01'))
                             )


#%%
Kanban(data['gitlab_url'], 
                data['gitlab_projectname'], 
                'hoge')