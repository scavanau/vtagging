####
#Doesn't need to be run, just for plotting settings
####
#!/usr/bin/env python3
import ROOT
import os

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)

def plot_basic(
    rootfile,
    histname,
    title="",
    xtitle="",
    ytitle="Events",
    output_name="plot",
    output_dir="plots_tagging",
    logy=False,
):

    f = ROOT.TFile.Open(rootfile)
    h = f.Get(histname)
    if not h:
        raise RuntimeError(f"Histogram {histname} not found in {rootfile}")

    h = h.Clone()
    h.SetDirectory(0)
    f.Close()

    # Canvas
    c = ROOT.TCanvas("c", "c", 800, 700)
    c.SetMargin(0.12, 0.05, 0.12, 0.08)
    c.SetGrid()

    if logy:
        c.SetLogy()

    h.SetTitle(title)
    h.SetLineColor(ROOT.kBlue + 1)
    h.SetMarkerStyle(20)
    h.SetMarkerSize(1.0)
    h.SetMarkerColor(ROOT.kBlue + 1)
    h.SetLineWidth(2)

    h.GetXaxis().SetTitle(xtitle)
    h.GetYaxis().SetTitle(ytitle)

    h.GetXaxis().SetTitleSize(0.045)
    h.GetYaxis().SetTitleSize(0.045)

    h.GetXaxis().SetLabelSize(0.04)
    h.GetYaxis().SetLabelSize(0.04)

    h.Draw("E1")

    # Output
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    c.SaveAs(os.path.join(output_dir, f"{output_name}.pdf"))
    c.SaveAs(os.path.join(output_dir, f"{output_name}.png"))

    print(f"Saved plot to {output_dir}/{output_name}.pdf")
    
def plot_histogram(
    rootfile,
    histname,
    title="",
    xtitle="",
    ytitle="",
    output_name="plot",
    output_dir="plots_tagging",
    ymin=None,
    ymax=None,
):
    """
    General plotting function for efficiencies and scale factors.
    """
    f = ROOT.TFile.Open(rootfile)
    h = f.Get(histname)
    if not h:
        raise RuntimeError(f"Histogram {histname} not found in {rootfile}")

    h = h.Clone()
    h.SetDirectory(0)
    f.Close()

    # create canvas
    c = ROOT.TCanvas("c", "c", 800, 700)
    c.SetMargin(0.13, 0.05, 0.12, 0.08)
    c.SetGrid()

    h.SetTitle(title)
    h.SetLineColor(ROOT.kBlack)
    h.SetMarkerStyle(20)
    h.SetMarkerSize(1.1)
    h.SetMarkerColor(ROOT.kBlack)
    h.SetLineWidth(2)

    h.GetXaxis().SetTitle(xtitle)
    h.GetYaxis().SetTitle(ytitle)

    h.GetXaxis().SetTitleSize(0.045)
    h.GetYaxis().SetTitleSize(0.045)

    h.GetXaxis().SetLabelSize(0.04)
    h.GetYaxis().SetLabelSize(0.04)

    if ymin is not None:
        h.SetMinimum(ymin)
    if ymax is not None:
        h.SetMaximum(ymax)
        
    h.Draw("E1")

    # Output
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    c.SaveAs(os.path.join(output_dir, f"{output_name}.pdf"))
    c.SaveAs(os.path.join(output_dir, f"{output_name}.png"))

    print(f"Saved plot to {output_dir}/{output_name}.pdf")

def plot_eff_with_sf(
    rootfile,
    region,
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

    pad1.SetBottomMargin(0.1)
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
    h_mc.SetLineColor(ROOT.kBlue+1)
    h_mc.SetMarkerColor(ROOT.kBlue+1)
    h_mc.SetMarkerStyle(20)
    h_mc.SetLineWidth(2)

    h_data.SetLineColor(ROOT.kOrange-3)
    h_data.SetMarkerColor(ROOT.kOrange-3)
    h_data.SetMarkerStyle(21)
    h_data.SetLineWidth(2)

    h_mc.GetYaxis().SetTitle("Efficiency")
    h_mc.GetYaxis().SetTitleSize(0.045)
    h_mc.GetYaxis().SetLabelSize(0.04)

    h_mc.SetMinimum(0)
    h_mc.SetMaximum(1.1)

    h_mc.Draw("E1")
    h_data.Draw("E1 SAME")

    leg = ROOT.TLegend(0.6, 0.75, 0.85, 0.88)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.AddEntry(h_data, "Data", "lep")
    leg.AddEntry(h_mc, "MC", "lep")
    leg.Draw()

    # bottom
    pad2.cd()
    pad2.SetGrid()

    h_sf.SetTitle("")
    h_sf.SetLineColor(ROOT.kRed+1)
    h_sf.SetMarkerColor(ROOT.kRed+1)
    h_sf.SetMarkerStyle(20)
    h_sf.SetLineWidth(2)

    h_sf.GetYaxis().SetTitle("Scale Factor")
    h_sf.GetXaxis().SetTitle(xtitle)

    h_sf.GetYaxis().SetTitleSize(0.09)
    h_sf.GetYaxis().SetLabelSize(0.08)
    h_sf.GetXaxis().SetTitleSize(0.1)
    h_sf.GetXaxis().SetLabelSize(0.08)

    h_sf.GetYaxis().SetTitleOffset(0.5)

    h_sf.SetMinimum(0.55)
    h_sf.SetMaximum(1.15)

    h_sf.Draw("E1")

    # 1 line
    line = ROOT.TLine(
        h_sf.GetXaxis().GetXmin(),
        1.0,
        h_sf.GetXaxis().GetXmax(),
        1.0,
    )
    line.SetLineStyle(2)
    line.Draw()

    # Save
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    c.SaveAs(os.path.join(output_dir, f"{output_name}.pdf"))
    c.SaveAs(os.path.join(output_dir, f"{output_name}.png"))

    print(f"Saved plot to {output_dir}/{output_name}.pdf")