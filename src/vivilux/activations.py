import numpy as np

def Sigmoid(A=1, B=4, C=0.5):
    return lambda input: A/(1 + np.exp(-B*(input-C)))