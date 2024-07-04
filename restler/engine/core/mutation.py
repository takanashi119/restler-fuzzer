import random
import string
import threading
import copy
import engine.core.sequences as sequences
import engine.core.requests as requests
import engine.primitives as primitives
import engine.dependencies as dependencies
import engine.transport_layer.messaging as messaging
import engine.core.async_request_utilities as async_request_utilities
import engine.core.request_utilities as request_utilities
from engine.core.fuzzing_monitor import Monitor
from utils.logging.trace_db import SequenceTracker
from engine.core.requests import GrammarRequestCollection
from engine.transport_layer.response import *
from engine.bug_bucketing import BugBuckets
from utils.logger import raw_network_logging as RAW_LOGGING

threadLocal = threading.local()
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
    def get_mutated_blocks(self,fuzzable_blocks):
        #No need to mutate the same value 
        mutated_blocks={}
        for idx,block in fuzzable_blocks.items():
            mutated_value = self.mutate_value(block[1])
            mutated_blocks[idx]=block[:1]+(mutated_value,)+block[2:]
        return mutated_blocks
    


    def apply_mutation_dict(self,seq:sequences.Sequence,max_dict=300):
        #Ensure the last request has fuzzable value 
        if (len( GrammarRequestCollection().candidate_values_pool.\
                candidate_values['restler_fuzzable_string'].values)>=max_dict):
            return 0
        last_req = seq.last_request
        definition=last_req.definition
        self.candidate_pool = GrammarRequestCollection().candidate_values_pool
        fuzzable_blocks=self.get_fuzzable(last_req)
        if (len(fuzzable_blocks)==0):
            return 0

        #execute current seq until the last one
        #and referered the cheker
        start_reqs=self.execute_start_of_sequence(seq)
        
        mutated_blocks=self.get_mutated_blocks(fuzzable_blocks)
        new_last_req=copy.deepcopy(last_req)
        for idx,block in mutated_blocks.items():
            new_last_req.definition[idx]=block
            new_seq=start_reqs+sequences.Sequence(new_last_req)
            response =self.render_and_send_by_definition(new_seq,new_last_req) 
            if response.has_valid_code():
                GrammarRequestCollection().candidate_values_pool.\
                    candidate_values['restler_fuzzable_string'].values.append(block[1])
                candidate_pool = GrammarRequestCollection().candidate_values_pool
            elif response.has_bug_code():
                print('find bug when redering a mutated request')
        return 
    


    def get_fuzzable(self,last_req):
        #return idx and fuzzable blocks
        fuzzable_blocks={}
        idx=-1
        for request_block in last_req.definition:
            idx=idx+1
            primitive_type = request_block[0]
            if primitive_type in [primitives.FUZZABLE_STRING,
                                  primitives.FUZZABLE_INT,
                                  primitives.CUSTOM_PAYLOAD]:
            #TODO:add more fuzzable type
                fuzzable_blocks[idx]=request_block
        return fuzzable_blocks
    def execute_start_of_sequence(self,seq:sequences.Sequence):
        new_seq = sequences.Sequence([])
        for request in seq.requests[:-1]:
            new_seq = new_seq + sequences.Sequence(request)
            response, _ = self.render_and_send_data(new_seq, request)
            # Check to make sure a bug wasn't uncovered while executing the sequence
            if response and response.has_bug_code():

                print("find bug while re-rendering")
                # if response and response.status_code:
                #     status_code = self._format_status_code(response.status_code)
                #     self._checker_log.checker_print(f"\nSuspect sequence: {status_code}")
                # for req in seq:
                #     self._checker_log.checker_print(f"{req.method} {req.endpoint}")
        return new_seq
    def render_and_send_by_definition(self,seq,last_req):
        response=[]
        response_to_parse=[]
        definition=last_req.definition
        rendered_values = []
        for block in definition:
            primitive_type = block[0]
            if primitive_type == primitives.REFRESHABLE_AUTHENTICATION_TOKEN:
                value = primitives.restler_refreshable_authentication_token
            elif primitive_type in [primitives.FUZZABLE_STRING,
                                    primitives.CUSTOM_PAYLOAD]:
                value = f'"{block[1]}"'
            else :
                value = block[1]
            rendered_values.append(value)
        
        rendered_values = request_utilities.resolve_dynamic_primitives(rendered_values, self.candidate_pool)

        rendered_data="".join(rendered_values)

        parser = None
        rendered_data = seq.resolve_dependencies(rendered_data)
        if bool(last_req.metadata) and 'post_send' in last_req.metadata\
            and 'parser' in last_req.metadata['post_send']:
                parser = last_req.metadata['post_send']['parser']
        
        response = self.send_request(parser,rendered_data)
        return response


    def render_and_send_data(self, seq, request:requests.Request):
        response=[]
        response_to_parse=[]
        rendered_data, parser, tracked_parameters, updated_writer_variables, replay_blocks =\
             request.render_current(self.candidate_pool)                                         
        rendered_data = seq.resolve_dependencies(rendered_data)
    
        SequenceTracker.initialize_sequence_trace(combination_id=seq.combination_id,
                                            tags={'hex_definition': seq.hex_definition})
        SequenceTracker.initialize_request_trace(combination_id=seq.combination_id,
                                                 request_id=request.hex_definition,
                                                 replay_blocks=replay_blocks)
        response = self.send_request(parser, rendered_data)
    
        return response,response_to_parse
    def send_request(self, parser, rendered_data):
        from engine.transport_layer.messaging import HttpSock
        try:
            checkers_sock = threadLocal.checkers_sock
        except AttributeError:
            # Socket not yet initialized.
            threadLocal.checkers_sock = HttpSock(Settings().connection_settings)
            checkers_sock = threadLocal.checkers_sock

        response = request_utilities.send_request_data(
            rendered_data, req_timeout_sec=Settings().max_request_execution_time,
            reconnect=Settings().reconnect_on_every_request,
            http_sock=checkers_sock
        )

        Monitor().increment_requests_count(self.__class__.__name__)
        return response
# mutator=dict_mutator()
# input_dict = ['Hi','!','my','best','friend']
# mutated_dict=mutator.mutated_dict(input_dict, num_mutations=10)
# print(mutated_dict)

    

