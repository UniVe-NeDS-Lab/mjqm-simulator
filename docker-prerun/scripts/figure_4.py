from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib
import csv
import re
import glob

fsize = 150
legend_size = 200
label_size = 300
title_size = 195
tuplesize = (100, 80)
marker_size = 100
line_size = 20
tick_size = 180
l_pad = 40
asym_size = 20 

cols = [
    'peru',       # brownish-orange
    'royalblue',  # vivid blue
    'crimson',    # strong red
    'purple',     # purple
    'darkgreen',  # dark green
    '#453f44',    # grayish
#    'pink',       # light pink
#    'gold',       # bright yellow-gold
    'deepskyblue',# cyan-like blue
    'orangered',  # red-orange
    'limegreen',  # bright green
    'slateblue',  # bluish purple
]

styles = ['solid', 'dotted', 'dashed', 'dashdot', (0, (3, 5, 1, 5, 1, 5))]
markers = ['o', 'v', 's',  'X', 'D', 'H', 'P', '<', '>']

files = glob.glob("sre/pesa_exp_N20_Classes5_lam*_L100_Nsamples100000.csv")

def extract_lam(filename):
    return float(re.search(r"lam([0-9.]+)", filename).group(1))

# sort files by lam
files_sorted = sorted(files, key=extract_lam)

rows = []

for f in files_sorted:
    lam = extract_lam(f)
    df = pd.read_csv(f)

    avg = df[["T1", "T2", "T5", "T10", "T15"]].mean()

    row = {"lam": lam, **avg.to_dict()}
    rows.append(row)

result_df = pd.DataFrame(rows).sort_values("lam")

files = glob.glob("sre/pesa_bpar_N20_Classes5_lam*_L100_Nsamples100000.csv")

def extract_lam(filename):
    return float(re.search(r"lam([0-9.]+)", filename).group(1))

# sort files by lam
files_sorted = sorted(files, key=extract_lam)

rows = []

for f in files_sorted:
    lam = extract_lam(f)
    df = pd.read_csv(f)

    avg = df[["T1", "T2", "T5", "T10", "T15"]].mean()

    row = {"lam": lam, **avg.to_dict()}
    rows.append(row)

result_df_bpar = pd.DataFrame(rows).sort_values("lam")

def set_ymargin(ax, bottom=0.0, top=0.3):
    ax.set_ymargin(0)
    ax.autoscale_view()
    lim = ax.get_ylim()
    delta = np.diff(lim)
    bottom = lim[0] - delta*bottom
    top = lim[1] + delta*top
    ax.set_ylim(bottom=bottom,top=top)

plt.figure(dpi=1200)
plt.rc('font',**{'family':'serif','serif':['Palatino']})
plt.rc('text',usetex=False)
matplotlib.rcParams['font.size'] = fsize
matplotlib.rcParams['xtick.major.pad'] = 8
matplotlib.rcParams['ytick.major.pad'] = 8
fix, ax = plt.subplots(figsize=tuplesize)
i = 4
j = 0

nClass = 5
N = 20
sn = 'tools_five'
dists = ['Exponential', 'Bounded pareto']
win = 1

for dist in dists:
    if dist == 'Exponential':
        sim_name = sn + '_exp'
    else:
        sim_name = sn + '_bpar'
    lambdas = []
    rtt = []
    rt1 = []
    rt2 = []
    rt5 = []
    rt10 = []
    rt15 = []
    with open('../results/'+sim_name+'/overLambdas-nClasses'+str(nClass)+'-N'+str(N)+'-Win'+str(win)+'-'+dist+'-'+sim_name+'.csv', mode ='r')as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            lambdas.append(float(row['arrival.rate']))
            rtt.append(float(row['RespTime Total']))
            rt1.append(float(row['T1 Waiting']))
            rt2.append(float(row['T2 Waiting']))
            rt5.append(float(row['T5 Waiting']))
            rt10.append(float(row['T10 Waiting']))
            rt15.append(float(row['T15 Waiting']))

    # Zip, sort by first list, then unzip
    a_sorted, b_sorted, c_sorted, d_sorted, e_sorted, f_sorted, g_sorted = zip(*sorted(zip(lambdas, rtt, rt1,rt2,rt5,rt10,rt15)))
    
    a_sorted = list(a_sorted)
    b_sorted = list(b_sorted)
    c_sorted = list(c_sorted)
    d_sorted = list(d_sorted)
    e_sorted = list(e_sorted)
    f_sorted = list(f_sorted)
    g_sorted = list(g_sorted)
            
    tipe = dist
    ax.plot(a_sorted, c_sorted, label='[Class-1] DES', color = cols[i], ls = styles[j], lw = line_size)
    if (dist=='Exponential'):
        ax.plot(result_df["lam"], result_df["T1"], label='[Class-1] SRE', color = cols[i], ls = '', lw = line_size, markersize = 100, marker = '*')
    else:
        ax.plot(result_df_bpar["lam"], result_df_bpar["T1"], label='[Class-1] SRE', color = cols[i], ls = '', lw = line_size, markersize = 100, marker = '*')
    ax.plot(a_sorted, g_sorted, label='[Class-15] DES', color = cols[i], ls = styles[j+2], lw = line_size)
    if (dist=='Exponential'):
        ax.plot(result_df["lam"], result_df["T15"], label='[Class-15] SRE', color = cols[i], ls = '', lw = line_size, markersize = 75, marker = 'X')
    else:
        ax.plot(result_df_bpar["lam"], result_df_bpar["T15"], label='[Class-15] SRE', color = cols[i], ls = '', lw = line_size, markersize = 75, marker = 'X')
    i+=3


ax.set_xlabel("Arrival Rate", fontsize=label_size)
ax.set_ylabel("Average Waiting Time", fontsize=label_size)
#ax.xaxis.set_ticks(np.arange(0.25,0.56,0.05))
#plt.xscale('log')
plt.yscale("log")
plot_filename = "Average Waiting Time vs. Arrival Rate"
ax.set_title(plot_filename, fontsize=label_size)
#ax.xaxis.set_ticks([c[-4] for c in measurements[(i*runs):(i*runs)+runs]])
ax.tick_params(axis='both', which='major', labelsize=tick_size, pad = l_pad)
ax.tick_params(axis='both', which='minor', labelsize=tick_size, pad = l_pad)
#ax.legend(bbox_to_anchor=(1,0.00), loc='lower right', fontsize = 162,ncol=2)
handles, labels = ax.get_legend_handles_labels()

# first 4 → lower right
legend1 = ax.legend(
    handles[:4], labels[:4],
    loc='lower right',
    bbox_to_anchor=(1, 0.00),
    fontsize=230
)

# last 4 → upper left
legend2 = ax.legend(
    handles[4:], labels[4:],
    loc='upper left',
    bbox_to_anchor=(0, 1),
    fontsize=230
)

# keep both legends
ax.add_artist(legend1)
ax.set_xlim(left=0.1, right=2.1)
ax.set_ylim(top=1000)
plt.grid()
#plt.margins(y=0.4)
#set_ymargin(ax, bottom=0, top=100)
plt.savefig('figure_4a.pdf')

plt.figure(dpi=1200)
plt.rc('font',**{'family':'serif','serif':['Palatino']})
plt.rc('text', usetex=False)
matplotlib.rcParams['font.size'] = fsize
matplotlib.rcParams['xtick.major.pad'] = 8
matplotlib.rcParams['ytick.major.pad'] = 8
fix, ax = plt.subplots(figsize=tuplesize)
i = 4
j = 0

win = 1
nClass = 2
N = 1024
sim_name = 'tools_oneOrT'
maxx = 4.96
dist = 'Exponential'

lambdas = []
rtt = []
rts = []
with open('../results/'+sim_name+'/overLambdas-nClasses'+str(nClass)+'-N'+str(N)+'-Win'+str(win)+'-'+dist+'-'+sim_name+'.csv', mode ='r')as file:
    reader = csv.DictReader(file, delimiter=';')
    for row in reader:
        lambdas.append(float(row['arrival.rate']))
        rts.append(float(row['WaitTime Total']))

# Zip, sort by first list, then unzip
a_sorted, b_sorted = zip(*sorted(zip(lambdas, rts)))

a_sorted = list(a_sorted)
b_sorted = list(b_sorted)
        
ax.plot(a_sorted, b_sorted, label='MJQM-Simulator', color = cols[i], ls = styles[j], lw = line_size)

lambdas = []
rtt = []
rts = []
with open('mg/MGEXP-N1024_T512_ps0.9_mus1_mub0.1.csv', mode ='r')as file:
    reader = csv.DictReader(file, delimiter=',')
    for row in reader:
        lambdas.append(float(row['Arrival rate']))
        rts.append(float(row['Wt']))

ax.plot(lambdas, rts, label='Matrix Geometric', color = cols[i], ls = '', lw = line_size, markersize = 100, marker = 'v')
    
i+=1

ax.set_xlabel("Arrival Rate", fontsize=label_size)
ax.set_ylabel("Average Overall Waiting Time", fontsize=label_size)
#ax.xaxis.set_ticks(np.arange(0.25,0.56,0.05))
#plt.xscale('log')
plt.yscale("log")
plot_filename = "Average Overall Waiting Time vs. Arrival Rate"
ax.set_title(plot_filename, fontsize=250)
#ax.xaxis.set_ticks([c[-4] for c in measurements[(i*runs):(i*runs)+runs]])
ax.tick_params(axis='both', which='major', labelsize=tick_size, pad = l_pad)
ax.tick_params(axis='both', which='minor', labelsize=tick_size, pad = l_pad)
ax.legend(bbox_to_anchor=(0,1.00), loc='upper left', fontsize = label_size,ncol=1)
#ax.set_xlim(left=0.1,right=1.6)
#ax.set_ylim(bottom=5, top=1000_000)
plt.grid()
#plt.margins(y=0.4)
#set_ymargin(ax, bottom=0, top=100)
plt.savefig('figure_4b.pdf')