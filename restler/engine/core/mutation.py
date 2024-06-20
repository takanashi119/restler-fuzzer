import random
import string
from engine.core.requests import GrammarRequestCollection
class dict_mutator:
    def __init__(self) -> None:
        self.seed_pool={}
    def mutate_value(self,value):
        try:
            if isinstance(value, int):
                return value + random.randint(-10, 10)
            elif isinstance(value, float):
                return value * random.uniform(0.9, 1.1)
            elif isinstance(value, str):
                if len(value):
                    mutate_mtd=0
                    
                else:
                    mutate_mtd=random.randint(0,3)
                if mutate_mtd==0:
                    random_char = random.choice(string.ascii_letters + string.digits)
                    random_position = random.randint(0, len(value))
                    modified_str = value[:random_position] + random_char + value[random_position:]
                if mutate_mtd==1:
                    random_position = random.randint(0, len(value))
                    modified_str = value[:random_position] + value[random_position+1:]
                if mutate_mtd==2:
                    random_char = random.choice(string.ascii_letters + string.digits)
                    random_position = random.randint(0, len(value))
                    modified_str = value[:random_position] + random_char + value[random_position+1:]
                    
                return modified_str        
        except:
            pass

    def mutated_dict(self,num_mutations=1):
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

    

