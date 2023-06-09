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

    
    def get_current_status(self, every:str='1w',offset: str= None, save_path=None):
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
                .dt.truncate(every=every, offset=offset)
                )

        df_created = (self.df.groupby("created_at").agg(pl.col('point').sum(),pl.count())).rename({"created_at":"time_index", "point":"open", "count": "open_cnt"}).drop_nulls()
        df_todo = (self.df.groupby("todo_at").agg(pl.col('point').sum(),pl.count())).rename({"todo_at":"time_index", "point":"todo", "count": "todo_cnt"}).drop_nulls()
        df_closed = (self.df.groupby("closed_at").agg(pl.col('point').sum(),pl.count())).rename({"closed_at":"time_index", "point":"closed", "count": "closed_cnt"}).drop_nulls()

        self.df_burnup = (
                df_created.join(df_todo, on='time_index', how='left')
                .join(df_closed, on='time_index', how='left')
              ).fill_null(0).sort("time_index").select(['time_index', 'open', 'todo', 'closed', 'open_cnt', 'todo_cnt', 'closed_cnt'])
        
        self.df_burnup = self.df_burnup.with_columns(pl.col("time_index").cast(pl.Date).alias("time_index"))

        self.df_burnup_cum = self.df_burnup.with_columns(pl.col(['open', 'todo', 'closed', 'open_cnt', 'todo_cnt', 'closed_cnt']).cumsum())

    def visualize(self, plot_type:str='point', start_string:str=None, end_string:str=None):
        
        ## filter
        start_datetime = self.df_burnup['time_index'].min() if start_string is None else datetime.strptime(start_string, "%Y-%m-%d") 
        end_datetime = datetime.today() if end_string is None else datetime.strptime(end_string, "%Y-%m-%d")

        df_burnup = self.df_burnup.filter(
                            (pl.col('time_index') >= start_datetime) &
                            (pl.col('time_index') <= end_datetime)
                            )
        
        ## data process
        x = df_burnup['time_index']
        
        if plot_type == 'point':
            y_1, y_1_mean = df_burnup['open'], df_burnup['open'].mean()
            y_2, y_2_mean = df_burnup['todo'], df_burnup['todo'].mean()
            y_3, y_3_mean = df_burnup['closed'], df_burnup['closed'].mean()

            df_burnup_cum = df_burnup.with_columns(pl.col(["open", "todo", "closed"]).cumsum())
            df_burnup_cum = df_burnup_cum.with_columns(todo = pl.col('todo') + pl.col('closed'))
            y1_cum, y2_cum, y3_cum = df_burnup_cum['open'], df_burnup_cum['todo'], df_burnup_cum['closed']

        
        elif plot_type == 'count':
            y_1, y_1_mean = df_burnup['open_cnt'], df_burnup['open_cnt'].mean()
            y_2, y_2_mean = df_burnup['todo_cnt'], df_burnup['todo_cnt'].mean()
            y_3, y_3_mean = df_burnup['closed_cnt'], df_burnup['closed_cnt'].mean()

            df_burnup_cum = df_burnup.with_columns(pl.col(["open_cnt", "todo_cnt", "closed_cnt"]).cumsum())
            df_burnup_cum = df_burnup_cum.with_columns(todo_cnt = pl.col('todo_cnt') + pl.col('closed_cnt'))
            y1_cum, y2_cum, y3_cum = df_burnup_cum['open_cnt'], df_burnup_cum['todo_cnt'], df_burnup_cum['closed_cnt']

        ## first plot
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

        open_cum = go.Scatter(x=x, y=y1_cum, mode='lines', name='open',fill='tonexty')
        todo_cum = go.Scatter(x=x, y=y2_cum, mode='lines', name='todo',fill='tonexty')
        closed_cum = go.Scatter(x=x, y=y3_cum, mode='lines', name='closed',fill='tonexty')

        fig_cum = go.Figure(data=[closed_cum, todo_cum, open_cum]) #NOTE: 小さい順
        fig_cum.update_layout(title='Cumulative flow diagram', xaxis=dict(type='date'), xaxis_title='sprint', yaxis_title='cumulative point')

        fig.show()
        fig_cum.show()
