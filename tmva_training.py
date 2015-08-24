import pickle
import ROOT
from ROOT import TMVA
from optparse import OptionParser
TMVA_tools = TMVA.Tools.Instance()

training_vars = ['l1_pt', 'pthiggs','svfitMass', 'visMass', 'mt', 'pZetaDisc', 'nJets', 'jet1_pt', 'l2_pt', 'l1_mass', 'diTau_pt', 'pfmet', 'deltaRL1L2', 'deltaPhiL1MET', 'deltaPhiL2MET', 'diTau_eta', 'pZetaMET']
vbf_vars = ['abs(VBF_deta)', 'abs(VBF_hdijetphi)', 'VBF_mjj', 'VBF_jdphi', 'VBF_ptvis']
# each fold: name, (mod for training, mod for test)
folds = [('fold0', (0, 1)), ('fold1', (1, 0))]

def prepare_trees(factory, sample_dict, weight):
    sumSignalTrain = 0
    sumSignalTest = 0

    factory.SetWeightExpression('weight')

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

def prepare_trees_multiclass(factory, sample_dict, weight):
    sumTrain = 0
    sumTest = 0

    for name, comp in sample_dict.items():   
        if 'data' in name:
            continue    
        class_name = 'rest' 
        if '125' in name:
            class_name = 'signal'
        elif 'Ztt' in name:
            class_name = 'ztt'

        print 'Adding signal tree', name
        if comp['tree0'].GetEntries():
            sumTrain += comp['tree0'].GetEntries()
            factory.AddTree(comp['tree0'], class_name, weight, ROOT.TCut(''), TMVA.Types.kTraining)
        if comp['tree1'].GetEntries():
            sumTest += comp['tree1'].GetEntries()
            factory.AddTree(comp['tree1'], class_name, weight, ROOT.TCut(''), TMVA.Types.kTesting)

    factory.SetWeightExpression('weight', 'signal')
    factory.SetWeightExpression('weight', 'ztt')
    factory.SetWeightExpression('weight', 'rest')

    print 'n(train)', sumTrain
    print 'n(test)', sumTest

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
    parser.add_option("-m", "--multiclass", 
                      dest="multiclass", 
                      help="Use multiclass training",
                      action="store_true",
                      default=False)
    
    (options,args) = parser.parse_args()

    sample_dict = pickle.load(open('TMVA_inputs/sample_dict.pkl', 'rb'))

    # print sample_dict
    if options.vbf:
        training_vars += vbf_vars


    sel_onejet = sample_dict['HiggsVBF125']['sel_onejet']
    sel_vbf = sample_dict['HiggsVBF125']['sel_vbf']

    full_sel = sel_vbf if options.vbf else sel_onejet

    full_sel += '&& mt>=0.'

    full_sel = full_sel.replace('mt<30', 'mt<50')

    print 'Using selection', full_sel

    print 'Reading trees'    
    f_name = 'TMVA_training_vbf.root' if options.vbf else 'TMVA_training_onejet.root'



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
            "TMVAMulticlass" if options.multiclass else "TMVAClassification", 
            outFile, 
            "!V:!Silent:Color:DrawProgressBar:Transformations=I" ) 

        for var in training_vars:
            factory.AddVariable(var, 'F') # add float variable

        if options.multiclass:
            prepare_trees_multiclass(factory, sample_dict, weight)
        else:
            prepare_trees(factory, sample_dict, weight)

        # import pdb; pdb.set_trace()

        postfix = '_vbf_' if options.vbf else '_'
        if options.multiclass:
            postfix += '_multiclass'
        postfix += fold_name

        # factory.BookMethod(TMVA.Types.kBDT, "BDTG", "!H:!V:NTrees=500::BoostType=Grad:Shrinkage=0.05:UseBaggedBoost:GradBaggingFraction=0.9:nCuts=500:MaxDepth=5:MinNodeSize=0.1" )
        factory.BookMethod("BDT", "BDTG"+postfix, "!H:!V:NTrees=500::BoostType=Grad:Shrinkage=0.03:GradBaggingFraction=1.0:nCuts=500:MaxDepth=5:MinNodeSize=0.1:UseBaggedBoost" )
        factory.BookMethod("BDT", "BDTG4"+postfix, "!H:!V:NTrees=500::BoostType=Grad:Shrinkage=0.04:nCuts=1000:MaxDepth=5:MinNodeSize=0.01" )
        # factory.BookMethod("Fisher", "Fisher"+postfix, "!H:!V:Fisher:CreateMVAPdfs:PDFInterpolMVAPdf=Spline2:NbinsMVAPdf=50:NsmoothMVAPdf=10")
        factory.BookMethod("BDT", "BDTG6", "!H:!V:NTrees=1000::BoostType=Grad:Shrinkage=0.01:GradBaggingFraction=0.5:nCuts=1000:MaxDepth=6:MinNodeSize=0.01:UseBaggedBoost" )
        # factory.BookMethod("BDT", "BDTG7", "!H:!V:NTrees=500::BoostType=Grad:Shrinkage=0.03:GradBaggingFraction=0.5:nCuts=500:MaxDepth=7:MinNodeSize=0.1:UseBaggedBoost" )
        #:MinNodeSize=0.1:UseBaggedBoost

        factory.TrainAllMethods()
        factory.TestAllMethods()
        factory.EvaluateAllMethods()
