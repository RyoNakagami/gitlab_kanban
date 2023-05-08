__version__ = '0.1.0'

import dataclasses
import gitlab
import plotly.graph_objects as go
import plotly.subplots as sp
import polars as pl
from datetime import datetime

@dataclasses.dataclass
class Kanban:
    gitlab_url: str
    gitlab_projectname: str
    access_token: str

    def __post_init__(self):
        self.gl = gitlab.Gitlab(self.gitlab_url,
                           self.access_token)
        ## auth check
        self.gl.auth()
        
        ## refreshed the board
        confirmed_issue = self.gl.projects.get(
                                    self.gitlab_projectname
                             ).issues.list(labels=['confirmed'])
        for issue in confirmed_issue:
            issue.labels.remove('confirmed')
            issue.state_event = 'close'
            issue.save()

    
    def get_current_status(self, save_path=None):
        issue_list = self.gl.projects.get(self.gitlab_projectname).issues.list(sort='asc')
        issue_master = []
        todo_label_list = ['work-in-progress', 'review']

        for row in issue_list:
            label_list = row.labels
            if label_list == []:
                continue
            elif any(label in 'trash' for label in label_list):
                continue
            else:
                updated_at = row.updated_at if any(label in todo_label_list for label in label_list) else None

                label_list = list(set(label_list)-set(todo_label_list))
                record = [row.iid, 
                          row.title, 
                          row.created_at, 
                          updated_at,
                          row.closed_at, 
                          label_list,
                          row.weight]
            issue_master.append(record)
        
        df = pl.DataFrame(issue_master, 
                          schema=['iid', 'title', 'created_at', 
                                  'todo_at','closed_at', 'labels', 
                                  'point'])
        
        self.df = (df
                    .with_columns(
                     pl.col(['created_at','todo_at', 'closed_at'])
                     .str.strptime(pl.Datetime(time_zone='Asia/Tokyo'),
                                   "%Y-%m-%dT%H:%M:%S%.fZ",
                                   strict=False),
                                  )
                   ).with_columns(
                     pl.col(["point"]).fill_null(
                         pl.lit(1),
                     ),
                   )
        
        if save_path is not None:
            self.df.write_json("path.json")

        self.df = self.df.with_columns(
                pl.col(['created_at','todo_at', 'closed_at'])
                .dt.truncate(every='1w')
                )

        df_created = (self.df.groupby("created_at").agg(pl.col('point').sum())).rename({"created_at":"time_index", "point":"open"}).drop_nulls()
        df_todo = (self.df.groupby("todo_at").agg(pl.col('point').sum())).rename({"todo_at":"time_index", "point":"todo"}).drop_nulls()
        df_closed = (self.df.groupby("closed_at").agg(pl.col('point').sum())).rename({"closed_at":"time_index", "point":"closed"}).drop_nulls()

        self.df_burndown = (
                df_created.join(df_todo, on='time_index', how='left')
                .join(df_closed, on='time_index', how='left')
              ).fill_null(0).sort("time_index")

        self.df_burndown_cum = self.df_burndown.with_columns(pl.col(["open", "todo", "closed"]).cumsum())

    def visualize(self, start_string:str=None, end_string:str=None):
        
        ## filter
        start_datetime = self.df_burndown['time_index'].min() if start_string is None else datetime.strptime(start_string, "%Y-%m-%d") 
        end_datetime = datetime.today() if end_string is None else datetime.strptime(end_string, "%Y-%m-%d")

        df_burndown = self.df_burndown.filter(
                            (pl.col('time_index') >= start_datetime) &
                            (pl.col('time_index') <= end_datetime)
                            ).with_columns(
                                pl.col("time_index").cast(pl.Date).alias("date_index"))
        
        ## first plot 
        x = df_burndown['date_index']
        y_1, y_1_mean = df_burndown['open'], df_burndown['open'].mean()
        y_2, y_2_mean = df_burndown['todo'], df_burndown['todo'].mean()
        y_3, y_3_mean = df_burndown['closed'], df_burndown['closed'].mean()

        open_mean_line = go.Scatter(x=[x[0], x[-1]], y=[y_1_mean, y_1_mean], 
                       mode='lines',
                       line=dict(dash='dot')
                       )
        open_line = go.Scatter(x=x, y=y_1, mode='lines')

        todo_mean_line = go.Scatter(x=[x[0], x[-1]], y=[y_2_mean, y_2_mean], 
                               mode='lines',
                               line=dict(dash='dot')
                               )
        todo_line = go.Scatter(x=x, y=y_2, mode='lines')

        closed_mean_line = go.Scatter(x=[x[0], x[-1]], y=[y_3_mean, y_3_mean], 
                               mode='lines',
                               line=dict(dash='dot')
                               )
        closed_line = go.Scatter(x=x, y=y_3, mode='lines')


        fig = sp.make_subplots(rows=1, cols=3,
                               shared_yaxes=True, 
                               subplot_titles=('open', 'todo', 'closed'))

        fig.add_trace(open_line, row=1, col=1)
        fig.add_trace(open_mean_line, row=1, col=1)
        fig.add_trace(todo_line, row=1, col=2)
        fig.add_trace(todo_mean_line, row=1, col=2)
        fig.add_trace(closed_line, row=1, col=3)
        fig.add_trace(closed_mean_line, row=1, col=3)

        fig.update_layout(width=1000, height=400, showlegend=False, xaxis=dict(type='date'))

        ## plot second
        df_burndown_cum = df_burndown.with_columns(pl.col(["open", "todo", "closed"]).cumsum())
        df_burndown_cum = df_burndown_cum.with_columns(todo = pl.col('todo') + pl.col('closed'))

        open_cum = go.Scatter(x=df_burndown_cum['time_index'], y=df_burndown_cum['open'], mode='lines', name='open',fill='tonexty')
        todo_cum = go.Scatter(x=df_burndown_cum['time_index'], y=df_burndown_cum['todo'], mode='lines', name='todo',fill='tonexty')
        closed_cum = go.Scatter(x=df_burndown_cum['time_index'], y=df_burndown_cum['closed'], mode='lines', name='closed',fill='tonexty')

        fig_cum = go.Figure(data=[closed_cum, todo_cum, open_cum]) #NOTE: 小さい順
        fig_cum.update_layout(title='Cumulative flow diagram', xaxis=dict(type='date'), xaxis_title='sprint', yaxis_title='cumulative point')

        fig.show()
        fig_cum.show()
