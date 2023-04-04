'''
A library for Hebbian-like learning implementations on MZI meshes based on the
work of O'Reilly et al. [1] in computation.

REFERENCES:
[1] O'Reilly, R. C., Munakata, Y., Frank, M. J., Hazy, T. E., and
    Contributors (2012). Computational Cognitive Neuroscience. Wiki Book,
    4th Edition (2020). URL: https://CompCogNeuro.org

[2] R. C. O'Reilly, “Biologically Plausible Error-Driven Learning Using
    Local Activation Differences: The Generalized Recirculation Algorithm,”
    Neural Comput., vol. 8, no. 5, pp. 895-938, Jul. 1996, 
    doi: 10.1162/neco.1996.8.5.895.
'''

from collections.abc import Iterator

import numpy as np
np.random.seed(seed=0)

# import defaults
from .activations import Sigmoid
from .metrics import RMSE
from .learningRules import CHL

# library constants
DELTA_TIME = 0.1

class Net:
    '''Base class for neural networks with Hebbian-like learning
    '''
    def __init__(self, layers: iter, meshType, metric = RMSE, learningRate = 0.1):
        '''Instanstiates an ordered list of layers that will be
            applied sequentially during inference.
        '''
        # TODO: allow different mesh types between layers
        self.layers = layers
        self.metric = metric

        for index, layer in enumerate(self.layers[1:], 1):
            size = len(layer)
            layer.addMesh(meshType(size, self.layers[index-1], learningRate))

    def Predict(self, data):
        '''Inference method called 'prediction' in accordance with a predictive
            error-driven learning scheme of neural network computation.
        '''
        # outputs = []
        self.layers[0].ClampPre(data)

        for layer in self.layers[1:-1]:
            layer.Predict()

        output = self.layers[-1].Predict()
        
        return output

    def Observe(self, inData, outData):
        '''Training method called 'observe' in accordance with a predictive
            error-driven learning scheme of neural network computation.
        '''
        self.layers[0].ClampObs(inData)
        self.layers[-1].ClampObs(outData)
        for layer in self.layers[1:-1]:
            layer.Observe()
        # self.layers[-1].ClampObs(outData)

        return None # observations know the outcome

    def Infer(self, inData, numTimeSteps=25):
        outputData = np.zeros(inData.shape)
        index = 0
        for inDatum in inData:
            for time in range(numTimeSteps):
                result = self.Predict(inDatum)
            # for layer in self.layers[1:]:
            #         layer.obsLin = layer.preLin
            #         layer.obsAct = layer.preAct
            outputData[index] = result
            index += 1
        return outputData

    
    def Learn(self, inData, outData,
              numTimeSteps=50, numEpochs=50,
              verbose = False, reset = False):
        '''Control loop for learning based on GeneRec-like algorithms.
                inData      : input data
                outData     : 
                verbose     : if True, prints net each iteration
                reset       : if True, resets activity between each input sample
        '''
        results = np.zeros(numEpochs+1)
        results[0] = self.Evaluate(inData, outData, numTimeSteps)
        epochResults = np.zeros((len(outData), len(self.layers[-1])))
        for epoch in range(numEpochs):
            # iterate through data and time
            index=0
            for inDatum, outDatum in zip(inData, outData):
                if reset: self.resetActivity()
                # TODO: MAKE ACTIVATIONS CONTINUOUS
                ### Data should instead be recorded and labeled at the end of each phase
                for time in range(numTimeSteps):
                    lastResult = self.Predict(inDatum)
                epochResults[index][:] = lastResult
                index += 1
                for layer in self.layers[1:]:
                    layer.obsLin[:] = layer.preLin
                    layer.obsAct[:] = layer.preAct
                for time in range(numTimeSteps):
                    self.Observe(inDatum, outDatum)
                # update meshes
                for layer in self.layers:
                    layer.Learn()
                # make activation variable continuous
                for layer in self.layers[1:]:
                    layer.preLin[:] = layer.obsLin
                    layer.preAct[:] = layer.obsAct
            # evaluate metric
            results[epoch+1] = self.metric(epochResults, outData)
            if verbose: print(self)
        
        return results
    
    def Evaluate(self, inData, outData, numTimeSteps=25):
        results = self.Infer(inData, numTimeSteps)
        return self.metric(results, outData)

    def getWeights(self, ffOnly):
        weights = []
        for layer in self.layers:
            for mesh in layer.meshes:
                weights.append(mesh.get())
                if ffOnly: break
        return weights
    
    def getActivity(self):
        for layer in self.layers:
            "\n".join(layer.getActivity())

    def resetActivity(self):
        for layer in self.layers:
            layer.resetActivity()

    def setLearningRule(self, rule, layerIndex: int = -1):
        '''Sets the learning rule for all forward meshes to 'rule'.
        '''
        if layerIndex == -1 :
            for layer in self.layers:
                layer.rule = rule
        else:
            self.layers[layerIndex].rule = rule

    def __str__(self) -> str:
        strs = []
        for layer in self.layers:
            strs.append(str(layer))

        return "\n\n".join(strs)

class Mesh:
    '''Base class for meshes of synaptic elements.
    '''
    count = 0
    def __init__(self, size: int, inLayer, learningRate=0.5):
        self.size = size if size > len(inLayer) else len(inLayer)
        self.matrix = np.eye(self.size)
        self.inLayer = inLayer
        self.rate = learningRate


        self.name = f"MESH_{Mesh.count}"
        Mesh.count += 1

    def set(self, matrix):
        self.matrix = matrix

    def get(self):
        return self.matrix

    def apply(self, data):
        try:
            return self.matrix @ data
        except ValueError as ve:
            print(f"Attempted to apply {data} (shape: {data.shape}) to mesh "
                  f"of dimension: {self.matrix}")

    def Predict(self):
        data = self.inLayer.preAct
        return self.apply(data)

    def Observe(self):
        data = self.inLayer.obsAct
        return self.apply(data)

    def Update(self, delta):
        self.matrix += self.rate*delta

    def __len__(self):
        return self.size

    def __str__(self):
        return f"\n\t\t{self.name.upper()} ({self.size} <={self.inLayer.name}) = {self.get()}"

class fbMesh(Mesh):
    '''A class for feedback meshes based on the transpose of another mesh.
    '''
    def __init__(self, mesh: Mesh, inLayer) -> None:
        super().__init__(mesh.size, inLayer)
        self.name = "TRANSPOSE_" + mesh.name
        self.mesh = mesh

    def set(self):
        raise Exception("Feedback mesh has no 'set' method.")

    def get(self):
        return self.mesh.get().T

    def apply(self, data):
        matrix = self.mesh.matrix.T
        try:
            return matrix @ data
        except ValueError as ve:
            print(f"Attempted to apply {data} (shape: {data.shape}) to mesh of dimension: {matrix}")

    def Update(self, delta):
        return None

class Layer:
    '''Base class for a layer that includes input matrices and activation
        function pairings. Each layer retains a seperate state for predict
        and observe phases, along with a list of input meshes applied to
        incoming data.
    '''
    count = 0
    def __init__(self, length, activation=Sigmoid, learningRule=CHL, isInput = False, name = None):
        self.preLin = np.zeros(length)
        self.preAct = np.zeros(length)
        
        self.obsLin = np.zeros(length)
        self.obsAct = np.zeros(length)
        self.act = activation
        self.rule = learningRule
        self.meshes = [] #empty initial mesh list

        self.isInput = isInput
        self.freeze = False
        self.name =  f"LAYER_{Layer.count}" if name == None else name
        if isInput: self.name = "INPUT_" + self.name
        Layer.count += 1

    def Freeze(self):
        self.freeze = True

    def Unfreeze(self):
        self.freeze = False
    
    def addMesh(self, mesh):
        self.meshes.append(mesh)

    def Predict(self):
        self.preLin -= DELTA_TIME*self.preLin
        for mesh in self.meshes:
            self.preLin += DELTA_TIME * mesh.Predict()[:len(self)]**2
        self.preAct = self.act(self.preLin)
        return self.preAct

    def Observe(self):
        self.obsLin -= DELTA_TIME * self.obsLin
        for mesh in self.meshes:
            self.obsLin += DELTA_TIME * mesh.Observe()[:len(self)]**2
        self.obsAct = self.act(self.obsLin)
        return self.obsAct

    def ClampPre(self, data):
        self.preLin = data[:len(self)]
        self.preAct = data[:len(self)]

    def ClampObs(self, data):
        self.obsLin = data[:len(self)]
        self.obsAct = data[:len(self)]

    def Learn(self):
        if self.isInput or self.freeze: return
        # TODO: Allow multiple meshes to learn, skip fb meshes
        inLayer = self.meshes[0].inLayer # assume first mesh as input
        delta = self.rule(inLayer, self)
        self.meshes[0].Update(delta)

    def getActivity(self):
        return [self.preLin, self.preAct, self.obsLin, self.obsAct]
    
    def resetActivity(self):
        '''Resets all activation traces to zero vectors.'''
        length = len(self)
        self.preLin = np.zeros(length)
        self.preAct = np.zeros(length)
        
        self.obsLin = np.zeros(length)
        self.obsAct = np.zeros(length)

    def __len__(self):
        return len(self.preAct)

    def __str__(self) -> str:
        layStr = f"{self.name} ({len(self)}): \n\tActivation = {self.act}\n\tLearning"
        layStr += f"Rule = {self.rule}"
        layStr += f"\n\tMeshes: " + "\n".join([str(mesh) for mesh in self.meshes])
        layStr += f"\n\tActivity: {self.preLin}, {self.preAct}, {self.obsLin}, {self.obsAct}"
        return layStr

class FFFB(Net):
    '''A network with feed forward and feedback meshes between each
        layer. Based on ideas presented in [2]
    '''
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for index, layer in enumerate(self.layers[1:-1], 1): 
            #skip input and output layers, add feedback matrices
            nextLayer = self.layers[index+1]
            layer.addMesh(fbMesh(nextLayer.meshes[0], nextLayer))


if __name__ == "__main__":
    from .learningRules import GeneRec
    
    from sklearn import datasets
    import matplotlib.pyplot as plt

    net = FFFB([
        Layer(4, isInput=True),
        Layer(4, learningRule=GeneRec),
        Layer(4, learningRule=GeneRec)
    ], Mesh)

    iris = datasets.load_iris()
    inputs = iris.data
    maxMagnitude = np.max(np.sqrt(np.sum(np.square(inputs), axis=1)))
    inputs = inputs/maxMagnitude # bound on (0,1]
    targets = np.zeros((len(inputs),4))
    targets[np.arange(len(inputs)), iris.target] = 1
    #shuffle both arrays in the same manner
    shuffle = np.random.permutation(len(inputs))
    inputs, targets = inputs[shuffle], targets[shuffle]

    result = net.Learn(inputs, targets, numEpochs=500)
    plt.plot(result)
    plt.show()