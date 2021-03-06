#!/usr/bin/env python

import math
import ROOT
from ROOT import THStack, TLatex
from ROOT import TCanvas, TPad, TLegend
from UserCode.TopMassSecVtx.CMS_lumi import *
from UserCode.TopMassSecVtx.rounding import *

class Plot:
    """
    A wrapper to store data and MC histograms for comparison
    """

    def __init__(self,name):
        self.name = name
        self.mc = []
        self.dataH = None
        self.data = None
        self.garbageList = []

    def info(self):
        print self.name
        print len(self.mc),' mc processes', ' data=', self.data

    def add(self, h, title, color, isData):
        self.garbageList.append(h)
        h.SetTitle(title)

        if "GeV" in h.GetXaxis().GetTitle():
            h.GetYaxis().SetTitle("Events / %3.1f GeV" % h.GetBinWidth(1))
        else:
            h.GetYaxis().SetTitle("Events / %3.1f" % h.GetBinWidth(1))

        if isData:
            h.SetMarkerStyle(20)
            h.SetMarkerColor(color)
            h.SetLineColor(color)
            h.SetLineWidth(2)
            h.SetFillColor(0)
            h.SetFillStyle(0)
            self.dataH=h
            self.data=convertToPoissonErrorGr(h)
        else:
            h.SetMarkerStyle(1)
            h.SetMarkerColor(color)
            h.SetLineColor(color)
            h.SetLineWidth(1)
            h.SetFillColor(color)
            h.SetFillStyle(1001)
            self.mc.append(h)

    def appendTo(self,outUrl):
        #if file does not exist it is created
        outF=ROOT.TFile.Open(outUrl,'UPDATE')
        outDir=outF.mkdir(self.name)
        outDir.cd()
        for m in self.mc : 
            if m :
                m.Write()
        if self.data : 
            self.data.Write()
            self.dataH.Write()
        outF.Close()


    def reset(self):
        for o in self.garbageList: 
            try:
                o.Delete()
            except:
                pass

    def showTable(self, outDir, firstBin=1, lastBin=-1):
        if len(self.mc)==0:
            print '%s is empty' % self.name
            return

        if firstBin<1: firstBin = 1

        f = open(outDir+'/'+self.name+'.dat','w')
        f.write('------------------------------------------\n')
        f.write("Process".ljust(20),)
        f.write("Events after each cut\n")
        f.write('------------------------------------------\n')

        tot ={}
        err = {}
        f.write(' '.ljust(20),)
        try:
            for xbin in xrange(1,self.mc[0].GetXaxis().GetNbins()+1):
                pcut=self.mc[0].GetXaxis().GetBinLabel(xbin)
                f.write(pcut.ljust(40),)
                tot[xbin]=0
                err[xbin]=0
        except:
            pass
        f.write('\n')
        f.write('------------------------------------------\n')

        for h in self.mc:
            pname = h.GetTitle()
            f.write(pname.ljust(20),)

            for xbin in xrange(1,h.GetXaxis().GetNbins()+1):
                itot=h.GetBinContent(xbin)
                ierr=h.GetBinError(xbin)
                pval=' & %s'%toLatexRounded(itot,ierr)
                f.write(pval.ljust(40),)
                tot[xbin] = tot[xbin]+itot
                err[xbin] = err[xbin]+ierr*ierr
            f.write('\n')

        f.write('------------------------------------------\n')
        f.write('Total'.ljust(20),)
        for xbin in tot:
            pval=' & %s'%toLatexRounded(tot[xbin],math.sqrt(err[xbin]))
            f.write(pval.ljust(40),)
        f.write('\n')

        if self.data is None: return
        f.write('------------------------------------------\n')
        f.write('Data'.ljust(20),)
        for xbin in xrange(1,self.dataH.GetXaxis().GetNbins()+1):
            itot=self.dataH.GetBinContent(xbin)
            pval=' & %d'%itot
            f.write(pval.ljust(40))
        f.write('\n')
        f.write('------------------------------------------\n')
        f.close()


    def show(self, outDir):
        if len(self.mc)==0:
            print '%s is empty' % self.name
            return
        canvas = TCanvas('c_'+self.name,'C',600,600)
        canvas.cd()
        t1 = TPad("t1","t1", 0.0, 0.20, 1.0, 1.0)
        t1.SetBottomMargin(0)
        t1.Draw()
        t1.cd()
        self.garbageList.append(t1)

        frame = None
        # leg = TLegend(0.15,0.9,0.9,0.95)
        leg = TLegend(0.5,0.7,0.9,0.89)
        leg.SetBorderSize(0)
        leg.SetFillStyle(0)
        leg.SetTextFont(42)
        leg.SetTextSize(0.04)
        nlegCols = 0

        maxY = 1.0
        if self.data is not None:
            leg.AddEntry( self.data, self.data.GetTitle(),'p')
            frame = self.dataH.Clone('frame')
            self.garbageList.append(frame)
            maxY = self.data.GetMaximum()*1.1
            frame.Reset('ICE')

        totalMC = None
        stack = THStack('mc','mc')
        for h in self.mc:
            stack.Add(h,'hist')
            leg.AddEntry(h,h.GetTitle(),'f')
            nlegCols = nlegCols+1
            if totalMC is None:
                totalMC = h.Clone('totalmc')
                self.garbageList.append(totalMC)
                totalMC.SetDirectory(0)
            else:
                totalMC.Add(h)

        if totalMC is not None:
            maxY = max(totalMC.GetMaximum(),maxY)
            if frame is None:
                frame = totalMC.Clone('frame')
                frame.Reset('ICE')
                self.garbageList.append(frame)

        if self.data is not None: nlegCols = nlegCols+1
        if nlegCols == 0:
            print '%s is empty'%self.name
            return 

        frame.GetYaxis().SetTitleSize(0.045)
        frame.GetYaxis().SetLabelSize(0.04)
        frame.GetYaxis().SetRangeUser(0.5,1.3*maxY)
        frame.SetDirectory(0)
        frame.Draw()
        frame.GetYaxis().SetTitleOffset(1.6)
        stack.Draw('hist same')
        if self.data is not None: self.data.Draw('P same')
        # leg.SetNColumns(nlegCols)
        leg.SetNColumns(2)
        leg.Draw()

        ## Draw CMS Preliminary label
        CMS_lumi(t1,2,0)

        if totalMC is None or self.data is None:
            t1.SetPad(0,0,1,1)
            t1.SetBottomMargin(0.12)
        else:
            canvas.cd()
            t2 = TPad("t2","t2", 0.0, 0.0, 1.0, 0.2)
            self.garbageList.append(t2)
            t2.SetTopMargin(0)
            t2.SetBottomMargin(0.4)
            t2.SetGridy()
            t2.Draw()
            t2.cd()
            
            ratioframe=self.dataH.Clone('ratioframe')
            ratioframe.Draw()
            ratioframe.GetYaxis().SetRangeUser(0.62,1.36)
            #ratioframe.GetYaxis().SetRangeUser(0.36,1.64)
            ratioframe.GetYaxis().SetTitle('Data/#SigmaBkg')
            ratioframe.GetYaxis().SetNdivisions(5)
            ratioframe.GetYaxis().SetLabelSize(0.15)
            ratioframe.GetXaxis().SetLabelSize(0.15)
            ratioframe.GetYaxis().SetTitleSize(0.18)
            ratioframe.GetXaxis().SetLabelSize(0.18)
            ratioframe.GetXaxis().SetTitleSize(0.18)
            ratioframe.GetYaxis().SetTitleOffset(0.3)
            ratioframe.GetXaxis().SetTitleOffset(0.9)

            gr=ROOT.TGraphAsymmErrors()
            gr.SetName("data2bkg")
            gr.SetMarkerStyle(20)
            gr.SetMarkerColor(1)
            gr.SetLineColor(1)
            gr.SetLineWidth(2)
            bkgUncGr=ROOT.TGraphErrors()
            bkgUncGr.SetName('bkgunc')
            bkgUncGr.SetMarkerColor(920)
            bkgUncGr.SetMarkerStyle(1)
            bkgUncGr.SetLineColor(920)
            bkgUncGr.SetFillColor(920)
            bkgUncGr.SetFillStyle(3001)
            for xbin in xrange(1,self.dataH.GetXaxis().GetNbins()+1):
                x            = self.dataH.GetXaxis().GetBinCenter(xbin)
                dx           = self.dataH.GetXaxis().GetBinWidth(xbin)
                dataCts      = self.dataH.GetBinContent(xbin)
                data_err_low = self.data.GetErrorYlow(xbin-1) #get errors from the graph
                data_err_up  = self.data.GetErrorYhigh(xbin-1)
                bkgCts       = totalMC.GetBinContent(xbin);
                bkgCts_err   = totalMC.GetBinError(xbin);
                if bkgCts==0 : continue
                errLo=math.sqrt(math.pow(data_err_low*bkgCts,2) + math.pow(dataCts*bkgCts_err,2))/math.pow(bkgCts,2)
                errHi=math.sqrt(math.pow(data_err_up*bkgCts,2)  + math.pow(dataCts*bkgCts_err,2))/math.pow(bkgCts,2)
                np=gr.GetN()
                gr.SetPoint(np,x,dataCts/bkgCts)
                gr.SetPointError(np,0,0,errLo,errHi)
                bkgUncGr.SetPoint(np,x,1)
                bkgUncGr.SetPointError(np,dx,bkgCts_err/bkgCts)
            bkgUncGr.Draw('p2')
            gr.Draw('p')


        canvas.cd()
        canvas.Modified()
        canvas.Update()
        for ext in ['pdf','png'] : canvas.SaveAs(outDir+'/'+self.name+'.'+ext)
        t1.cd()
        t1.SetLogy()
        frame.GetYaxis().SetRangeUser(0.5,4*maxY)
        canvas.cd()
        for ext in ['pdf','png'] : canvas.SaveAs(outDir+'/'+self.name+'_log.'+ext)



"""
converts an histogram to a graph with Poisson error bars
"""
def convertToPoissonErrorGr(h):
    #check https://twiki.cern.ch/twiki/bin/view/CMS/PoissonErrorBars
    alpha = 1 - 0.6827;
    grpois = ROOT.TGraphAsymmErrors(h);
    for i in xrange(0,grpois.GetN()+1) :
        N = grpois.GetY()[i]
        if N<200 :
            L = 0
            if N>0 : L = ROOT.Math.gamma_quantile(alpha/2,N,1.)
            U = ROOT.Math.gamma_quantile_c(alpha/2,N+1,1)
            grpois.SetPointEYlow(i, N-L)
            grpois.SetPointEYhigh(i, U-N)
        else:
            grpois.SetPointEYlow(i, math.sqrt(N))
            grpois.SetPointEYhigh(i,math.sqrt(N))
    return grpois


"""
increments the first and the last bin to show the under- and over-flows
"""
def fixExtremities(h,addOverflow=True,addUnderflow=True):
    if addUnderflow :
        fbin  = h.GetBinContent(0) + h.GetBinContent(1)
	fbine = ROOT.TMath.Sqrt(h.GetBinError(0)*h.GetBinError(0) + h.GetBinError(1)*h.GetBinError(1))
	h.SetBinContent(1,fbin)
	h.SetBinError(1,fbine)
	h.SetBinContent(0,0)
	h.SetBinError(0,0)
    if addOverflow:
        nbins = h.GetNbinsX();
	fbin  = h.GetBinContent(nbins) + h.GetBinContent(nbins+1)
	fbine = ROOT.TMath.Sqrt(h.GetBinError(nbins)*h.GetBinError(nbins)  + h.GetBinError(nbins+1)*h.GetBinError(nbins+1))
	h.SetBinContent(nbins,fbin)
	h.SetBinError(nbins,fbine)
	h.SetBinContent(nbins+1,0)
	h.SetBinError(nbins+1,0)


def setTDRStyle():
    """
    Loads TDR style
    """
    tdrStyle = ROOT.TStyle("tdrStyle","Style for P-TDR")
    # For the canvas:
    tdrStyle.SetCanvasBorderMode(0)
    tdrStyle.SetCanvasColor(ROOT.kWhite)
    tdrStyle.SetCanvasDefH(928) #Height of canvas
    tdrStyle.SetCanvasDefW(904) #Width of canvas
    tdrStyle.SetCanvasDefX(1320)   #POsition on screen
    tdrStyle.SetCanvasDefY(0)
    
    # For the Pad:
    tdrStyle.SetPadBorderMode(0)
    # tdrStyle.SetPadBorderSize(Width_t size = 1)
    tdrStyle.SetPadColor(ROOT.kWhite)
    tdrStyle.SetPadGridX(False)
    tdrStyle.SetPadGridY(False)
    tdrStyle.SetGridColor(0)
    tdrStyle.SetGridStyle(3)
    tdrStyle.SetGridWidth(1)
    
    # For the frame:
    tdrStyle.SetFrameBorderMode(0)
    tdrStyle.SetFrameBorderSize(1)
    tdrStyle.SetFrameFillColor(0)
    tdrStyle.SetFrameFillStyle(0)
    tdrStyle.SetFrameLineColor(1)
    tdrStyle.SetFrameLineStyle(1)
    tdrStyle.SetFrameLineWidth(1)
    
    # For the histo:
    # tdrStyle.SetHistFillColor(1)
    # tdrStyle.SetHistFillStyle(0)
    tdrStyle.SetHistLineColor(1)
    tdrStyle.SetHistLineStyle(0)
    tdrStyle.SetHistLineWidth(1)
    # tdrStyle.SetLegoInnerR(Float_t rad = 0.5)
    # tdrStyle.SetNumberContours(Int_t number = 20)
    
    tdrStyle.SetEndErrorSize(2)
    #  tdrStyle.SetErrorMarker(20)
    tdrStyle.SetErrorX(0.)
    
    tdrStyle.SetMarkerStyle(20)
    
    # For the fit/function:
    tdrStyle.SetOptFit(1)
    tdrStyle.SetFitFormat("5.4g")
    tdrStyle.SetFuncColor(2)
    tdrStyle.SetFuncStyle(1)
    tdrStyle.SetFuncWidth(1)
    
    #For the date:
    tdrStyle.SetOptDate(0)
    # tdrStyle.SetDateX(Float_t x = 0.01)
    # tdrStyle.SetDateY(Float_t y = 0.01)
    
    # For the statistics box:
    tdrStyle.SetOptFile(0)
    tdrStyle.SetOptStat(0) # To display the mean and RMS:   SetOptStat("mr")
    tdrStyle.SetStatColor(ROOT.kWhite)
    tdrStyle.SetStatFont(42)
    tdrStyle.SetStatFontSize(0.025)
    tdrStyle.SetStatTextColor(1)
    tdrStyle.SetStatFormat("6.4g")
    tdrStyle.SetStatBorderSize(1)
    tdrStyle.SetStatH(0.1)
    tdrStyle.SetStatW(0.15)
    # tdrStyle.SetStatStyle(Style_t style = 1001)
    # tdrStyle.SetStatX(Float_t x = 0)
    # tdrStyle.SetStatY(Float_t y = 0)
    
    # Margins:
    tdrStyle.SetPadTopMargin(0.07)
    tdrStyle.SetPadBottomMargin(0.13)
    tdrStyle.SetPadLeftMargin(0.17)
    tdrStyle.SetPadRightMargin(0.03)
    
    # For the Global title:
    tdrStyle.SetOptTitle(0)
    tdrStyle.SetTitleFont(42)
    tdrStyle.SetTitleColor(1)
    tdrStyle.SetTitleTextColor(1)
    tdrStyle.SetTitleFillColor(10)
    tdrStyle.SetTitleFontSize(0.065)
    tdrStyle.SetTitleH(0.07) # Set the height of the title box
    tdrStyle.SetTitleW(0.80) # Set the width of the title box
    tdrStyle.SetTitleX(0.15) # Set the position of the title box
    tdrStyle.SetTitleY(1.00) # Set the position of the title box
    # tdrStyle.SetTitleStyle(Style_t style = 1001)
    tdrStyle.SetTitleBorderSize(1)

    # For the axis titles:
    tdrStyle.SetTitleColor(1, "XYZ")
    tdrStyle.SetTitleFont(42, "XYZ")
    tdrStyle.SetTitleSize(0.06, "XYZ")
    # tdrStyle.SetTitleXSize(Float_t size = 0.02) # Another way to set the size?
    # tdrStyle.SetTitleYSize(Float_t size = 0.02)
    tdrStyle.SetTitleXOffset(0.95)
    tdrStyle.SetTitleYOffset(1.3)
    # tdrStyle.SetTitleOffset(1.1, "Y") # Another way to set the Offset
    
    # For the axis labels:
    tdrStyle.SetLabelColor(1, "XYZ")
    tdrStyle.SetLabelFont(42, "XYZ")
    tdrStyle.SetLabelOffset(0.007, "XYZ")
    tdrStyle.SetLabelSize(0.044, "XYZ")

    # For the axis:
    tdrStyle.SetAxisColor(1, "XYZ")
    tdrStyle.SetStripDecimals(True)
    tdrStyle.SetTickLength(0.03, "XYZ")
    tdrStyle.SetNdivisions(510, "XYZ")
    tdrStyle.SetPadTickX(1)  # To get tick marks on the opposite side of the frame
    tdrStyle.SetPadTickY(1)
    
    # Change for log plots:
    tdrStyle.SetOptLogx(0)
    tdrStyle.SetOptLogy(0)
    tdrStyle.SetOptLogz(0)
    
    # Postscript options:
    tdrStyle.SetPaperSize(20.,20.)
    # tdrStyle.SetLineScalePS(Float_t scale = 3)
    # tdrStyle.SetLineStyleString(Int_t i, const char* text)
    # tdrStyle.SetHeaderPS(const char* header)
    # tdrStyle.SetTitlePS(const char* pstitle)
    
    # tdrStyle.SetBarOffset(Float_t baroff = 0.5)
    # tdrStyle.SetBarWidth(Float_t barwidth = 0.5)
    # tdrStyle.SetPaintTextFormat(const char* format = "g")
    # tdrStyle.SetPalette(Int_t ncolors = 0, Int_t* colors = 0)
    # tdrStyle.SetTimeOffset(Double_t toffset)
    # tdrStyle.SetHistMinimumZero(True)
    
    tdrStyle.cd()

