import numpy as np

def Detect(input):
    '''DC power detected (no cross terms)
    '''
    return np.square(np.abs(np.sum(input, axis=-1)))

def Diagonalize(vector):
    '''Turns a vector into a diagonal matrix to simulate independent wavelength
       components that don't have constructive/destructive interference.
    '''
    diag = np.eye(len(vector))
    for i in range(len(vector)):
        diag[i,i] = vector[i]
    return diag

def BoundTheta(thetas):
    '''Bounds the size of phase shifts between 1-2pi.
    '''
    thetas[thetas > (2*np.pi)] -= 2*np.pi
    thetas[thetas < 0] += 2*np.pi
    return thetas

def psToRect(phaseShifters, size):
    '''Calculates the implemented matrix of rectangular MZI from its phase 
        shifts. Assumes ideal components.
    '''
    fullMatrix = np.eye(size, dtype=np.cdouble)
    index = 0
    for stage in range(size):
        stageMatrix = np.eye(size, dtype=np.cdouble)
        parity = stage % 2 # even or odd stage
        for wg in range(parity, size, 2): 
            # add MZI weights in pairs
            if wg >= size-1: break # handle case of last pair
            theta, phi = phaseShifters[index]
            index += 1
            stageMatrix[wg:wg+2,wg:wg+2] = np.array([[np.exp(1j*phi)*np.sin(theta),np.cos(theta)],
                                                     [np.exp(1j*phi)*np.cos(theta),-np.sin(theta)]],
                                                     dtype=np.cdouble)
        fullMatrix[:] = stageMatrix @ fullMatrix
    return fullMatrix