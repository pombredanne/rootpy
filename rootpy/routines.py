import string
import ROOT
import array
import math
import random
from plotting import Graph
from ntuple import Cut
from style import *
from ROOT import gROOT, gStyle, gPad, TGraph
import os
import sys
import uuid
import operator

currentStyle = None

def readline(file, cont=None):

    line = file.readline()
    if cont != None:
        while line.strip().endswith(cont):
            line = " ".join([line.strip()[:-1*len(cont)], file.readline()])
    return line

def readlines(file, cont=None):
    
    lines = []
    line = readline(file, cont)
    while line != '':
        lines.append(line)
        line = readline(file, cont)
    return lines

def getTrees(inputFile):

    return getObjects(inputFile, "TTree")

def getTreeNames(inputFile):

    return getObjectNames(inputFile, "TTree")

def getGraphs(inputFile):
    
    return getObjects(inputFile, "TGraph")
    
def getHistos(inputFile):

    return getObjects(inputFile, "TH1D")

def getObjects(inputFile, className=""):
    
    keys = inputFile.GetListOfKeys()
    objects = []
    for key in keys:
        if className=="" or key.GetClassName() == className:
            objects.append(inputFile.Get(key.GetName()))
    return objects

def getObjectNames(inputFile, className):
    
    keys = inputFile.GetListOfKeys()
    names = []
    for key in keys:
        if key.GetClassName() == className:
            names.append(key.GetName())
    return names

def getNumEntries(trees,cuts=None,weighted=True,verbose=False):
   
    if type(trees) is not list:
        trees = [trees]
    if weighted:
        if verbose: print "Retrieving the weighted number of entries in:"
    else:
        if verbose: print "Retrieving the unweighted number of entries in:"
    wentries = 0.
    if cuts != None:
        if not cuts.empty():
            if verbose: print "Using cuts: %s"%str(cuts)
            for tree in trees:
                weight = tree.GetWeight()
                entries = tree.GetEntries(str(cuts))
                if verbose: print "%s\t%e\t%i"%(tree.GetName(),weight,entries)
                if weighted:
                    wentries += weight*entries
                else:
                    wentries += entries
            return wentries
    for tree in trees:
        weight = tree.GetWeight()
        entries = tree.GetEntries()
        if verbose: print "%s\t%e\t%i"%(tree.GetName(),weight,entries)
        if weighted:
            wentries += weight*entries
        else:
            wentries += entries
    return wentries

def makeLabel(x,y,text,textsize=-1):

    label = ROOT.TLatex(x,y,text)
    label.SetNDC()
    if textsize > 0:
        label.SetTextSize(textsize)
    return label

def drawObject(pad,object,options=""):

    pad.cd()
    object.Draw(options)
    pad.Modified()
    pad.Update()
    hold_pointers_to_implicit_members(pad)

def getTreeMaximum(trees,branchName):

    if type(trees) is not list:
        trees = [trees]
    max = -1E300
    for tree in trees:
        treeMax = tree.GetMaximum(branchName)
        if treeMax > max:
            max = treeMax
    return max 

def getTreeMinimum(trees,branchName):
    
    if type(trees) is not list:
        trees = [trees]
    min = -1E300
    for tree in trees:
        treeMin = tree.GetMinimum(branchName)
        if treeMin > min:
            min = treeMin
    return min

def drawTrees(trees,hist,expression,cuts=None,weighted=True,verbose=False):
   
    if type(trees) is not list:
        trees = [trees]
    temp_weight = 1. 
    if verbose:
        print ""
        print "Drawing the following trees onto %s:"%hist.GetName()
        print "Initial integral: %f"%hist.Integral()
    if cuts != None:
        if not cuts.empty():
            if verbose: print "cuts applied: %s"%str(cuts)
            for tree in trees:
                if verbose: print tree.GetName()
                if not weighted:
                    temp_weight = tree.GetWeight()
                    tree.SetWeight(1.)
                tree.Draw("%s>>+%s"%(expression,hist.GetName()),str(cuts))
                if not weighted:
                    tree.SetWeight(temp_weight)
            if verbose:
                print "Final integral: %f"%hist.Integral()
            return
    for tree in trees:
        if verbose: print tree.GetName()
        if not weighted:
            temp_weight = tree.GetWeight()
            tree.SetWeight(1.)
        tree.Draw("%s>>+%s"%(expression,hist.GetName()))
        if not weighted:
            tree.SetWeight(temp_weight)
    if verbose:
        print "Final integral: %f"%hist.Integral()

def closest(target, collection):

    return collection.index((min((abs(target - i), i) for i in collection)[1]))

def round_to_n(x, n):

    if n < 1:
        raise ValueError("number of significant digits must be >= 1")
    return "%.*g" % (n, x)

def drawLogGraphs(pad,graphs,title,xtitle,ytitle,legend=None,legendheight=1.,label=None,format="png"):
    
    pad.cd()
    pad.SetLogy()
    #if format not in ("pdf","eps"):
    #pad.SetGrid()
    
    if not legend:
        legend,legendheight = getLegend(len(graphs),pad)
    #legend.SetEntrySeparation(0.01)
    
    xmax = -1E20
    xmin = 1E20
    ymax = -1E20
    ymin = 1E20
    for graph in graphs:
        txmax = graph.xMax()
        txmin = graph.xMin()
        tymax = graph.yMax()
        tymin = graph.yMin()
        if txmax > xmax:
            xmax = txmax
        if txmin < xmin:
            xmin = txmin
        if tymax > ymax:
            ymax = tymax
        if tymin < ymin:
            ymin = tymin
        
    for index,graph in enumerate(graphs):
        legend.AddEntry(graph,graph.GetTitle(),"P")
        graph.SetMarkerSize(1.5)
        if index==0:
            graph.SetTitle(title)
            graph.GetXaxis().SetLimits(xmin,xmax)
            graph.GetXaxis().SetRangeUser(xmin,xmax)
            graph.GetXaxis().SetTitle(xtitle)
            graph.GetYaxis().SetLimits(ymin,ymax)
            graph.GetYaxis().SetRangeUser(ymin,ymax)
            graph.GetYaxis().SetTitle(ytitle)
            graph.Draw("AP")
        else:
            graph.Draw("P SAME")
    
    legend.Draw()
    if label:
        label.Draw()
    pad.Modified()
    pad.Update()
    for item in pad.GetListOfPrimitives():
        if isinstance(item,ROOT.TPaveText):
            text = item.GetLine(0)
            text.SetTextFont(63)
            text.SetTextSizePixels(20)
    _hold_pointers_to_implicit_members(pad)

# scales
class AxisScales:
    LINEAR = 0
    LOG = 1

#normalization modes
class NormModes:
    NONE = 0
    MAX = 1
    UNIT = 2

def draw(
        hists
        pad = None,
        title = None,
        axislabels = None,
        legend = None,
        textlabels = None,
        xscale = AxisScales.LINEAR,
        yscale = AxisScales.LINEAR,
        minimum = None,
        maximum = None,
        use_global_margins=True
    ):
    
    if type(hists) is not list:
        hists = [hists]

    hists = [hist.Clone() for hist in hists]
    
    if axislabels:
        if type(axislabels) is not list:
            axislabels = [axislabels]
    
    if textlabels:
        if type(textlabels) is not list:
            textlabels = [textlabels]

    if not pad:
        pad = ROOT.TCanvas(uuid.uuid4().hex,uuid.uuid4().hex,0,0,800,600)
    
    pad.cd()

    if yscale = AxisScales.LOG:
        pad.SetLogy(True)
    else:
        pad.SetLogy(False)
    if xscale == AxisScales.LOG:
        pad.SetLogx(True)
    else:
        pad.SetLogx(False)
    
    if use_global_margins:
        pad.SetTopMargin(ROOT.gStyle.GetPadTopMargin())
        pad.SetRightMargin(ROOT.gStyle.GetPadRightMargin())
        pad.SetBottomMargin(ROOT.gStyle.GetPadBottomMargin())
        pad.SetLeftMargin(ROOT.gStyle.GetPadLeftMargin())

    if title:
        pad.SetTopMargin(0.1)

    for hist in hists:
        if "colz" in hist.format.lower():
            if not title:
                pad.SetTopMargin(0.06)
            pad.SetRightMargin(0.13)
            break

    if not legend:
        legend = Legend(len(histos),pad)
    
    for hist in histos:
        if normHist and hist != normHist:
            if hist.Integral()>0:
                hist.Scale(normHist.Integral()/hist.Integral())
        elif normalized.upper() == "MAX":
            if hist.GetMaximum()>0:
                hist.Scale(1./hist.GetMaximum())
        elif normalized.upper() == "UNIT":
            if hist.Integral()>0:
                hist.Scale(1./float(hist.Integral()))
    
    max = None  # negative infinity
    min = ()    # positive infinity
    for hist in histos:
        lmax = hist.GetMaximum(includeError=True)
        lmin = hist.GetMinimum(includeError=True)
        if lmax > max:
            max = lmax
        if lmin < min and not (yscale=="log" and lmin <= 0.):
            min = lmin

    if myMax != None:
        if myMax > max:
            max = myMax
    if myMin != None:
        if myMin < min:
            min = myMin
    
    axesDrawn = False
    if legend:
        plotheight = 1 - pad.GetTopMargin() - pad.GetBottomMargin()
        legendheight = legend.Height() + padding
        padding = 0.05
        if yscale == "linear":
            max = (max - (min * legendheight / plotheight)) / (1. - (legendheight / plotheight))
        else: # log
            if max <= 0.:
                raise ValueError("Attempted to plot log scale where max<=0: %f"%max)
            if min <= 0.:
                raise ValueError("Attempted to plot log scale where min<=0: %f"%min)
            max = 10.**((math.log10(max) - (math.log10(min) * legendheight / plotheight)) / (1. - (legendheight / plotheight)))
    else:
        max += (max - min)*.1

    if min > 0 and min - (max - min)*.1 < 0:
        min = 0. 
    
    for index,hist in enumerate(hists):
       
        if legend and hist.inlegend:
            legend.AddEntry(hist,hist.GetTitle().replace("_"," "),hist.legend) 
        drawOptions = []
        if index == 0 or not axesDrawn:
            hist.SetTitle(title)
            hist.GetXaxis().SetTitle(axisTitles[0])
            hist.GetYaxis().SetTitle(ylabel)
            if max > min and len(axisTitles)==1:
                hist.GetYaxis().SetLimits(min,max)
                hist.GetYaxis().SetRangeUser(min,max)
            if hist.intMode:
                hist.GetXaxis().SetNdivisions(hist.GetXaxis().GetNbins(),True)
            if len(axisTitles) in [2,3]:
                hist.GetYaxis().SetTitle(axisTitles[1])
                if len(axisTitles) == 3:
                    hist.GetZaxis().SetTitle(axisTitles[2])
                    hist.GetZaxis().SetTitleOffset(1.8)
        else:
            hist.SetTitle("")
            drawOptions.append("same")
        if hist.visible:
            axesDrawn = True
        hist.Draw(*drawOptions)
    
    if stackedhistos:
        stackedHist = ROOT.THStack("stack","stack")
        for hist in stackedhistos:
            if legend and showLegend and hist.inlegend:
                legend.AddEntry(hist,hist.GetTitle().replace("_"," "),hist.legend) 
            stackedHist.Add(hist)
        stackedHist.Draw()

    if legend:
        legend.Draw()

    for label in textlabels:
        label.Draw()

    pad.Modified()
    pad.Update()
    for item in pad.GetListOfPrimitives():
        if isinstance(item,ROOT.TPaveText):
            text = item.GetLine(0)
            text.SetTextFont(63)
            text.SetTextSizePixels(20)
    _hold_pointers_to_implicit_members(pad)
    return pad

def save_pad(pad,filename=None,format="png",dir=None):
    
    if not filename:
        filename = pad.GetName() #To Fix
    for c in string.punctuation:
        filename = filename.replace(c,'-')
    filename = filename.strip().replace(' ','-')
    
    if dir:
        filename = dir.strip("/")+"/"+filename
    
    formats = format.split('+')
    for imageformat in formats:
        pad.Print(".".join([filename,imageformat]))

def _hold_pointers_to_implicit_members( obj ):
    
    if not hasattr(obj, '_implicit_members'):
        obj._implicit_members = []
    if hasattr(obj, 'GetListOfPrimitives'):
        for prim in obj.GetListOfPrimitives():
            if prim not in obj._implicit_members:
                obj._implicit_members.append(prim)

def ROOTlogon(batch=False,noGlobal=False,style="MINE"):

    global currentStyle
    if noGlobal:
        ROOT.TH1.AddDirectory(False) # Stupid global variables in ROOT... doing this will screw up TTree.Draw()
    if batch:
        ROOT.gROOT.SetBatch()
    ROOT.TH1.SetDefaultSumw2(True)
    #ROOT.gROOT.SetStyle("Plain")
    ROOT.TGaxis.SetMaxDigits(3)
    tstyle = getStyle(style)
    currentStyle = tstyle
    if tstyle:
        print "Using ROOT style %s"%tstyle.GetName()
        ROOT.gROOT.SetStyle(tstyle.GetName())
        ROOT.gROOT.ForceStyle()
        ROOT.gStyle.SetPalette(1)
    else:
        print "Style %s is not defined"%style
