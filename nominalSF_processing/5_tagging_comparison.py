#!/usr/bin/env python3
import ROOT
import os

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)

def plot_sf_comparison(
    rootfile,
    region,
    pog_values,
    pog_errors,
    output_dir="plots_tagging",
    title="Scale Factor Comparison",
    era_label="",
):
    f = ROOT.TFile.Open(rootfile)
    h_sf = f.Get(f"h_sf_{region}")
    h_sf = h_sf.Clone()
    h_sf.SetDirectory(0)
    f.Close()

    """Build POG histogram to match binning of derived SF"""
    h_pog = h_sf.Clone("h_pog")
    h_pog.Reset()
    for i in range(1, h_sf.GetNbinsX() + 1):
        h_pog.SetBinContent(i, pog_values[i - 1])
        h_pog.SetBinError(i, pog_errors[i - 1])

    c = ROOT.TCanvas("c", "c", 800, 700)
    c.SetMargin(0.12, 0.05, 0.12, 0.08)
    c.SetGrid()

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

    h_sf.SetTitle(title)
    h_sf.GetXaxis().SetTitle("FatJet p_{T} [GeV]")
    h_sf.GetYaxis().SetTitle("Scale Factor")
    h_sf.SetMinimum(0)
    h_sf.SetMaximum(1.5)

    h_sf.Draw("E1")
    h_pog.Draw("E1 SAME")

    leg = ROOT.TLegend(0.55, 0.75, 0.85, 0.88)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.AddEntry(h_sf,  "MonoV Derived", "lep")
    leg.AddEntry(h_pog, "POG Values",    "lep")
    # For reweighting comparisons swap above labels with:
    # "With Top Reweight" / "No Top Reweight"
    leg.Draw()

    # Era label (e.g. "2022EE")
    text = ROOT.TLatex()
    text.SetNDC()
    text.SetTextSize(0.04)
    text.SetTextAlign(13)
    text.DrawLatex(0.15, 0.89, era_label)

    os.makedirs(output_dir, exist_ok=True)
    outname = os.path.join(output_dir, "sf_comparison.pdf")
    c.SaveAs(outname)
    print(f"Saved plot to {outname}")

if __name__ == "__main__":
    """POG scale factors per era — add new eras here as needed"""
    pog = {
        "2022":   {"values": [0.86, 0.86, 0.69], "errors": [0.07, 0.06, 0.14]},
        "high_pt_cut": {"values": [0.68, 0.78, 0.84], "errors": [0.02, 0.02, 0.04]},
        "2022EE": {"values": [0.94, 0.81, 0.76], "errors": [0.03, 0.04, 0.06]},
    }

    era      = "2022"   # EDIT
    region   = "sele"  # EDIT
    plot_dir = f"plots_tagging/{region}" 

    plot_sf_comparison(
        rootfile=f"rootfiles/eff_{region}.root",
        region=region,
        pog_values=pog[era]["values"],
        pog_errors=pog[era]["errors"],
        title="Comparison of SF's for Single Electron CR",
        era_label=era,
        output_dir=plot_dir, 
    )