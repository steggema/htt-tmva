import pickle
import ROOT
from ROOT import TMVA
import numpy
from optparse import OptionParser
TMVA_tools = TMVA.Tools.Instance()

from tmva_training import training_vars

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
        training_vars += ['abs(VBF_deta)', 'abs(VBF_hdijetphi)', 'VBF_mjj']


   
    for name, comp in sample_dict.items():
        fileName = 'TMVA_inputs/{n}.root'.format(n=name)
        weight = comp['weight']

        f = ROOT.TFile(fileName)
        # comp['file'] = f
        
        in_tree = f.Get('H2TauTauTreeProducerTauMu')

        mva_name = 'mva_vbf' if options.vbf else 'mva_onejet'
        out_file = ROOT.TFile(fileName.replace('.root', '_{a}.root'.format(a=mva_name)), 'RECREATE')

        out_tree = ROOT.TTree(mva_name, mva_name)

        mva_val = numpy.zeros(1, dtype=float)

        out_tree.Branch(mva_name, mva_val, mva_name+'/D')

        for entry in in_tree:
            


    factory = TMVA.Factory(
        "TMVAClassification", 
        out_file, 
        "!V:!Silent:Color:DrawProgressBar:Transformations=I" ) 

    factory.SetWeightExpression('weight')

    for var in training_vars:
        factory.AddVariable(var, 'F') # add float variable


    sumSignalTrain = 0
    sumSignalTest = 0

    for name, comp in sample_dict.items():        
        if '125' in name:
            print 'Adding signal tree', name
            if comp['tree0'].GetEntries():
                sumSignalTrain += comp['tree0'].GetEntries()
                factory.AddSignalTree(comp['tree0'], weight, TMVA.Types.kTraining)
            if comp['tree1'].GetEntries():
                sumSignalTest += comp['tree1'].GetEntries()
                factory.AddSignalTree(comp['tree1'], weight, TMVA.Types.kTesting)
        elif not 'data' in name:
            print 'Adding background tree', name
            if comp['tree0'].GetEntries():
                factory.AddBackgroundTree(comp['tree0'], weight, TMVA.Types.kTraining)
            if comp['tree1'].GetEntries():
                factory.AddBackgroundTree(comp['tree1'], weight, TMVA.Types.kTesting)

    print 'Signal n(train)', sumSignalTrain
    print 'Signal n(test)', sumSignalTest
    # import pdb; pdb.set_trace()

    # factory.PrepareTrainingAndTestTree( ROOT.TCut(full_sel), ROOT.TCut(full_sel),
    #                                     "nTrain_Signal=0:nTest_Background=0:SplitMode=Block:NormMode=NumEvents:!V" )
    postfix = '_vbf_' if options.vbf else '_'
    postfix += fold_name

    # factory.BookMethod(TMVA.Types.kBDT, "BDTG", "!H:!V:NTrees=500::BoostType=Grad:Shrinkage=0.05:UseBaggedBoost:GradBaggingFraction=0.9:nCuts=500:MaxDepth=5:MinNodeSize=0.1" )
    factory.BookMethod("BDT", "BDTG"+postfix, "!H:!V:NTrees=500::BoostType=Grad:Shrinkage=0.03:GradBaggingFraction=1.0:nCuts=500:MaxDepth=5:MinNodeSize=0.1:UseBaggedBoost" )
    factory.BookMethod("BDT", "BDTG4"+postfix, "!H:!V:NTrees=500::BoostType=Grad:Shrinkage=0.03:GradBaggingFraction=0.5:nCuts=500:MaxDepth=5:MinNodeSize=0.1:UseBaggedBoost" )
    # factory.BookMethod("BDT", "BDTG6", "!H:!V:NTrees=500::BoostType=Grad:Shrinkage=0.03:GradBaggingFraction=0.5:nCuts=500:MaxDepth=6:MinNodeSize=0.1:UseBaggedBoost" )
    # factory.BookMethod("BDT", "BDTG7", "!H:!V:NTrees=500::BoostType=Grad:Shrinkage=0.03:GradBaggingFraction=0.5:nCuts=500:MaxDepth=7:MinNodeSize=0.1:UseBaggedBoost" )
    #:MinNodeSize=0.1:UseBaggedBoost

    factory.TrainAllMethods()
    factory.TestAllMethods()
    factory.EvaluateAllMethods()
