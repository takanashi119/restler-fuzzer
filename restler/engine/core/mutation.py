import random
import string

import engine.core.sequences as sequences
import engine.core.requests as requests
import engine.primitives as primitives
import engine.transport_layer.messaging as messaging
from engine.core.requests import GrammarRequestCollection
from engine.transport_layer.response import *
from engine.bug_bucketing import BugBuckets
from utils.logger import raw_network_logging as RAW_LOGGING
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
        
    def apply_mutation_dict(self,seq:sequences.Sequence,num_mutations=1):
        #Ensure the last request has fuzzable value 
        self.seq = seq
        self.last_req = seq.last_request
        self.candidate_pool = GrammarRequestCollection().candidate_values_pool
        fuzzable_block=self.get_fuzzable()
        if (len(fuzzable_block)==0):
            return 0

        
        self.execute_start_of_sequence(seq)
        candidate_pool=GrammarRequestCollection().candidate_values_pool
        candidate_values=candidate_pool.candidate_values['restler_fuzzable_string'].values
        for _ in range(num_mutations):
            value_to_mutate = random.choice(candidate_values)
        #TODO add weight to every seed in dict instead of random
            new_value = self.mutate_value(value_to_mutate)
            candidate_pool.candidate_values['restler_fuzzable_string'].values.append(new_value)
        return candidate_pool
    def get_fuzzable(self):
        fuzzable_block=[]
        for request_block in self.last_req.definition:
            primitive_type = request_block[0]
            if primitive_type in [primitives.FUZZABLE_STRING,
                                  primitives.FUZZABLE_INT]:
            #TODO:add more fuzzable type
                fuzzable_block.append(request_block)
        return fuzzable_block
    def execute_start_of_sequence(self,seq:sequences.Sequence):
        if len(seq.requests) > 1:
            RAW_LOGGING("Re-rendering and sending start of sequence")
        new_seq = sequences.Sequence([])
        for request in seq.requests[:-1]:
            new_seq = new_seq + sequences.Sequence(request)
            response, _ = self.render_and_send_data(new_seq, request)
            # Check to make sure a bug wasn't uncovered while executing the sequence
            if response and response.has_bug_code():
                self._print_suspect_sequence(new_seq, response)
                BugBuckets.Instance().update_bug_buckets(new_seq, response.status_code, origin=self.__class__.__name__)
        return 0
    def render_and_send_data(self, seq, request:requests.Request):
        rendered_data, parser, tracked_parameters, updated_writer_variables, replay_blocks =\
             request.render_current(self.candidate_pool)
        rendered_data = seq.resolve_dependencies(rendered_data)
    def render(self):
        return 
   
# mutator=dict_mutator()
# input_dict = ['Hi','!','my','best','friend']
# mutated_dict=mutator.mutated_dict(input_dict, num_mutations=10)
# print(mutated_dict)

    

