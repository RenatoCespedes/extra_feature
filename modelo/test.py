from tensorflow.core.framework import summary_pb2
from random import shuffle
import numpy as np
from scipy.stats import rankdata

from conf_proyecto import *
import os

def run_test(sess, model, batch_gen, data, name_group):
    
    list_batch_ce = []
    list_batch_correct = []
    
    list_pred = []
    list_label = []

    max_loop  = int(len(data) / model.batch_size)
    remaining = int(len(data) % model.batch_size)

    # Evalua los datos ( N of chunk (batch_size) + remaining( +1) )
    for test_itr in range( max_loop + 1 ):
        
        raw_encoder_inputs, raw_encoder_seq, raw_encoder_prosody, raw_label = batch_gen.get_batch(
                                        data=data,
                                        batch_size=model.batch_size,
                                        encoder_size=model.encoder_size,
                                        is_test=True,
                                        start_index= (test_itr* model.batch_size)
                                        )
        
        # prepara la data que se inserta de pc al placeholder
        input_feed = {}

        input_feed[model.encoder_inputs] = raw_encoder_inputs
        input_feed[model.encoder_seq] = raw_encoder_seq
        input_feed[model.encoder_prosody] = raw_encoder_prosody
        input_feed[model.y_labels] = raw_label
        input_feed[model.dr_prob] = 1.0             # no drop out while evaluating
    
        try:
            bpred, bloss = sess.run([model.batch_pred, model.batch_loss], input_feed)
        except:
            print("la excepción ocurre en un paso válido : " + str(test_itr))
            pass
        
        # remaining data case (last iteration)
        if test_itr == (max_loop):
            bpred = bpred[:remaining]
            bloss = bloss[:remaining]
            raw_label = raw_label[:remaining]
        
        # batch loss
        list_batch_ce.extend( bloss )
        # print(list_batch_ce)

        # batch accuracy
        list_pred.extend( np.argmax(bpred, axis=1) )
        list_label.extend( np.argmax(raw_label, axis=1) )
     

        
    with open( '../analysis/audio'+str(name_group)+'.txt', 'w' ) as f:
            f.write( ' '.join( [str(x) for x in list_pred] ) )

    with open( '../analysis/audio_label'+str(name_group)+'.txt', 'w' ) as f:
            f.write( ' '.join( [str(x) for x in list_label] ) )   
        
            
    
    list_batch_correct = [1 for x, y in zip(list_pred,list_label) if x==y]
    
    sum_batch_ce = np.sum( list_batch_ce )  
    # print('Test CE: ' + str(sum_batch_ce))
    accr = np.sum ( list_batch_correct ) / float( len(data) )
    
    value1 = summary_pb2.Summary.Value(tag="valid_loss", simple_value=sum_batch_ce)
    value2 = summary_pb2.Summary.Value(tag="valid_accuracy", simple_value=accr )
    summary = summary_pb2.Summary(value=[value1, value2])
    
    return sum_batch_ce, accr, summary, list_pred