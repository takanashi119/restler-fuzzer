import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import random

def mutation(string_to_mutate,mutation_rate=0.5):
    encoded_bytes = string_to_mutate.encode('utf-8')
    byte_list = list(encoded_bytes)
    for i in range(len(byte_list)):
        if random.random() < mutation_rate:
            byte_list[i] = random.randint(0, 255)
    mutated_bytes = bytes(byte_list)
    mutated_string = mutated_bytes.decode('utf-8', errors='ignore') 
    return mutated_string