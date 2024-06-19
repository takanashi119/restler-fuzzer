import random
from engine.core.requests import GrammarRequestCollection
class dict_mutator:
    def mutate_value(self,value):
        try:
            if isinstance(value, int):
                return value + random.randint(-10, 10)
            elif isinstance(value, float):
                return value * random.uniform(0.9, 1.1)
            elif isinstance(value, str):
                return value + random.choice('abcdefghijklmnopqrstuvwxyz')
        except:
            pass

    def mutated_dict(self,num_mutations=5):
        
        # candidate_pool=GrammarRequestCollection().candidate_values_pool.candidate_values['restler_fuzzable_string'].values
        candidate_pool=GrammarRequestCollection().candidate_values_pool
        candidate_values=candidate_pool.candidate_values['restler_fuzzable_string'].values
        for _ in range(num_mutations):
            value_to_mutate = random.choice(candidate_values)
        #TODO add weight to every seed in dict instead of random
            new_value = self.mutate_value(value_to_mutate)
            candidate_pool.candidate_values['restler_fuzzable_string'].values.append(new_value)
        return candidate_pool


# mutator=dict_mutator()
# input_dict = ['Hi','!','my','best','friend']
# mutated_dict=mutator.mutated_dict(input_dict, num_mutations=10)
# print(mutated_dict)

    

