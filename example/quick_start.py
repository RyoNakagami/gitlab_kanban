
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


kanban.get_current_status(every='1w',offset='1d')

#kanban.visualize()
#kanban.visualize(plot_type='count')
#%%
kanban.visualize(start_string='2023-04-01')

#%%
kanban.df_burnup.filter(
   (pl.col('time_index') >= datetime.strptime('2020-04-01',  "%Y-%m-%d")) &
   (pl.col('time_index') <= datetime.strptime('2023-05-09',  "%Y-%m-%d"))
)


#%%
kanban.df_burnup_cum.filter(
        (pl.col('time_index') >= datetime.strptime('2020-04-01',  "%Y-%m-%d")) &
        (pl.col('time_index') <= datetime.strptime('2023-05-09',  "%Y-%m-%d"))
        )
