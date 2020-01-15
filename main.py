#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 10 16:30:58 2018

@author: omarschall
"""

import numpy as np
from network import RNN
from fast_weights_network import Fast_Weights_RNN
from simulation import Simulation
from utils import *
from gen_data import *
try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    pass
import time
from optimizers import *
from analysis_funcs import *
from learning_algorithms import *
from metalearning_algorithms import *
from functions import *
from itertools import product
import os
import pickle
from copy import copy
from state_space import State_Space_Analysis
from pdb import set_trace
from scipy.stats import linregress
from scipy.ndimage.filters import uniform_filter1d

if os.environ['HOME']=='/home/oem214':
    n_seeds = 20
    try:
        i_job = int(os.environ['SLURM_ARRAY_TASK_ID']) - 1
    except KeyError:
        i_job = 0
    macro_configs = config_generator(algorithm=['Only_Output_Weights', 'RTRL',
                                                'UORO', 'KF-RTRL', 'R-KF-RTRL',
                                                'BPTT', 'DNI', 'DNIb',
                                                'RFLO', 'KeRNL'],
                                     alpha=[1, 0.5],
                                     task=['Coin', 'Mimic'])
    micro_configs = tuple(product(macro_configs, list(range(n_seeds))))

    params, i_seed = micro_configs[i_job]
    i_config = i_job//n_seeds
    np.random.seed(i_job)

    save_dir = os.environ['SAVEPATH']
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

if os.environ['HOME']=='/Users/omarschall':
    params = {'algorithm': 'DNIb', 'alpha': 1, 'task': 'Coin'}
    i_job = 0
    save_dir = '/Users/omarschall/vanilla-rtrl/library'

    np.random.seed()


if params['alpha'] == 1:
    n_1, n_2 = 5, 9
    tau_task = 1
if params['alpha'] == 0.5:
    n_1, n_2 = 2, 4
    tau_task = 2

if params['task'] == 'Mimic':
    
    n_in = 32
    n_hidden = 32
    n_out = 32
    
    
    
    W_in_target  = np.random.normal(0, np.sqrt(1/(n_in)), (n_hidden, n_in))
    W_rec_target = np.linalg.qr(np.random.normal(0, 1, (n_hidden, n_hidden)))[0]
    W_out_target = np.random.normal(0, np.sqrt(1/(n_hidden)), (n_out, n_hidden))
    b_rec_target = np.random.normal(0, 0.1, n_hidden)
    b_out_target = np.random.normal(0, 0.1, n_out)
    
    alpha = params['alpha']
    
    rnn_target = RNN(W_in_target, W_rec_target, W_out_target,
                     b_rec_target, b_out_target,
                     activation=tanh,
                     alpha=alpha,
                     output=identity,
                     loss=mean_squared_error)

    task = Mimic_RNN(rnn_target, p_input=0.5, tau_task=tau_task)
    
elif params['task'] == 'Coin':
    
    task = Add_Task(n_1, n_2, deterministic=True, tau_task=tau_task)
    
data = task.gen_data(1000000, 5000)

n_in     = task.n_in
n_hidden = 32
n_out    = task.n_out

W_in  = np.random.normal(0, np.sqrt(1/(n_in)), (n_hidden, n_in))
W_rec = np.linalg.qr(np.random.normal(0, 1, (n_hidden, n_hidden)))[0]
W_out = np.random.normal(0, np.sqrt(1/(n_hidden)), (n_out, n_hidden))
W_FB = np.random.normal(0, np.sqrt(1/n_out), (n_out, n_hidden))
b_rec = np.zeros(n_hidden)
b_out = np.zeros(n_out)

alpha = params['alpha']

if params['task'] == 'Coin':
    rnn = RNN(W_in, W_rec, W_out, b_rec, b_out,
              activation=tanh,
              alpha=alpha,
              output=softmax,
              loss=softmax_cross_entropy)

if params['task'] == 'Mimic':
    rnn = RNN(W_in, W_rec, W_out, b_rec, b_out,
              activation=tanh,
              alpha=alpha,
              output=identity,
              loss=mean_squared_error)

optimizer = SGD(lr=0.0001)
SG_optimizer = SGD(lr=0.001)
if params['alpha'] == 1 and params['task'] == 'Coin':
    SG_optimizer = SGD(lr=0.05)
KeRNL_optimizer = SGD(lr=5)

if params['algorithm'] == 'Only_Output_Weights':
    learn_alg = Only_Output_Weights(rnn)
if params['algorithm'] == 'RTRL':
    learn_alg = RTRL(rnn)
if params['algorithm'] == 'UORO':
    learn_alg = UORO(rnn)
if params['algorithm'] == 'KF-RTRL':
    learn_alg = KF_RTRL(rnn)
if params['algorithm'] == 'R-KF-RTRL':
    learn_alg = Reverse_KF_RTRL(rnn)
if params['algorithm'] == 'BPTT':
    learn_alg = Future_BPTT(rnn, 10)
if params['algorithm'] == 'DNI':
    learn_alg = DNI(rnn, SG_optimizer)
if params['algorithm'] == 'DNIb':
    J_lr = 0.001
    if params['alpha'] == 1 and params['task'] == 'Coin':
        J_lr = 0.01
    learn_alg = DNI(rnn, SG_optimizer, use_approx_J=True, J_lr=J_lr,
                    SG_label_activation=tanh, W_FB=W_FB)
    learn_alg.name = 'DNIb'
if params['algorithm'] == 'RFLO':
    learn_alg = RFLO(rnn, alpha=alpha)
if params['algorithm'] == 'KeRNL':
    learn_alg = KeRNL(rnn, KeRNL_optimizer, sigma_noise=0.001)

comp_algs = []

monitors = ['net.loss_']

sim = Simulation(rnn)
sim.run(data, learn_alg=learn_alg, optimizer=optimizer,
        comp_algs=comp_algs,
        monitors=monitors,
        verbose=True,
        check_accuracy=False,
        check_loss=True)

#Filter losses
loss = sim.mons['net.loss_']
downsampled_loss = np.nanmean(loss.reshape((-1, 10000)), axis=1)
filtered_loss = uniform_filter1d(downsampled_loss, 10)
processed_data = {'filtered_loss': filtered_loss}

if os.environ['HOME']=='/Users/omarschall':


    plot_filtered_signals([sim.mons['net.loss_'],
                           sim.mons['learn_alg.A_loss'],
                           sim.mons['learn_alg.J_loss']])

    #Test run
    np.random.seed(2)
    n_test = 1000
    data = task.gen_data(100, n_test)
    test_sim = copy(sim)
    test_sim.run(data,
                 mode='test',
                 monitors=['net.loss_', 'net.y_hat', 'net.a'],
                 verbose=False)
    fig = plt.figure()
    plt.plot(test_sim.mons['net.y_hat'][:,0])
    plt.plot(data['test']['Y'][:,0])
    plt.plot(data['test']['X'][:,0]*0.1)
    #plt.legend(['Prediction', 'Label', 'Stimulus'])#, 'A Norm'])
    #plt.ylim([-0.2, 0.2])
    for i in range(n_test//task.time_steps_per_trial):
        continue
        plt.axvline(x=i*task.time_steps_per_trial, color='k', linestyle='--')
    plt.xlim([0, 200])
    #fig.savefig()

    plt.figure()
    x = test_sim.mons['net.y_hat'].flatten()
    y = data['test']['Y'].flatten()
    plt.plot(x, y, '.', alpha=0.05)
    plt.plot([np.amin(x), np.amax(x)],
              [np.amin(y), np.amax(y)], 'k', linestyle='--')
    plt.axis('equal')

if os.environ['HOME']=='/home/oem214':

    result = {'sim': sim, 'i_seed': i_seed, 'task': task,
              'config': params, 'i_config': i_config, 'i_job': i_job,
              'processed_data': processed_data}
    save_dir = os.environ['SAVEPATH']
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    save_path = os.path.join(save_dir, 'rnn_'+str(i_job))

    with open(save_path, 'wb') as f:
        pickle.dump(result, f)




























