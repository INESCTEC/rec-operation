##############################################
##            Results Functions             ##
##############################################

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import json
# from plotly.subplots import make_subplots
# import plotly.graph_objects as go

from .auxiliary_functions import create_empty_nested_dict

##############################################
##              Plot Results                ##
##############################################
def plot_results(opt_output, plotOption='w', writePath = './output/results.png'):

    # unpack some variables
    opt_diagrams = opt_output['opt_diagrams']
    tempSet = opt_output['tempSet']
    original_load = opt_diagrams['original_load']
    optimized_load = opt_diagrams['optimized_load']
    original_load_kwh = opt_output['original_load']
    optimized_load_kwh = opt_output['optimized_load']

    opt_diagrams['old_index'] = opt_diagrams.index
    opt_diagrams = opt_diagrams.set_index('timestamp')

    # parameters
    fig, (ax1, ax3, ax4) = plt.subplots(3, sharex=True, figsize=(15, 8))
    fig.tight_layout(rect=[0.01, 0.1, 1, 0.85])
    fig.suptitle('Original Load = ' + "{:.2f}".format(original_load_kwh) + ' kWh' + ' | Optimized Load = ' + "{:.2f}".format(optimized_load_kwh) + ' kWh', fontsize=12)
    ax1.axhline(y = tempSet, color = 'lightgreen', linestyle = 'dashed')
    ax1.set_ylabel('Temp. (°C)', labelpad=8)
    ax3.set_ylabel('Load (W)', labelpad=8)
    ax4.set_ylabel('Load (W)', labelpad=8)
    ax1.title.set_text('EWH Water Temperature & Usage')
    ax3.title.set_text('EWH Optimized Energy Consumption')
    ax4.title.set_text('EWH Original Energy Consumption')
    ax1.title.set_size(8)
    ax3.title.set_size(8)
    ax4.title.set_size(8)
    ax2 = ax1.twinx()
    ax2.set_yticks([])
    ax3.tick_params(labelrotation=90)
    ax4.tick_params(labelrotation=90)

    #plots
    ax3.axvspan(opt_diagrams.index[0], opt_diagrams.index[len(opt_diagrams)-1], color="green", alpha=0.1)
    ax1.plot(opt_diagrams.index, opt_diagrams.temp, color='royalblue')
    ax3.plot(opt_diagrams.index, optimized_load, color='darkorange')
    ax4.plot(opt_diagrams.index, original_load, color='goldenrod')
    block_red = 0
    block_blue = 0
    for i in opt_diagrams.index:
        # auxiliary index
        j = opt_diagrams.loc[i,'old_index']
        if (opt_diagrams.loc[i,'delta_use'] == 1) & (block_red==0):
            block_red = 1
            start_red = opt_diagrams.index[j]
        if (opt_diagrams.loc[i, 'delta_use'] == 0) & (block_red == 1):
            end_red = opt_diagrams.index[j-1]
            block_red = 0
            ax2.axvspan(start_red,end_red, color="red", alpha=0.3)
            ax3.axvspan(start_red, end_red, color="red", alpha=0.3)
            ax4.axvspan(start_red, end_red, color="red", alpha=0.3)
        if (opt_diagrams.loc[i,'delta_in'] == 1) & (block_blue==0):
            block_blue = 1
            start_blue = opt_diagrams.index[j]
        if (opt_diagrams.loc[i, 'delta_in'] == 0) & (block_blue == 1):
            end_blue = opt_diagrams.index[j-1]
            block_blue = 0
            ax2.axvspan(start_blue,end_blue, color="blue", alpha=0.1)
            ax3.axvspan(start_blue, end_blue, color="blue", alpha=0.1)

    legend_elements = [Line2D([0], [0], color='royalblue', lw=2, label='EWH Water Temperature'),
                       Line2D([0], [0], color='lightgreen', lw=2, label='User-Defined Hot Water Confort Temperature',linestyle='dashed'),
                       Line2D([0], [0], color='darkorange', lw=2, label='EWH Optimized Energy Consumption'),
                       Line2D([0], [0], color='goldenrod', lw=2, label='EWH Original Energy Consumption'),
                       Patch(facecolor='palegreen', label='Flexibility Available'),
                       Patch(facecolor='salmon', label='Detected Hot Water Usage'),
                       Patch(facecolor='lightskyblue', label='Optimized EWH ON Status')]
    fig.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.9,0.99), fontsize="8")


    if plotOption == 'w': plt.savefig(writePath)
    if plotOption == 'p': plt.show()

# def plot_results_plotly(opt_output, plotOption='w', writePath='./output/results.png'):
#
#             opt_diagrams = opt_output['opt_diagrams']
#             opt_diagrams['tempSet'] = opt_output['tempSet']
#             tempSet = opt_diagrams['tempSet']
#             original_load = opt_diagrams['original_load']
#             optimized_load = opt_diagrams['optimized_load']
#             original_load_kwh = opt_output['original_load']
#             optimized_load_kwh = opt_output['optimized_load']
#             opt_diagrams['old_index'] = opt_diagrams.index
#             opt_diagrams = opt_diagrams.set_index('timestamp')
#
#             fig = make_subplots(rows=3, cols=1,
#                                 subplot_titles=("EWH Water Temperature & Usage", "EWH Optimized Energy Consumption",
#                                                 "EWH Original Energy Consumption"),
#                                 shared_xaxes=True,
#                                 vertical_spacing=0.15)
#
#             fig.update_annotations(font_size=10)
#             fig.update_layout(template="plotly_dark")
#             fig.update_yaxes(title_text='Temp. (°C)', row=1, col=1, title_font=dict(size=10))
#             fig.update_yaxes(title_text='Load (W)', row=2, col=1, title_font=dict(size=10))
#             fig.update_yaxes(title_text='Load (W)', row=3, col=1, title_font=dict(size=10))
#
#             fig.add_trace(go.Scatter(name='User-Defined Hot Water Confort Temperature', x=opt_diagrams.index, y=tempSet,
#                                      mode='lines', line_width=3, line_dash="dash", line_color="limegreen",
#                                      opacity=0.75), row=1, col=1)
#             fig.add_trace(
#                 go.Scatter(name='EWH Water Temperature', x=opt_diagrams.index, y=opt_diagrams.temp, mode='lines',
#                            line_color='royalblue'), row=1, col=1)
#             fig.add_trace(go.Scatter(name='EWH Optimized Energy Consumption', x=opt_diagrams.index, y=optimized_load,
#                                      mode='lines', line_color='darkorange'), row=2, col=1)
#             fig.add_trace(
#                 go.Scatter(name='EWH Original Energy Consumption', x=opt_diagrams.index, y=original_load, mode='lines',
#                            line_color='goldenrod'), row=3, col=1)
#
#             fig.add_trace(go.Bar(name='Detected Hot Water Usage', x=opt_diagrams.index, y=tempSet, marker_color='red',
#                                  opacity=0.6), row=3, col=1)
#             fig.add_trace(
#                 go.Bar(name='Optmized EWH ON Status', x=opt_diagrams.index, y=tempSet, marker_color='lightskyblue',
#                        opacity=0.5), row=3, col=1)
#             fig.add_trace(
#                 go.Bar(name='Flexibility Available', x=opt_diagrams.index, y=tempSet, marker_color='palegreen',
#                        opacity=0.5), row=3, col=1)
#
#             fig.update_layout(title_text='Original Load = ' + "{:.2f}".format(
#                 original_load_kwh) + ' kWh' + ' | Optimized Load = ' + "{:.2f}".format(optimized_load_kwh) + ' kWh',
#                 legend = dict(font = dict(size = 10)))
#             fig.update_xaxes(showgrid=True)
#             fig.update_yaxes(showgrid=True)
#
#             block_red = 0
#             block_blue = 0
#             block_green = 0
#             for i in opt_diagrams.index:
#                 # auxiliary index
#                 j = opt_diagrams.loc[i, 'old_index']
#                 if (opt_diagrams.loc[i, 'delta_in'] == 1) & (block_blue == 0):
#                     block_blue = 1
#                     start_blue = opt_diagrams.index[j]
#                 if (opt_diagrams.loc[i, 'delta_in'] == 0) & (block_blue == 1):
#                     end_blue = opt_diagrams.index[j]
#                     block_blue = 0
#                     fig.add_vrect(x0=start_blue, x1=end_blue,
#                                   fillcolor='lightskyblue', opacity=0.3,
#                                   layer="below", line_width=1, line_color='lightskyblue',
#                                   row=1, col=1)
#                     fig.add_vrect(x0=start_blue, x1=end_blue,
#                                   fillcolor='lightskyblue', opacity=0.3,
#                                   layer="below", line_width=1, line_color='lightskyblue',
#                                   row=2, col=1)
#                 if (opt_diagrams.loc[i, 'delta_use'] == 1) & (block_red == 0):
#                     block_red = 1
#                     start_red = opt_diagrams.index[j]
#                 if (opt_diagrams.loc[i, 'delta_use'] == 0) & (block_red == 1):
#                     end_red = opt_diagrams.index[j]
#                     block_red = 0
#                     fig.add_vrect(x0=start_red, x1=end_red,
#                                   fillcolor='red', opacity=0.6,
#                                   layer="below", line_width=1, line_color='red')
#                 if (opt_diagrams.loc[i, 'delta_in'] == 0) & (block_green == 0):
#                     block_green = 1
#                     start_green = opt_diagrams.index[j]
#                 if ((opt_diagrams.loc[i, 'delta_in'] == 1) & (block_green == 1)):
#                     end_green = opt_diagrams.index[j - 1]
#                     block_green = 0
#                     fig.add_vrect(x0=start_green, x1=end_green,
#                                   fillcolor='palegreen', opacity=0.2,
#                                   layer="below", line_width=1, line_color='palegreen',
#                                   row=2, col=1)
#                 if ((i == opt_diagrams.index[-1]) & (opt_diagrams.loc[i, 'delta_in'] == 0)):
#                     end_green = opt_diagrams.index[j]
#                     block_green = 0
#                     fig.add_vrect(x0=start_green, x1=end_green,
#                                   fillcolor='palegreen', opacity=0.2,
#                                   layer="below", line_width=1, line_color='palegreen',
#                                   row=2, col=1)
#
#             if plotOption == 'w': fig.write_image(writePath, width=1920, height=1080)
#             return fig



##############################################
##             Export Results               ##
##############################################
def write_results(opt_output, writePath="./output/results.json"):

    # organize data to be exported
    opt_diagrams = opt_output['opt_diagrams']
    user = opt_output['user']
    simulation_period_start = opt_diagrams['timestamp'].astype(str)[0]
    simulation_period_end = opt_diagrams['timestamp'].astype(str)[opt_diagrams.index[-1]]
    days_in_simulation = opt_output['simulated_period']
    original_energy = round(opt_output['original_load'],4)
    optimized_energy = round(opt_output['optimized_load'],4)
    avg_daily_energy = round(opt_output['avg_daily_consumption'],4)
    total_flexibility = opt_output['total_flexibility']
    perc_flexibility = round(opt_output['perc_flexibility'],2)
    avg_daily_flexibility = round(opt_output['avg_daily_flexibility'],0)
    original_price = round(opt_output['original_price'],2)
    optimized_price = round(opt_output['optimized_price'],2)
    savings_cost = round(opt_output['savings_cost'],2)
    savings_energy = round(opt_output['savings_energy'],4)
    original_usage_profile = opt_diagrams[['timestamp','delta_use']].copy()
    original_usage_profile['timestamp'] = original_usage_profile['timestamp'].astype(str)
    original_usage_profile = original_usage_profile.rename(columns={"delta_use": "hot_water_usage"})
    original_usage_profile = original_usage_profile.to_dict('records')
    optimized_calendar = opt_diagrams[['timestamp','delta_in']].copy()
    optimized_calendar['timestamp'] = optimized_calendar['timestamp'].astype(str)
    optimized_calendar = optimized_calendar.rename(columns={"delta_in": "ewh_on"})
    optimized_calendar = optimized_calendar.to_dict('records')


    # list of variables to fill in results dictionary
    list_of_keys = ['user', 'simulation_period', 'original_energy', 'optimized_energy', 'original_price',
                    'optimized_price', 'avg_daily_energy', 'total_flexibility', 'perc_flexibility',
                    'avg_daily_flexibility', 'savings_cost', 'savings_energy', 'original_usage_profile',
                    'optimized_calendar']

    # create empty nested dictionary
    results = create_empty_nested_dict(list_of_keys)
    # fill dictionary
    results['user'] = user
    results['simulation_period']['start'] = simulation_period_start
    results['simulation_period']['end'] = simulation_period_end
    results['simulation_period']['days_in_simulation'] = days_in_simulation
    results['original_energy']['value'] = original_energy
    results['original_energy']['unit'] = 'kWh'
    results['optimized_energy']['value'] = optimized_energy
    results['optimized_energy']['unit'] = 'kWh'
    results['original_price']['value'] = original_price
    results['original_price']['unit'] = 'Euro'
    results['optimized_price']['value'] = optimized_price
    results['optimized_price']['unit'] = 'Euro'
    results['avg_daily_energy']['value'] = avg_daily_energy
    results['avg_daily_energy']['unit'] = 'kWh'
    results['total_flexibility']['value'] = total_flexibility
    results['total_flexibility']['unit'] = 'minutes'
    results['perc_flexibility']['value'] = perc_flexibility
    results['perc_flexibility']['unit'] = 'Percent'
    results['avg_daily_flexibility']['value'] = avg_daily_flexibility
    results['avg_daily_flexibility']['unit'] = 'kWh'
    results['savings_cost']['value'] = savings_cost
    results['savings_cost']['unit'] = 'Euro'
    results['savings_energy']['value'] = savings_energy
    results['savings_energy']['unit'] = 'kWh'
    results['original_usage_profile'] = original_usage_profile
    results['optimized_calendar'] = optimized_calendar

    with open(writePath, "w") as outfile:
        json.dump(results, outfile)

def return_results(opt_output):

    # organize data to be exported
    opt_diagrams = opt_output['opt_diagrams']
    user = opt_output['user']
    simulation_period_start = opt_diagrams['timestamp'].astype(str)[0]
    simulation_period_end = opt_diagrams['timestamp'].astype(str)[opt_diagrams.index[-1]]
    days_in_simulation = opt_output['simulated_period']
    original_energy = round(opt_output['original_load'],4)
    optimized_energy = round(opt_output['optimized_load'],4)
    avg_daily_energy = round(opt_output['avg_daily_consumption'],4)
    total_flexibility = opt_output['total_flexibility']
    perc_flexibility = round(opt_output['perc_flexibility'],2)
    avg_daily_flexibility = round(opt_output['avg_daily_flexibility'],0)
    original_price = round(opt_output['original_price'],2)
    optimized_price = round(opt_output['optimized_price'],2)
    savings_cost = round(opt_output['savings_cost'],2)
    savings_energy = round(opt_output['savings_energy'],4)
    original_usage_profile = opt_diagrams[['timestamp','delta_use']].copy()
    original_usage_profile['timestamp'] = original_usage_profile['timestamp'].astype(str)
    original_usage_profile = original_usage_profile.rename(columns={"delta_use": "hot_water_usage"})
    original_usage_profile = original_usage_profile.to_dict('records')
    optimized_calendar = opt_diagrams[['timestamp','delta_in']].copy()
    optimized_calendar['timestamp'] = optimized_calendar['timestamp'].astype(str)
    optimized_calendar = optimized_calendar.rename(columns={"delta_in": "ewh_on"})
    optimized_calendar = optimized_calendar.to_dict('records')


    # list of variables to fill in results dictionary
    list_of_keys = ['user', 'simulation_period', 'original_energy', 'optimized_energy', 'original_price',
                    'optimized_price', 'avg_daily_energy', 'total_flexibility', 'perc_flexibility',
                    'avg_daily_flexibility', 'savings_cost', 'savings_energy', 'original_usage_profile',
                    'optimized_calendar']

    # create empty nested dictionary
    results = create_empty_nested_dict(list_of_keys)
    # fill dictionary
    results['user'] = user
    results['simulation_period']['start'] = simulation_period_start
    results['simulation_period']['end'] = simulation_period_end
    results['simulation_period']['days_in_simulation'] = days_in_simulation
    results['original_energy']['value'] = original_energy
    results['original_energy']['unit'] = 'kWh'
    results['optimized_energy']['value'] = optimized_energy
    results['optimized_energy']['unit'] = 'kWh'
    results['original_price']['value'] = original_price
    results['original_price']['unit'] = 'Euro'
    results['optimized_price']['value'] = optimized_price
    results['optimized_price']['unit'] = 'Euro'
    results['avg_daily_energy']['value'] = avg_daily_energy
    results['avg_daily_energy']['unit'] = 'kWh'
    results['total_flexibility']['value'] = total_flexibility
    results['total_flexibility']['unit'] = 'minutes'
    results['perc_flexibility']['value'] = perc_flexibility
    results['perc_flexibility']['unit'] = 'Percent'
    results['avg_daily_flexibility']['value'] = avg_daily_flexibility
    results['avg_daily_flexibility']['unit'] = 'kWh'
    results['savings_cost']['value'] = savings_cost
    results['savings_cost']['unit'] = 'Euro'
    results['savings_energy']['value'] = savings_energy
    results['savings_energy']['unit'] = 'kWh'
    results['original_usage_profile'] = original_usage_profile
    results['optimized_calendar'] = optimized_calendar

    return results
