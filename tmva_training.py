import pickle
import ROOT
from ROOT import TMVA
from optparse import OptionParser
TMVA_tools = TMVA.Tools.Instance()

training_vars = ['l1_pt', 'pthiggs','svfitMass', 'visMass', 'mt']

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


    sel_onejet = sample_dict['HiggsVBF125']['sel_onejet']
    sel_vbf = sample_dict['HiggsVBF125']['sel_vbf']

    full_sel = sel_vbf if options.vbf else sel_onejet

    full_sel += '&& mt>=0.'

    print 'Using selection', full_sel

    print 'Reading trees'    
    f_name = 'TMVA_training_vbf.root' if options.vbf else 'TMVA_training_onejet.root'



    folds = [('fold0', (0, 1)), ('fold1', (1, 0))]

    for fold in folds:
        fold_name = fold[0]
        outFile = ROOT.TFile(f_name.replace('.root', '_'+fold_name+'.root'), 'RECREATE')
        
        for name, comp in sample_dict.items():
            fileName = 'TMVA_inputs/{n}.root'.format(n=name)

            weight = comp['weight']

            f = ROOT.TFile(fileName)
            comp['file'] = f
            
            outFile.cd()
            comp['tree'] = f.Get('H2TauTauTreeProducerTauMu').CopyTree(full_sel)
            comp['tree0'] = comp['tree'].CopyTree(full_sel+'&& abs(int(metphi*1000))%{n_folds}=={n}'.format(n_folds=len(folds), n=fold[1][0]))
            comp['tree1'] = comp['tree'].CopyTree(full_sel+'&& abs(int(metphi*1000))%{n_folds}=={n}'.format(n_folds=len(folds), n=fold[1][1]))

        print 'Booking TMVA'


        factory = TMVA.Factory(
            "TMVAClassification", 
            outFile, 
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
