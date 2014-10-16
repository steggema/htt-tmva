import ROOT
ROOT.gROOT.LoadMacro('$ROOTSYS/tmva/test/TMVAGui.C')
# ROOT.TMVAGui('TMVA_training_vbf_fold1.root')
ROOT.TMVAGui('TMVA_training_onejet_fold1.root')
raw_input("Press Enter to continue...")
