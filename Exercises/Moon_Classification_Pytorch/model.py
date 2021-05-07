import torch
import torch.nn as nn
import torch.nn.functional as F

## TODO: Complete this classifier
class SimpleNet(nn.Module):
    
    ## TODO: Define the init function
    def __init__(self, input_dim, hidden_dim, output_dim):
        '''Defines layers of a neural network.
           :param input_dim: Number of input features
           :param hidden_dim: Size of hidden layer(s)
           :param output_dim: Number of outputs
         '''
        super(SimpleNet, self).__init__()

        #         From my past experience i use this formula to find the optimal number of nodes
        #         Nh=Ns(α∗(Ni+No)) = 500

        #         Ni = number of input neurons.
        #         No = number of output neurons.
        #         Ns = number of samples in training data set.
        #         α = an arbitrary scaling factor usually 2-10.
        
        #         Nh = ... = [22,75]
        
        # define all layers, here. I choose 4 layers andone Dropout.
        
        print("Default numbers for, input_dim, hidden_dim, output_dim", input_dim, hidden_dim, output_dim)
        hid_layer1 = 50
        hid_layer2 = 45
        hid_layer3 = 40
        
        self.fc1 = nn.Linear(input_dim, hid_layer1)
        self.fc2 = nn.Linear(hidden_1, hid_layer2)
        self.fc3 = nn.Linear(hid_layer2, output_dim)
        # dropout prevents overfitting of data
        self.dropout = nn.Dropout(0.2)
        
    
    ## TODO: Define the feedforward behavior of the network
    def forward(self, x):
        '''Feedforward behavior of the net.
           :param x: A batch of input features
           :return: A single, sigmoid activated value
         '''
        out = F.relu(self.fc1(x))
        x = F.leaky_relu(self.fc1(x), negative_slope=0.01)
        x = self.dropout(x)
        x = F.leaky_relu(self.fc2(x), negative_slope=0.01)
        x = self.dropout(x)
        BN = nn.BatchNorm1d(input_dim)
        BN_x = BN(x)
        x = F.leaky_relu(self.fc3(BN_x), negative_slope=0.01)
        
        return x