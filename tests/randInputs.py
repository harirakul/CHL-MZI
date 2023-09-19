import copy

from vivilux import *
from vivilux.metrics import RMSE
from vivilux.learningRules import CHL, GeneRec

import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
np.random.seed(seed=0)


numSamples = 40
numEpochs = 100


#define input and output data (must be normalized and positive-valued)
vecs = np.random.normal(size=(numSamples, 4))
mags = np.linalg.norm(vecs, axis=-1)
inputs = np.abs(vecs/mags[...,np.newaxis])
vecs = np.random.normal(size=(numSamples, 4))
mags = np.linalg.norm(vecs, axis=-1)
targets = np.abs(vecs/mags[...,np.newaxis])
del vecs, mags

netGR = RecurNet([
    Layer(4, isInput=True),
    GainLayer(4, learningRule=GeneRec),
    GainLayer(4, learningRule=GeneRec)
], AbsMesh, name = "NET_GR")

netGR3 = RecurNet([
    Layer(4, isInput=True),
    GainLayer(4, learningRule=GeneRec),
    GainLayer(4, learningRule=GeneRec),
    GainLayer(4, learningRule=GeneRec)
], AbsMesh, name = "NET_GR3")

netGR4 = RecurNet([
    Layer(4, isInput=True),
    GainLayer(4, learningRule=GeneRec),
    GainLayer(4, learningRule=GeneRec),
    GainLayer(4, learningRule=GeneRec),
    GainLayer(4, learningRule=GeneRec)
], AbsMesh, name = "NET_GR4")

netCHL = RecurNet([
    Layer(4, isInput=True),
    GainLayer(4, learningRule=CHL),
    GainLayer(4, learningRule=CHL)
], AbsMesh, name = "NET_CHL")


netMixed = RecurNet([
    Layer(4, isInput=True),
    GainLayer(4, learningRule=CHL),
    GainLayer(4, learningRule=GeneRec)
], AbsMesh, name = "NET_Mixed")


netMixed2 = RecurNet([
    Layer(4, isInput=True),
    GainLayer(4, learningRule=CHL),
    GainLayer(4, learningRule=CHL)
], AbsMesh, name = "NET_Freeze")
netMixed2.layers[1].Freeze()

sig = lambda x: tf.math.sigmoid(10*(x-0.5))
refModel = tf.keras.models.Sequential([
    tf.keras.layers.InputLayer(input_shape=(4,)),
    tf.keras.layers.Dense(4, use_bias=False, activation=sig),
    tf.keras.layers.Dense(4, use_bias=False, activation=sig),
])
refModel.compile(optimizer=tf.keras.optimizers.SGD(0.001084),
                 loss = "mse",
                 metrics = "mse"
)

refResult = np.sqrt(refModel.fit(inputs, targets, epochs=numEpochs, batch_size=1).history["mse"])
plt.plot(refResult, label="SGD")

resultMixed = netMixed.Learn(inputs, targets, numEpochs=numEpochs, reset=True)
plt.plot(resultMixed, label="Mixed")

resultMixed2 = netMixed2.Learn(inputs, targets, numEpochs=numEpochs, reset=True)
plt.plot(resultMixed2, label="Frozen 1st layer")

resultGR = netGR.Learn(inputs, targets, numEpochs=numEpochs, reset=True)
plt.plot(resultGR, label="GeneRec")

resultGR3 = netGR3.Learn(inputs, targets, numEpochs=numEpochs, reset=True)
plt.plot(resultGR3, label="GeneRec (3 layer)")

resultGR4 = netGR4.Learn(inputs, targets, numEpochs=numEpochs, reset=True)
plt.plot(resultGR4, label="GeneRec (4 layer)")

baseline = np.mean([RMSE(entry/np.sqrt(np.sum(np.square(entry))), targets) for entry in np.random.uniform(size=(2000,numSamples,4))])
plt.axhline(y=baseline, color="b", linestyle="--", label="baseline guessing")

plt.title("Random Input/Output Matching")
plt.ylabel("RMSE")
plt.xlabel("Epoch")
plt.legend()
plt.show()

print("Done")
