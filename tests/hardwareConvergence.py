from vivilux import *
from vivilux.nets import Net, layerConfig_std
from vivilux.layers import Layer
import vivilux.hardware
from vivilux.learningRules import CHL
from vivilux.optimizers import Simple

import matplotlib.pyplot as plt
import numpy as np
np.random.seed(seed=0)

import pandas as pd

# from sklearn import datasets

from datetime import timedelta
from time import time

# np.set_printoptions(precision=3, suppress=True)


mziMapping = [(1,0),
              (1,1),
              (1,3),
              (1,5),
              (1,6),
              (2,0)
              ]
barMZI = [(1,4,4.4),
          (2,1,3.4)
          ]

optArgs = {"lr" : 0.1,
            "beta1" : 0.9,
            "beta2": 0.999,
            "epsilon": 1e-08}

meshArgs = {"mziMapping": mziMapping,
            "barMZI": barMZI,
            # "outChannels": [13, 0, 1, 2],
            "outChannels": [2, 1, 0, 13],
            "inChannels": [10,9,8,12],
            # "inChannels": [12,8,9,10],
            "updateMagnitude": 0.1,
            # "updateMagnitude": 0.5,
            }

layerList = [Layer(4, isInput=True),
             Layer(4, learningRule=CHL),
             ]
netMZI = Net(name = "Net_MZI")# , vl.hardware.HardMZI, FeedbackMesh=vl.photonics.phfbMesh,
netMZI.AddLayers(layerList)
ffMeshConfig = {"meshType": vivilux.hardware.HardMZI,
                "meshArgs": {"AbsScale": 1,
                             "RelScale": 1},
                }
ffMeshes = netMZI.AddConnection(layerList[0], layerList[1],
                                meshConfig=ffMeshConfig)

# handles for convenience
mesh = netMZI.layers[1].excMeshes[0]
inGen = mesh.inGen
magnitude = vivilux.hardware.magnitude
L1norm = vivilux.hardware.L1norm


numDeltas = 5

startMatrices = []
allDeltas = []
targetMatrices = []
finalMatrices = []
RECORDS = []
successes = []
numIter = []
initMag = []


print("\n\n","-"*80,"\nSTARTING CONVERGENCE TEST\n\n")
#%% Conergence test
for iteration in range(50):
    print(f"\tIteration: {iteration}")
    init = 0.25*np.random.rand(6,1)+2
    target = 0.25*np.random.rand(6,1)+2
    mesh.setParams([init])
    try:
        startMatrix = mesh.get()
    except AssertionError as msg:
        print(msg)
        print("SKIPPING ITERATION")
        continue
    
    try:
        targetMatrix = mesh.get([target])
    except AssertionError as msg:
        print(msg)
        print("SKIPPING ITERATION")
        continue
    startMatrices.append(startMatrices)
    strMatrix = str(startMatrix).replace('\n','\n\t\t')
    print(f"\t\tInitial matrix:\n\t\t{strMatrix}")
    strVoltages = str(mesh.getParams()[0]).replace('\n','\n\t\t')
    print(f"\t\tInitial voltages: {strVoltages}")
    strVoltages2 = str(target).replace('\n','\n\t\t')
    print(f"\t\tTarget voltages: {strVoltages2}")
    targetMatrices.append(targetMatrix)
    
    #Generate Delta
    delta = targetMatrix - startMatrix
    allDeltas.append(delta)
    print("\t\tTarget matrix:\n\t\t", str(targetMatrix).replace('\n','\n\t\t'))
    # delta = targetMatrix - startMatrix
    magDelta  = magnitude(delta)
    initMag.append(magDelta)
    # strMag = str(magnitude(delta))#.replace('\n','\n\t\t')
    print(f"\t\tStarting with Delta magnitude: {magDelta}...")
    # startingDeltas.append(delta)
    
    start = time()
    try:
        record, params, matrices = mesh.ApplyDelta(delta, eta=1,
                                                     numDirections=3, 
                                                     numSteps=30,
                                                      earlyStop=8e-2
                                                     )
        finalMatrices.append(matrices[-1])
        strVoltages3 = str(mesh.getParams()[0]).replace('\n','\n\t\t')
        print(f"\t\tFinal voltages: {strVoltages3}")
    except AssertionError as msg:
        print(msg)
        # record = -np.ones((4,4))
        # results = pd.concat([results, {"initMag": magDelta,
        #                            "iteration": iteration,
        #                            "numIter": -1,
        #                            "finalMag": -1,
        #                            "success": False,
        #                            "record": record}])
        finalMatrices.append(False)
        successes.append(False)
        RECORDS.append(-np.ones(31))
        continue
    end = time()
    print("\tExecution took: ", timedelta(seconds=(end-start)))
    iterToConverge = len(record)
    numIter.append(iterToConverge)
    print(f"\tTook {iterToConverge} iterations to converge.")
    finalMag = record[-1]
    record = np.pad(record, (0, 31-len(record)))
    RECORDS.append(record)
    successes.append(True)

    
    
vivilux.hardware.DAC_Init()
inGen.agilent.lasers_on([0,0,0,0])
print("\n\nSUCCESSFULLY FINISHED. PLEASE MAKE SURE LASER AND TEMPERATURE CONTROL ARE OFF.")

##%% Plot Convergence versus magnitude
converged = np.array(numIter) < 31
x = np.array(initMag)[successes][converged]
y = np.array(numIter)[converged]
#find line of best fit
a, b = np.polyfit(x, y, 1)
plt.figure()
plt.scatter(x, y)
fitX = np.linspace(0, 1.2*np.max(x), 20)
fitY = a*fitX + b
plt.plot(fitX, fitY, "--", label=f"{a:.2f}x+{b:.2f}")
plt.title("Convergence versus magnitude")
plt.xlabel("Initial magnitude of difference vector")
plt.ylabel("Number of iterations to converge")
plt.xlim(0, np.max(x)*1.2)
plt.ylim(0, np.max(y)*1.2)
plt.legend()
plt.show()


