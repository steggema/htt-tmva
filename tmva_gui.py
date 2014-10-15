import ROOT
ROOT.gROOT.LoadMacro('$ROOTSYS/tmva/test/TMVAGui.C')
ROOT.TMVAGui('TMVA_training_vbf.root')
raw_input("Press Enter to continue...")
