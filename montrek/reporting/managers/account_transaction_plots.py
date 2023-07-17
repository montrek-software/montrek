import pandas as pd
import plotly.graph_objects as go
from transaction.models import TransactionSatellite
from reporting.core.reporting_data import ReportingData
from reporting.core.reporting_plots import ReportingPlot

def draw_monthly_income_expanses_plot(transactions_data:pd.DataFrame) -> go.Figure:
    transactions_data['value'] = transactions_data['transaction_price'] * transactions_data['transaction_amount']
    transactions_data['income'] = transactions_data['value'].apply(lambda x: x if x > 0 else 0)
    transactions_data['expanse'] = transactions_data['value'].apply(lambda x: x if x < 0 else 0)
    transactions_data['transaction_date'] = transactions_data['transaction_date'].apply(lambda x: x.strftime('%Y-%m'))
    transactions_data = transactions_data.loc[:,['income', 'expanse','transaction_date']].groupby(['transaction_date']).sum()
    rolling_data = transactions_data.rolling(12).mean()
    transactions_data = transactions_data.join(rolling_data, rsuffix='_rolling_1y_mean')
    transactions_data['pnl_1y_mean'] = transactions_data['income_rolling_1y_mean'] + transactions_data['expanse_rolling_1y_mean']
    report_data = ReportingData(
        data_df=transactions_data,
        x_axis_is_index=True,
        y_axis_columns=['income', 'expanse', 'income_rolling_1y_mean', 'expanse_rolling_1y_mean', 'pnl_1y_mean'],
        plot_types=['bar', 'bar', 'line', 'line', 'line'],
    )
    plot = ReportingPlot()
    plot.generate(report_data)
    return plot
