#!/usr/bin/env python3
import ROOT
import os
from array import array
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetEndErrorSize(5)

# Data / MC / SF colors 
_COL_DATA  = ROOT.kAzure  + 2
_COL_MC    = ROOT.kRed    + 2
_COL_SF    = ROOT.kViolet - 6

# Syst breakdown color list (CMS-style hex palette)
_SYST_COLORS = [ROOT.TColor.GetColor(c) for c in
    ["#5790fc", "#f89c20", "#e42536", "#964a8b", "#5b5b5e", "#7a21dd"]]

def plot_histogram(
    rootfile,
    histname,
    title="",
    xtitle="",
    ytitle="Events",
    output_name="plot",
    output_dir="plots_tagging",
    color=ROOT.kBlack,
    ymin=None,
    ymax=None,
    logy=False,
):
    f = ROOT.TFile.Open(rootfile)
    h = f.Get(histname)
    if not h:
        raise RuntimeError(f"Histogram {histname} not found in {rootfile}")
    h = h.Clone()
    h.SetDirectory(0)
    f.Close()

    c = ROOT.TCanvas("c", "c", 800, 700)
    c.SetMargin(0.13, 0.05, 0.12, 0.08)
    c.SetGrid()
    if logy:
        c.SetLogy()

    h.SetTitle(title)
    h.SetLineColor(color)
    h.SetMarkerColor(color)
    h.SetMarkerStyle(20)
    h.SetMarkerSize(1.1)
    h.SetLineWidth(2)

    h.GetXaxis().SetTitle(xtitle)
    h.GetYaxis().SetTitle(ytitle)
    h.GetXaxis().SetTitleSize(0.052)
    h.GetYaxis().SetTitleSize(0.052)
    h.GetXaxis().SetLabelSize(0.047)
    h.GetYaxis().SetLabelSize(0.047)
    h.GetYaxis().SetTitleOffset(0.9)

    if ymin is not None: h.SetMinimum(ymin)
    if ymax is not None: h.SetMaximum(ymax)
    h.Draw("E1")

    os.makedirs(output_dir, exist_ok=True)
    c.SaveAs(os.path.join(output_dir, f"{output_name}.pdf"))
    #c.SaveAs(os.path.join(output_dir, f"{output_name}.png"))
    print(f"Saved plot to {output_dir}/{output_name}.pdf")

def draw_cms_label(pad, name, region):
    """Draw CMS / Work in progress + region label in top-left of pad (NDC)"""
    pad.cd()
    lat = ROOT.TLatex()
    lat.SetNDC()
    lat.SetTextFont(42)
    lat.SetTextSize(0.043)
    lat.DrawLatex(0.16, 0.84, "#bf{CMS} #it{Work in progress}")
    lat.SetTextSize(0.038)
    lat.DrawLatex(0.16, 0.78, f"{name}")
    lat.DrawLatex(0.16, 0.73, "MonoV")

def plot_eff_with_sf(
    rootfile,
    region,
    name="",
    title="",
    xtitle="FatJet p_{T} [GeV]",
    output_name="eff_sf",
    output_dir="plots_tagging",
):

    f = ROOT.TFile.Open(rootfile)

    h_mc   = f.Get(f"h_mc_eff_{region}")
    h_data = f.Get(f"h_data_eff_{region}")
    h_sf   = f.Get(f"h_sf_{region}")

    h_mc   = h_mc.Clone()
    h_data = h_data.Clone()
    h_sf   = h_sf.Clone()

    for h in [h_mc, h_data, h_sf]:
        h.SetDirectory(0)

    f.Close()

    # two pad canvas
    c = ROOT.TCanvas("c", "c", 600, 700)

    pad1 = ROOT.TPad("pad1", "", 0, 0.28, 1, 1.00)
    pad2 = ROOT.TPad("pad2", "", 0, 0.00, 1, 0.3)

    pad1.SetBottomMargin(0.05)
    pad2.SetTopMargin(0.02)
    pad2.SetBottomMargin(0.25)

    pad1.SetLeftMargin(0.12)
    pad1.SetRightMargin(0.05)

    pad2.SetLeftMargin(0.12)
    pad2.SetRightMargin(0.05)

    pad1.Draw()
    pad2.Draw()

    # top
    pad1.cd()
    pad1.SetGrid()

    h_mc.SetTitle(title)
    h_mc.SetLineColor(_COL_MC)
    h_mc.SetMarkerColor(_COL_MC)
    h_mc.SetMarkerStyle(24)
    h_mc.SetLineWidth(2)

    h_data.SetLineColor(_COL_DATA)
    h_data.SetMarkerColor(_COL_DATA)
    h_data.SetMarkerStyle(20)
    h_data.SetLineWidth(2)

    h_mc.GetYaxis().SetTitle("Efficiency")
    h_mc.GetYaxis().SetTitleSize(0.052)
    h_mc.GetYaxis().SetLabelSize(0.047)
    h_mc.GetYaxis().SetTitleOffset(0.9)
    h_mc.GetXaxis().SetLabelSize(0)
    h_mc.GetXaxis().SetTickLength(0)
    h_mc.GetXaxis().SetTitleSize(0)

    h_mc.SetMinimum(0)
    h_mc.SetMaximum(1.1)

    h_mc.Draw("E1")
    h_data.Draw("E1 SAME")

    leg = ROOT.TLegend(0.60, 0.74, 0.93, 0.88)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextSize(0.045)
    leg.SetEntrySeparation(0.5)
    leg.AddEntry(h_data, "Data Estimates", "lep")
    leg.AddEntry(h_mc,   "MC",             "lep")
    leg.Draw()

    draw_cms_label(pad1, name, region)

    # bottom
    pad2.cd()
    pad2.SetGrid()

    h_sf.SetTitle("")
    h_sf.SetLineColor(_COL_SF)
    h_sf.SetMarkerColor(_COL_SF)
    h_sf.SetMarkerStyle(20)
    h_sf.SetLineWidth(2)

    h_sf.GetYaxis().SetTitle("Scale Factor")
    h_sf.GetXaxis().SetTitle(xtitle)

    h_sf.GetYaxis().SetTitleSize(0.100)
    h_sf.GetYaxis().SetLabelSize(0.090)
    h_sf.GetXaxis().SetTitleSize(0.115)
    h_sf.GetXaxis().SetLabelSize(0.113)

    h_sf.GetYaxis().SetTitleOffset(0.5)

    h_sf.SetMinimum(0.55)
    h_sf.SetMaximum(1.25)

    h_sf.Draw("E1")

    # 1 line
    line = ROOT.TLine(
        h_sf.GetXaxis().GetXmin(),
        1.0,
        h_sf.GetXaxis().GetXmax(),
        1.0,
    )
    line.SetLineStyle(2)
    line.SetLineColor(ROOT.kRed - 3)
    line.Draw()

    os.makedirs(output_dir, exist_ok=True)
    c.SaveAs(os.path.join(output_dir, f"{output_name}.pdf"))
    #c.SaveAs(os.path.join(output_dir, f"{output_name}.png"))
    print(f"Saved plot to {output_dir}/{output_name}.pdf")

def plot_eff_sf_with_uncertainty(
    h_mc_nom,
    h_data_nom,
    h_sf_nom,
    h_mc_total_up,
    h_mc_total_down,
    h_data_total_up,
    h_data_total_down,
    h_sf_total_up,
    h_sf_total_down,
    region="",
    name="",
    title="",
    xtitle="FatJet p_{T} [GeV]",
    output_name="eff_sf_with_uncertainty",
    output_dir="plots_tagging",
):
    c = ROOT.TCanvas("c_eff_sf_unc", "c_eff_sf_unc", 600, 700)

    pad1 = ROOT.TPad("pad1", "", 0, 0.28, 1, 1.00)
    pad2 = ROOT.TPad("pad2", "", 0, 0.00, 1, 0.30)

    pad1.SetBottomMargin(0.05)
    pad2.SetTopMargin(0.02)
    pad2.SetBottomMargin(0.25)
    pad1.SetLeftMargin(0.12)
    pad1.SetRightMargin(0.05)
    pad2.SetLeftMargin(0.12)
    pad2.SetRightMargin(0.05)

    pad1.Draw()
    pad2.Draw()

    # --- top pad: efficiency + uncertainty bands ---
    pad1.cd()
    pad1.SetGrid()

    band_mc   = make_uncertainty_band(h_mc_nom,   h_mc_total_up,   h_mc_total_down)
    band_data = make_uncertainty_band(h_data_nom, h_data_total_up, h_data_total_down)

    band_mc.SetFillColorAlpha(_COL_MC, 0.20)
    band_mc.SetLineColor(_COL_MC)
    band_mc.SetFillStyle(1001)

    band_data.SetFillColorAlpha(_COL_DATA, 0.15)
    band_data.SetLineColor(_COL_DATA)
    band_data.SetFillStyle(1001)

    h_mc_nom.SetTitle(title)
    h_mc_nom.SetLineColor(_COL_MC)
    h_mc_nom.SetMarkerColor(_COL_MC)
    h_mc_nom.SetMarkerStyle(24)
    h_mc_nom.SetLineWidth(2)
    h_mc_nom.SetFillColorAlpha(_COL_MC, 0.20)
    h_mc_nom.SetFillStyle(1001)

    h_data_nom.SetLineColor(_COL_DATA)
    h_data_nom.SetMarkerColor(_COL_DATA)
    h_data_nom.SetMarkerStyle(20)
    h_data_nom.SetLineWidth(2)
    h_data_nom.SetFillColorAlpha(_COL_DATA, 0.15)
    h_data_nom.SetFillStyle(1001)

    h_mc_nom.GetYaxis().SetTitle("Efficiency")
    h_mc_nom.GetYaxis().SetTitleSize(0.052)
    h_mc_nom.GetYaxis().SetLabelSize(0.047)
    h_mc_nom.GetYaxis().SetTitleOffset(0.9)
    h_mc_nom.GetXaxis().SetLabelSize(0)
    h_mc_nom.GetXaxis().SetTickLength(0)
    h_mc_nom.GetXaxis().SetTitleSize(0)
    h_mc_nom.SetMinimum(0)
    h_mc_nom.SetMaximum(1.1)

    h_mc_nom.Draw("E1")
    band_mc.Draw("2 SAME")
    band_data.Draw("2 SAME")
    h_mc_nom.Draw("E1 SAME")
    h_data_nom.Draw("E1 SAME")

    leg = ROOT.TLegend(0.60, 0.76, 0.93, 0.88)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextSize(0.045)
    leg.SetEntrySeparation(0.5)
    leg.AddEntry(h_data_nom, "Data Estimates", "lepf")
    leg.AddEntry(h_mc_nom,   "MC",             "lepf")
    leg.Draw()

    draw_cms_label(pad1, name, region)

    # --- bottom pad: SF + uncertainty band ---
    pad2.cd()
    pad2.SetGrid()

    band_sf = make_uncertainty_band(h_sf_nom, h_sf_total_up, h_sf_total_down)
    band_sf.SetFillColorAlpha(_COL_SF, 0.15)
    band_sf.SetLineColor(_COL_SF)
    band_sf.SetFillStyle(1001)

    h_sf_nom.SetTitle("")
    h_sf_nom.SetLineColor(_COL_SF)
    h_sf_nom.SetMarkerColor(_COL_SF)
    h_sf_nom.SetMarkerStyle(20)
    h_sf_nom.SetLineWidth(2)

    h_sf_nom.GetYaxis().SetTitle("Scale Factor")
    h_sf_nom.GetXaxis().SetTitle(xtitle)
    h_sf_nom.GetYaxis().SetTitleSize(0.100)
    h_sf_nom.GetYaxis().SetLabelSize(0.090)
    h_sf_nom.GetXaxis().SetTitleSize(0.115)
    h_sf_nom.GetXaxis().SetLabelSize(0.113)
    h_sf_nom.GetYaxis().SetTitleOffset(0.5)
    h_sf_nom.SetMinimum(0.55)
    h_sf_nom.SetMaximum(1.25)

    h_sf_nom.Draw("E1")
    band_sf.Draw("2 SAME")
    h_sf_nom.Draw("E1 SAME")

    line = ROOT.TLine(
        h_sf_nom.GetXaxis().GetXmin(), 1.0,
        h_sf_nom.GetXaxis().GetXmax(), 1.0,
    )
    line.SetLineStyle(2)
    line.SetLineColor(ROOT.kRed - 3)
    line.SetLineWidth(2)
    line.Draw()

    os.makedirs(output_dir, exist_ok=True)
    c.SaveAs(os.path.join(output_dir, f"{output_name}.pdf"))
    #c.SaveAs(os.path.join(output_dir, f"{output_name}.png"))
    print(f"Saved plot to {output_dir}/{output_name}.pdf")

def make_uncertainty_band(h_nom, h_unc_up, h_unc_down):
    """Convert nominal + asymmetric uncertainty histograms into a TGraphAsymmErrors band.

    h_unc_up   -- positive magnitudes for the upward (high) uncertainty
    h_unc_down -- positive magnitudes for the downward (low) uncertainty
    """
    n   = h_nom.GetNbinsX()
    x   = array('d', [h_nom.GetBinCenter(i)        for i in range(1, n+1)])
    y   = array('d', [h_nom.GetBinContent(i)        for i in range(1, n+1)])
    ex  = array('d', [h_nom.GetBinWidth(i) / 2.0    for i in range(1, n+1)])
    eyl = array('d', [h_unc_down.GetBinContent(i)   for i in range(1, n+1)])
    eyh = array('d', [h_unc_up.GetBinContent(i)     for i in range(1, n+1)])
    return ROOT.TGraphAsymmErrors(n, x, y, ex, ex, eyl, eyh)

def plot_eff_with_uncertainty(
    h_mc_nom,
    h_data_nom,
    h_mc_total_up,
    h_mc_total_down,
    h_data_total_up,
    h_data_total_down,
    region="",
    name="",
    title="",
    xtitle="FatJet p_{T} [GeV]",
    output_name="eff_with_uncertainty",
    output_dir="plots_tagging",
):
    """
    Draws a shaded band for total uncertainty (stat+syst) and stat-only
    error bars on top, so both are visible.
    """
    c = ROOT.TCanvas("c_unc", "c_unc", 800, 700)
    c.SetMargin(0.13, 0.05, 0.12, 0.08)
    c.SetGrid()

    band_mc   = make_uncertainty_band(h_mc_nom,   h_mc_total_up,   h_mc_total_down)
    band_data = make_uncertainty_band(h_data_nom, h_data_total_up, h_data_total_down)

    band_mc.SetFillColorAlpha(_COL_MC, 0.20)
    band_mc.SetLineColor(_COL_MC)
    band_mc.SetFillStyle(1001)

    band_data.SetFillColorAlpha(_COL_DATA, 0.15)
    band_data.SetLineColor(_COL_DATA)
    band_data.SetFillStyle(1001)

    h_mc_nom.SetLineColor(_COL_MC)
    h_mc_nom.SetMarkerColor(_COL_MC)
    h_mc_nom.SetMarkerStyle(24)
    h_mc_nom.SetMarkerSize(1.1)
    h_mc_nom.SetLineWidth(2)
    h_mc_nom.SetFillColorAlpha(_COL_MC, 0.20)
    h_mc_nom.SetFillStyle(1001)

    h_data_nom.SetLineColor(_COL_DATA)
    h_data_nom.SetMarkerColor(_COL_DATA)
    h_data_nom.SetMarkerStyle(20)
    h_data_nom.SetMarkerSize(1.1)
    h_data_nom.SetLineWidth(2)
    h_data_nom.SetFillColorAlpha(_COL_DATA, 0.15)
    h_data_nom.SetFillStyle(1001)

    h_mc_nom.SetTitle(title)
    h_mc_nom.GetXaxis().SetTitle(xtitle)
    h_mc_nom.GetYaxis().SetTitle("Efficiency")
    h_mc_nom.GetXaxis().SetTitleSize(0.052)
    h_mc_nom.GetYaxis().SetTitleSize(0.052)
    h_mc_nom.GetXaxis().SetLabelSize(0.047)
    h_mc_nom.GetYaxis().SetLabelSize(0.047)
    h_mc_nom.GetYaxis().SetTitleOffset(0.9)
    h_mc_nom.SetMinimum(0)
    h_mc_nom.SetMaximum(1.1)

    h_mc_nom.Draw("E1")
    band_mc.Draw("2 SAME")
    band_data.Draw("2 SAME")
    h_mc_nom.Draw("E1 SAME")
    h_data_nom.Draw("E1 SAME")

    leg = ROOT.TLegend(0.62, 0.76, 0.93, 0.90)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextSize(0.045)
    leg.SetEntrySeparation(0.5)
    leg.AddEntry(h_data_nom, "Data Estimates", "lepf")
    leg.AddEntry(h_mc_nom,   "MC",             "lepf")
    leg.Draw()

    draw_cms_label(c, name, region)

    os.makedirs(output_dir, exist_ok=True)
    c.SaveAs(os.path.join(output_dir, f"{output_name}.pdf"))
    #c.SaveAs(os.path.join(output_dir, f"{output_name}.png"))
    print(f"Saved plot to {output_dir}/{output_name}.pdf")
