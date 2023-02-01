#!/usr/local/bin/python3

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# default size
plt.rc('figure', figsize=(15, 8))

stats = pd.read_csv ('out.tsv', sep='\t', parse_dates=['datetime'], dtype = {'node': 'string' }, low_memory=False)


# set index to timestamp and remove column
stats.index = stats['datetime'].copy()
stats.drop (columns = ['datetime'], inplace=True)


# get restarts
restarts = []
#if pd.unique(stats[stats['restart']>0].index.values):
if stats.columns.isin(['restart']).any():
    restarts = pd.unique (stats[stats['writeLocks']>0].index.values)

print (restarts)

float_columns = [key for key, value in stats.dtypes.items() if value == 'float64']


nodes = pd.unique(stats['node'])

print (nodes)

print (stats)

for column in float_columns:
    print ('working on ' + column + ' with max: ' + str(max))
    max = stats[column].max()
    fig, axes = plt.subplots(nodes.size, 1, sharex=True, sharey=True)
    fig.subplots_adjust(bottom=None, top=None, wspace=0, hspace=0)
    axes[0].set_title(column)
    for node_number in range (nodes.size):
        node = nodes[node_number]
        axes[node_number].tick_params(axis='x', labelrotation = 45)
        axes[node_number].plot (stats[(stats[column] > 0) & (stats['node'] == node)][column], marker='.', linestyle='', label='node ' + node)
        axes[node_number].legend()
        axes[node_number].vlines(restarts, 0, stats[column].max(), color='red')
        axes[node_number].grid()
        #axes[0].set_ylabel('MB')
        fig.savefig (f'{column}.pdf')
        plt.close()



