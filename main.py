#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 10 16:30:58 2018

@author: omarschall
"""

import numpy as np
from network import *
from simulation import *
from gen_data import *
try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    pass
from optimizers import *
from analysis_funcs import *
from learning_algorithms import *
from functions import *
from itertools import product
import os
import pickle
from copy import deepcopy
from scipy.ndimage.filters import uniform_filter1d
from sklearn import linear_model
from state_space import *
from dynamics import *
import multiprocessing as mp
from functools import partial
from sklearn.cluster import DBSCAN

if os.environ['HOME'] == '/home/oem214':
    n_seeds = 1
    try:
        i_job = int(os.environ['SLURM_ARRAY_TASK_ID']) - 1
    except KeyError:
        i_job = 0
    macro_configs = config_generator(i_start=list(range(0, 100000, 1000)),
                                     algorithm=['E-BPTT', 'RFLO'])
    micro_configs = tuple(product(macro_configs, list(range(n_seeds))))

    params, i_seed = micro_configs[i_job]
    i_config = i_job//n_seeds
    np.random.seed(i_job)

    save_dir = os.environ['SAVEPATH']
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
        
if os.environ['HOME'] == '/Users/omarschall':
    params = {'algorithm': 'RFLO', 'i_start': 45000}
    i_job = 0
    save_dir = '/Users/omarschall/vanilla-rtrl/library'

    #np.random.seed(1)

# np.random.seed(0)
# task = Flip_Flop_Task(3, 0.05, tau_task=1)
# N_train = 100
# N_test = 10000
# data = task.gen_data(N_train, N_test)
# with open('notebooks/good_ones/{}_net'.format(params['algorithm']), 'rb') as f:
#     sim = pickle.load(f)
    
# sim.resume_sim_at_checkpoint(data, 99999, N=100001, checkpoint_interval=100)

file_exists = True
try:
    with open('library/bptt_rflo/result_{}'.format(i_job), 'rb') as f:
        result = pickle.load(f)
except FileNotFoundError:
    file_exists = False
    
if file_exists:
    for i_checkpoint in range(params['i_start'],
                              params['i_start'] + 1000, 100):
        get_graph_structure(result['checkpoint_{}'.format(i_checkpoint)],
                            N=100, time_steps=5, parallelize=False)
    

# result = {}
# for i_checkpoint in range(params['i_start'], params['i_start'] + 1000, 100):
#     analyze_checkpoint(sim.checkpoints[i_checkpoint], data, verbose=False,
#                         sigma_pert=0.5, N=600, parallelize=False,
#                         N_iters=8000, same_LR_criterion=7000)
    
#     result['checkpoint_{}'.format(i_checkpoint)] = deepcopy(sim.checkpoints[i_checkpoint])
    
# np.random.seed(i_job)

# n_in = task.n_in
# n_hidden = 64
# n_out = task.n_out

# W_in  = np.random.normal(0, np.sqrt(1/(n_in)), (n_hidden, n_in))
# W_rec = np.linalg.qr(np.random.normal(0, 1, (n_hidden, n_hidden)))[0]
# W_out = np.random.normal(0, np.sqrt(1/(n_hidden)), (n_out, n_hidden))
# W_FB = np.random.normal(0, np.sqrt(1/n_out), (n_out, n_hidden))

# b_rec = np.zeros(n_hidden)
# b_out = np.zeros(n_out)

# alpha = 1

# rnn = RNN(W_in, W_rec, W_out, b_rec, b_out,
#           activation=tanh,
#           alpha=alpha,
#           output=identity,
#           loss=mean_squared_error)

# optimizer = SGD_Momentum(lr=0.0005, mu=0.6, clip_norm=0.3)
# if params['algorithm'] == 'E-BPTT':
#     learn_alg = Efficient_BPTT(rnn, 10, L2_reg=0.0001)
# elif params['algorithm'] == 'RFLO':
#     learn_alg = RFLO(rnn, alpha=alpha, L2_reg=0.0001)

# comp_algs = []
# monitors = []

# sim = Simulation(rnn)
# sim.run(data, learn_alg=learn_alg, optimizer=optimizer,
#         comp_algs=comp_algs,
#         monitors=monitors,
#         verbose=True,
#         report_accuracy=False,
#         report_loss=True,
#         checkpoint_interval=10000)
#         #checkpoint_interval=list(range(10000, 30000, 10)))

# # with open('notebooks/good_ones/RFLO_net_prezzy', 'rb') as f:
# #     sim = pickle.load(f)
# # #result = {}
# # # for i_checkpoint in range(0, 100000, 10000):
# analyze_checkpoint(sim.checkpoints[0], data, verbose=False,
#                     sigma_pert=0.5, N=600, parallelize=True,
#                     N_iters=8000, same_LR_criterion=7000)
    
# plot_checkpoint_results(sim.checkpoints[0], data, plot_test_points=True,
#                         plot_cluster_means=True)

# #     #result['checkpoint_{}'.format(i_checkpoint)] = deepcopy(sim.checkpoints[i_checkpoint])

# # plot_checkpoint_results(sim.checkpoints[99999], data,
# #                         plot_cluster_means=True)

# with open('notebooks/good_ones/{}_net_prezzy'.format(params['algorithm']), 'wb') as f:
#     pickle.dump(sim, f)

if os.environ['HOME'] == '/Users/omarschall':

    plt.figure()
    n_filter = 2000
    filtered_loss = uniform_filter1d(sim.mons['rnn.loss_'], n_filter)
    rec_grad_norms = uniform_filter1d(sim.mons['learn_alg.rec_grads-norm'], n_filter)
    rec_grad_norms *= (np.amax(filtered_loss) / np.amax(rec_grad_norms))
    plt.plot(filtered_loss)
    plt.plot(rec_grad_norms)
    plt.xticks(list(range(0, 100000, 10000)))
    
    plt.figure()
    plt.plot(sim.mons['rnn.loss_'], sim.mons['learn_alg.rec_grads-norm'], '.', alpha=0.08)
    
    rnn = sim.checkpoints[0]['rnn']
    test_sim = Simulation(rnn)
    test_sim.run(data,
                  mode='test',
                  monitors=['rnn.loss_', 'rnn.y_hat', 'rnn.a'],
                  verbose=False)
    
    plt.figure()
    plt.plot(data['test']['X'][:, 0] + 2.5, (str(0.6)), linestyle='--')
    plt.plot(data['test']['Y'][:, 0] + 2.5, 'C0')
    plt.plot(test_sim.mons['rnn.y_hat'][:, 0] + 2.5, 'C3')
    plt.plot(data['test']['X'][:, 1], (str(0.6)), linestyle='--')
    plt.plot(data['test']['Y'][:, 1], 'C0')
    plt.plot(test_sim.mons['rnn.y_hat'][:, 1], 'C3')
    plt.plot(data['test']['X'][:, 2] - 2.5, (str(0.6)), linestyle='--')
    plt.plot(data['test']['Y'][:, 2] - 2.5, 'C0')
    plt.plot(test_sim.mons['rnn.y_hat'][:, 2] - 2.5, 'C3')
    plt.xlim([0, 1000])
    plt.yticks([])
    plt.xlabel('time steps')

if os.environ['HOME'] == '/home/oem214' and file_exists:

    # result = {'sim': sim, 'i_seed': i_seed, 'task': task,
    #           'config': params, 'i_config': i_config, 'i_job': i_job,
    #           'processed_data': processed_data}
    result['i_job'] = i_job
    result['config'] = params
    save_dir = os.environ['SAVEPATH']
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    save_path = os.path.join(save_dir, 'result_'+str(i_job))

    with open(save_path, 'wb') as f:
        pickle.dump(result, f)




























