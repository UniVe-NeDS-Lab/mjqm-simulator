import matplotlib.pyplot as plt
import numpy as np
import matplotlib
import csv

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

def set_ymargin(ax, bottom=0.0, top=0.3):
    ax.set_ymargin(0)
    ax.autoscale_view()
    lim = ax.get_ylim()
    delta = np.diff(lim)
    bottom = lim[0] - delta*bottom
    top = lim[1] + delta*top
    ax.set_ylim(bottom=bottom,top=top)

prerun_input = input('Use pre-run results? (yes/no): ')
prerun = ''
if prerun_input == 'yes' or prerun_input == 'y' or prerun_input == 'Yes' or prerun_input == 'Y':
    prerun = 'prerun/'

plt.figure(dpi=1200)
plt.rc('font',**{'family':'serif','serif':['Palatino']})
plt.rc('text', usetex=False)
matplotlib.rcParams['font.size'] = fsize
matplotlib.rcParams['xtick.major.pad'] = 8
matplotlib.rcParams['ytick.major.pad'] = 8
fix, ax = plt.subplots(figsize=tuplesize)
i = 0
j = 0

wins = [1,10,0,-2]
nClass = 26
N = 2048
sim_name = 'tools_B_pol'
maxx = 4.96
idx = 0

for win in wins:
    maxx = 0
    lambdas = []
    rtt = []
    rts = []
    with open('../results/'+prerun+sim_name+'/overLambdas-nClasses'+str(nClass)+'-N'+str(N)+'-Win'+str(win)+'-Exponential-'+sim_name+'.csv', mode ='r')as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            lambdas.append(float(row['arrival.rate']))
            rts.append(float(row['RespTime Total']))
            if float(row['arrival.rate']) > maxx:
                maxx = float(row['arrival.rate'])
            idx+=1

    # Zip, sort by first list, then unzip
    a_sorted, b_sorted = zip(*sorted(zip(lambdas, rts)))
    
    a_sorted = list(a_sorted)
    b_sorted = list(b_sorted)
            
    tipe = 'FIFO'
    if win == 10:
        tipe = 'SMASH, w = 10'
    elif win == 0:
        tipe = 'MSF'
    elif win == -1:
        tipe = 'ServerFilling'
    ax.plot(a_sorted, b_sorted, label=tipe, color = cols[i], ls = styles[j], lw = line_size, markersize = 50, marker = 'o')
    ax.axvline(x=maxx, color=cols[i], linestyle=styles[j], linewidth=10)
        
    i+=1

ax.set_xlabel("Arrival Rate", fontsize=label_size)
ax.set_ylabel("Average Overall Response Time", fontsize=label_size)
#ax.xaxis.set_ticks(np.arange(0.25,0.56,0.05))
plt.xscale('log')
plt.yscale("log")
plot_filename = "Average Overall Response Time vs. Arrival Rate"
ax.set_title(plot_filename, fontsize=245)
#ax.xaxis.set_ticks([c[-4] for c in measurements[(i*runs):(i*runs)+runs]])
ax.tick_params(axis='both', which='major', labelsize=tick_size, pad = l_pad)
ax.tick_params(axis='both', which='minor', labelsize=tick_size, pad = l_pad)
ax.legend(bbox_to_anchor=(0,1.00), loc='upper left', fontsize = 260,ncol=1)
#ax.set_xlim(left=9, right = 12.5)
ax.set_ylim(bottom=5, top=10_000)
plt.grid()
#plt.margins(y=0.4)
#set_ymargin(ax, bottom=0, top=100)
plt.savefig('figure_2a.pdf')

plt.figure(dpi=1200)
plt.rc('font',**{'family':'serif','serif':['Palatino']})
plt.rc('text', usetex=False)
matplotlib.rcParams['font.size'] = fsize
matplotlib.rcParams['xtick.major.pad'] = 8
matplotlib.rcParams['ytick.major.pad'] = 8
fix, ax = plt.subplots(figsize=(120,80))
i = 0
j = 0

wins = [1,10,0,-2]
last = [27,41,37,58]
nClass = 26
N = 2048
sim_name = 'tools_B_pol'
maxx = 4.96
idx = 0
classes = [1,2,3,4,5,6,9,10,11,14,15,16,20,30,35,38,50,98,99,100,120,200,256,500,795,2000]
wait_tot = []

for w in range(len(wins)):
    win = wins[w]
    idx = last[0]
    maxx = 0
    lambdas = []
    rtt = []
    rts = []
    with open('../results/'+prerun+sim_name+'/overLambdas-nClasses'+str(nClass)+'-N'+str(N)+'-Win'+str(win)+'-Exponential-'+sim_name+'.csv', mode ='r')as file:
    #with open('../sim/res/OverLambdas-nClasses26-N2048-Win'+str(win)+'-Exponential-cellB-Sorted_2048.csv', mode ='r')as file:
        reader = csv.DictReader(file, delimiter=';')
        r = 0
        for row in reader:
            if r != idx:
                r+=1
                continue
            for c in classes:
                rts.append(float(row['T'+str(c)+' Waiting']))
            r+=1


    #print(maxx)

            
    tipe = 'FIFO'
    if win == 10:
        tipe = 'SMASH, w = 10'
    elif win == 0:
        tipe = 'MSF'
    elif win == -2:
        tipe = 'ServerFilling'
    wait_tot.append(rts)
        
    i+=1

ax.boxplot(
    wait_tot,
    widths=0.6,
    boxprops=dict(linewidth=10),
    whiskerprops=dict(linewidth=10),
    capprops=dict(linewidth=10),
    medianprops=dict(linewidth=10),
    flierprops=dict(marker='o', markersize=50, markerfacecolor='blue', alpha=0.7)  # <-- adjust size
)


# X-axis labels
policies = ["FIFO", "SMASH, w=10", "MSF", "ServerFilling"]
ax.set_xticks(range(1, len(policies)+1))
ax.set_xticklabels(policies, fontsize=label_size)

ax.set_yscale('log')
ax.set_ylabel('Average Waiting Time', fontsize=label_size)
ax.set_title('Average Waiting Time vs. Scheduling Policy', fontsize=260)

#plt.xscale('log')
plt.yscale("log")
ax.tick_params(axis='y', which='major', labelsize=tick_size, pad = l_pad)
ax.tick_params(axis='x', which='major', pad = l_pad)
ax.tick_params(axis='both', which='minor', pad = l_pad)
#ax.legend(bbox_to_anchor=(0,1.00), loc='upper left', fontsize = 200,ncol=1)
#ax.set_xlim(left=9, right = 12.5)
#ax.set_ylim(bottom=5, top=10_000)
plt.grid()
#plt.margins(y=0.4)
#set_ymargin(ax, bottom=0, top=100)
plt.savefig('figure_3.pdf')

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
nClass = 26
N = 2048
sim_name = 'tools_B_dist'
maxx = 4.96
dists = ['Exponential','Deterministic','Uniform','Bounded pareto']

for dist in dists:
    lambdas = []
    rtt = []
    rts = []
    with open('../results/'+prerun+sim_name+'/overLambdas-nClasses'+str(nClass)+'-N'+str(N)+'-Win'+str(win)+'-'+dist+'-'+sim_name+'.csv', mode ='r')as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            lambdas.append(float(row['arrival.rate']))
            rts.append(float(row['RespTime Total']))

    # Zip, sort by first list, then unzip
    a_sorted, b_sorted = zip(*sorted(zip(lambdas, rts)))
    
    a_sorted = list(a_sorted)
    b_sorted = list(b_sorted)
            
    ax.plot(a_sorted, b_sorted, label=dist, color = cols[i], ls = styles[j], lw = line_size, markersize = 50, marker = 'o')
        
    i+=1

ax.set_xlabel("Arrival Rate", fontsize=label_size)
ax.set_ylabel("Average Overall Response Time", fontsize=label_size)
#ax.xaxis.set_ticks(np.arange(0.25,0.56,0.05))
#plt.xscale('log')
plt.yscale("log")
plot_filename = "Average Overall Response Time vs. Arrival Rate"
ax.set_title(plot_filename, fontsize=245)
#ax.xaxis.set_ticks([c[-4] for c in measurements[(i*runs):(i*runs)+runs]])
ax.tick_params(axis='both', which='major', labelsize=tick_size, pad = l_pad)
ax.tick_params(axis='both', which='minor', labelsize=tick_size, pad = l_pad)
ax.legend(bbox_to_anchor=(0,1.00), loc='upper left', fontsize = 260,ncol=1)
ax.set_xlim(left=0.1,right=1.6)
ax.set_ylim(bottom=5, top=1000_000)
plt.grid()
#plt.margins(y=0.4)
#set_ymargin(ax, bottom=0, top=100)
plt.savefig('figure_2b.pdf')
