import pickle
import ROOT
from ROOT import TMVA
import numpy
from optparse import OptionParser
TMVA_tools = TMVA.Tools.Instance()

from tmva_training import training_vars
from tmva_training import vbf_vars
from tmva_training import folds

if __name__ == '__main__':
    parser = OptionParser()
    parser.usage = '''
    %prog 

    '''
    parser.add_option("-b", "--batch", 
                      dest="batch", 
                      help="Set batch mode.",
                      action="store_true",
                      default=False)
    parser.add_option("-v", "--vbf", 
                      dest="vbf", 
                      help="Use VBF training (default: 1-jet training)",
                      action="store_true",
                      default=False)

    
    (options,args) = parser.parse_args()

    sample_dict = pickle.load(open('TMVA_inputs/sample_dict.pkl', 'rb'))

    # print sample_dict
    if options.vbf:
        training_vars += vbf_vars

    reader = ROOT.TMVA.Reader("!Color:!Silent")

    var_arrays = []
    for var in training_vars:
        var_arrays.append(numpy.zeros(1, dtype=numpy.dtype('Float32') ))
        reader.AddVariable(var, var_arrays[-1])


    # Book MVA methods
    for fold in folds:
        mva_name = 'BDTG_'
        if options.vbf:
            mva_name += 'vbf_'
        mva_name += fold[0]
        reader.BookMVA(mva_name, 'weights/TMVAClassification_{n}.weights.xml'.format(n=mva_name))

    for name, comp in sample_dict.items():
        print 'Sample:', name

        fileName = 'TMVA_inputs/{n}.root'.format(n=name)
        weight = comp['weight']

        f = ROOT.TFile(fileName)
        
        in_tree = f.Get('H2TauTauTreeProducerTauMu')

        mva_name = 'mva_vbf' if options.vbf else 'mva_onejet'
        out_file = ROOT.TFile(fileName.replace('.root', '_{a}.root'.format(a=mva_name)), 'RECREATE')

        out_tree = ROOT.TTree(mva_name, mva_name)

        mva_val = numpy.zeros(1, dtype=float)

        out_tree.Branch(mva_name, mva_val, mva_name+'/D')

        mva_name = 'BDTG_'
        if options.vbf:
            mva_name += 'vbf_'

        for event in in_tree:
            met_phi1000 = abs(int(event.metphi * 1000.))
            for var, ar in zip(training_vars, var_arrays):
                if var.startswith('abs'):
                    ar[0] = abs(getattr(event, var.strip('abs(').strip(')')))
                else:
                    ar[0] = getattr(event, var)
            for fold in folds:
                if met_phi1000%len(folds) == fold[1][1]:
                    mva_val[0] = reader.EvaluateMVA(mva_name+folds[0][0])
            out_tree.Fill()

        out_tree.AddFriend(in_tree)

        out_file.Write()
        out_file.Close()

