#!/usr/bin/env python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser

from krnnt.keras_models import BEST, ExperimentParameters
from krnnt.new import UnalignedSimpleEvaluator
from krnnt.tagger_exps import RunFolds2, KerasData, RunExperiment


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('corpus_path', help='path to corpus')
    parser.add_argument('-p', '--preanalyzed', action='store_false',
                        default=True, dest='reanalyzed',
                        help='training data have not been reanalyzed')
    parser.add_argument('-c', '--cv', action='store_true',
                        default=False, dest='cv',
                        help='run 10-fold cross-validation')
    parser.add_argument('-t', '--train_ratio',
                        default=1.0, dest='train_ratio', type=float,
                        help='percentage of data for training')
    parser.add_argument('-d', '--dev_ratio',
                        default=0.0, dest='dev_ratio', type=float,
                        help='percentage of training data for development')
    parser.add_argument('-e', '--epochs',
                        default=100, dest='epochs', type=int,
                        help='number of epochs')
    parser.add_argument('--patience',
                        default=10, dest='patience', type=int,
                        help='patience')
    parser.add_argument('--maca_config',
                        default='morfeusz-nkjp-official',
                        help='Maca config')
    parser.add_argument('-g', '--debug', action='store_true', dest='debug_mode')  # TODO
    parser.add_argument('--hash', action='store', default=None, dest='hash')
    parser.add_argument('--reproducible', action='store_true', default=False, help='set seeds')
    parser.add_argument('-f', '--fold', default=None, dest='fold')
    args = parser.parse_args()

    if args.reproducible:
        from numpy.random import seed
        seed(1337)
        import random as rn
        rn.seed(1337)
        import tensorflow as tf
        session_conf = tf.ConfigProto(intra_op_parallelism_threads=1,
                                      inter_op_parallelism_threads=1)
        from keras import backend as K
        tf.set_random_seed(1337)
        sess = tf.Session(graph=tf.get_default_graph(), config=session_conf)
        K.set_session(sess)

    pref = {'nb_epoch': 100, 'batch_size': 256,
            'internal_neurons': 256, 'feature_name': 'tags4e3', 'label_name': 'label',
            'evaluator': UnalignedSimpleEvaluator, 'patience': 10,
            'weight_path': 'weights.hdf5', 'samples_per_epoch': 10000, 'keras_model_class': BEST,
            'corpus_path': 'data/train-reanalyzed.spickle', 'reanalyze': True, 'train_data_ratio': 0.9,
            'dev_data_ratio': 0.1}

    pref['reanalyze'] = args.reanalyzed
    pref['train_data_ratio'] = float(args.train_ratio)
    pref['dev_data_ratio'] = float(args.dev_ratio)
    pref['nb_epoch'] = int(args.epochs)
    pref['corpus_path'] = args.corpus_path
    pref['patience'] = args.patience
    pref['maca_config'] = args.maca_config
    if args.hash is not None:
        pref['h'] = args.hash
    if args.fold is not None:
        pref['fold'] = int(args.fold)

    keras_model_class = pref['keras_model_class']

    if args.cv:
        rf = RunFolds2(keras_model_class, pref)
        rf.run()
    else:
        parameters = ExperimentParameters(pref)
        km = keras_model_class(parameters)

        print('Model will be saved under: %s.final' % parameters.pref['weight_path'])
        print('Lemmatisation model will be saved under: %s' % parameters.pref['lemmatisation_path'])

        kd = KerasData(pref['corpus_path'], pref['reanalyze'])
        re = RunExperiment(kd, km)
        re.run()

        print('Model is saved under: %s' % parameters.pref['weight_path'])
        print('Lemmatisation model is saved under: %s' % parameters.pref['lemmatisation_path'])
        if pref['reanalyze']:
            print('Dictionary is saved under: %s' % parameters.pref[
                'corpus_path'] + '_FormatData2_PreprocessData_UniqueFeaturesValues')
        else:
            print('Dictionary is saved under: %s' % parameters.pref[
                'corpus_path'] + '_FormatDataPreAnalyzed_PreprocessData_UniqueFeaturesValues')
