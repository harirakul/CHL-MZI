import vivilux as vl
import vivilux.photonics
from vivilux import FFFB, Layer, Mesh, InhibMesh
from vivilux.learningRules import CHL, GeneRec, ByPass
from vivilux.optimizers import Adam

import matplotlib.pyplot as plt
import numpy as np
np.random.seed(seed=0)

import pandas as pd
import seaborn as sns

numSamples = 40
numEpochs = 50



#define input and output data (must be normalized and positive-valued)
vecs = np.random.normal(size=(numSamples, 4))
mags = np.linalg.norm(vecs, axis=-1)
inputs = np.abs(vecs/mags[...,np.newaxis])
vecs = np.random.normal(size=(numSamples, 4))
mags = np.linalg.norm(vecs, axis=-1)
targets = np.abs(vecs/mags[...,np.newaxis])
del vecs, mags


optParams = {"lr" : 0.05,
            "beta1" : 0.9,
            "beta2": 0.999,
            "epsilon": 1e-08}


netMixed_MZI_Adam = FFFB([
        vl.photonics.PhotonicLayer(4, isInput=True),
        vl.photonics.PhotonicLayer(4, learningRule=CHL),
        vl.photonics.PhotonicLayer(4, learningRule=CHL)
    ], vl.photonics.MZImesh, FeedbackMesh=vl.photonics.phfbMesh,
    learningRate = 0.1,
    name = f"NET_Mixed_FF-{1.0:.2}_FB-{1.0:.2}_Tau-{1/1.4:.2}_FF0-{0.1:.2}",
    optimizer = Adam(**optParams), monitoring = True)

resultMixedMZI_Adam = netMixed_MZI_Adam.Learn(
    inputs, targets, numEpochs=numEpochs, reset=False)


                
plt.title("Random Input/Output Matching with MZI meshes")
plt.ylabel("RMSE")
plt.xlabel("Epoch")
plt.legend()
plt.show()
plt.show()