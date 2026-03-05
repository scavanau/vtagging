#!/usr/bin/env python3
import ROOT
import os

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
#Has to be run after running tagging_plots.py
#Otherwise sf output will not be intended sf
def plot_sf_comparison(
    rootfile,
    region,
    pog_values,
    pog_errors,
    output_dir="plots_tagging",
):

    f = ROOT.TFile.Open(rootfile)
    h_sf = f.Get(f"h_sf_{region}")

    h_sf = h_sf.Clone()
    h_sf.SetDirectory(0)
    f.Close()

    nbins = h_sf.GetNbinsX()

    # histogram for values wanting to add to graph
    h_pog = h_sf.Clone("h_pog")
    h_pog.Reset()

    for i in range(1, nbins + 1):
        h_pog.SetBinContent(i, pog_values[i - 1])
        h_pog.SetBinError(i, pog_errors[i - 1])

    c = ROOT.TCanvas("c", "c", 800, 700)
    c.SetMargin(0.12, 0.05, 0.12, 0.08)
    c.SetGrid()

    #Canvases
    mono_color = ROOT.TColor.GetColor("#5B4B8A")  # medium blue-purple
    h_sf.SetLineColor(mono_color)
    h_sf.SetMarkerColor(mono_color)
    h_sf.SetMarkerStyle(20)
    h_sf.SetLineWidth(2)

    pog_color = ROOT.TColor.GetColor("#006400")  # dark green
    h_pog.SetLineColor(pog_color)
    h_pog.SetMarkerColor(pog_color)
    h_pog.SetMarkerStyle(21)
    h_pog.SetLineWidth(2)

    h_sf.SetTitle("")
    h_sf.GetXaxis().SetTitle("FatJet p_{T} [GeV]")
    h_sf.GetYaxis().SetTitle("Scale Factor")

    h_sf.SetMinimum(0)
    h_sf.SetMaximum(1.5)

    h_sf.Draw("E1")
    h_pog.Draw("E1 SAME")

    leg = ROOT.TLegend(0.55, 0.75, 0.85, 0.88)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.AddEntry(h_sf, "MonoV Derived", "lep")
    leg.AddEntry(h_pog, "POG Values", "lep")
    leg.Draw()

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    outname = os.path.join(output_dir, f"{region}_sf_comparison.pdf")
    c.SaveAs(outname)

    print(f"Saved plot to {outname}")

if __name__ == "__main__":

    region = "slep" ###Change region to compare each to the POG values 
    rootfile = f"rootfiles/eff_{region}.root"

    # Manual inputs (must match number of bins)
    pog_values = [0.86, 0.86, 0.69] #2022
    pog_errors = [0.07, 0.06, 0.14]
    #pog_values = [0.94, 0.81, 0.76] #2022EE
    #pog_errors = [0.03, 0.04, 0.06]
    
    plot_sf_comparison(
        rootfile=rootfile,
        region=region,
        pog_values=pog_values,
        pog_errors=pog_errors,
    )