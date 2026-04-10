#!/usr/bin/env python3
import ROOT
import os
import re
from unc_plotting import (
    get_safe_clone,
    clone_from_key,
    get_color,
    get_proc_label,
    make_frame_from_nominal,
    make_zero_line_from_nominal,
    make_stat_band_at_zero,
)
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.TH1.AddDirectory(False)

CONFIGS = [
    ("smu",  "22"),
    ("smu",  "22EE"),
    ("smu",  "23"),
    ("smu",  "23BPix"),
    ("sele", "22"),
    ("sele", "22EE"),
    ("sele", "23"),
    ("sele", "23BPix"),
    ("slep", "22"),
    ("slep", "22EE"),
    ("slep", "23"),
    ("slep", "23BPix"),
]

QUANTITIES = [
    "sf",
]

Y_MIN_SF = -0.2
Y_MAX_SF =  0.2

# ------------------------------------------------------------------
# Plot one SF uncertainty file
# ------------------------------------------------------------------
def plot_quantity(quantity, channel, era):
    input_dir  = os.path.join("rootfiles",    "sf_uncertainties",  f"{channel}_{era}")
    output_dir = os.path.join("plots_tagging", "sf_uncertainties", f"{channel}_{era}")
    os.makedirs(output_dir, exist_ok=True)

    infile = os.path.join(input_dir, f"{quantity}.root")

    f = ROOT.TFile.Open(infile)
    if not f or f.IsZombie():
        raise RuntimeError(f"Could not open ROOT file: {infile}")

    h_nom = get_safe_clone(f, "h_nominal")
    if not h_nom:
        raise RuntimeError(f"h_nominal not found in {infile}")

    h_total_plus  = get_safe_clone(f, "h_total_delta_plus")
    h_total_minus = get_safe_clone(f, "h_total_delta_minus")

    pattern_pm  = re.compile(r"^h_(.+)_(plus|minus)_delta$")
    pattern_one = re.compile(r"^h_(.+)_delta$")

    pm_hists  = {}   # (proc, plusminus) -> hist
    one_hists = {}   # proc -> hist

    for tkey in f.GetListOfKeys():
        name = tkey.GetName()
        if name in ("h_nominal", "h_total_delta_plus", "h_total_delta_minus"):
            continue

        m_pm = pattern_pm.match(name)
        if m_pm:
            proc, plusminus = m_pm.groups()
            h, _ = clone_from_key(tkey)
            if h:
                pm_hists[(proc, plusminus)] = h
            continue

        m_one = pattern_one.match(name)
        if m_one and ("_plus_delta" not in name) and ("_minus_delta" not in name):
            proc = m_one.group(1)
            h, _ = clone_from_key(tkey)
            if h:
                one_hists[proc] = h
    f.Close()

    print(f"  [pm_hists]  {sorted(pm_hists.keys())}")
    print(f"  [one_hists] {sorted(one_hists.keys())}")

    if not pm_hists and not one_hists:
        raise RuntimeError(f"No delta histograms found in {infile}")

    c = ROOT.TCanvas(f"c_{quantity}", "", 900, 700)
    c.SetTicks(1, 1)
    c.SetTopMargin(0.07)
    c.SetLeftMargin(0.13)

    title = (
        f"Scale factor unc - {channel} {era}"
        f";FatJet p_{{T}} [GeV];SF (varied - nominal)"
    )

    hframe = make_frame_from_nominal(h_nom, title)
    hframe.GetYaxis().SetRangeUser(Y_MIN_SF, Y_MAX_SF)
    hframe.Draw("HIST")

    h_stat = make_stat_band_at_zero(h_nom)
    h_stat.Draw("E2 SAME")

    leg = ROOT.TLegend(0.62, 0.58, 0.93, 0.90)
    leg.SetBorderSize(1)
    leg.SetFillColor(ROOT.kWhite)
    leg.SetFillStyle(1001)
    leg.SetTextSize(0.028)
    leg.AddEntry(h_stat, "Nominal stat. unc.", "f")

    all_pm_procs  = sorted(set(proc for proc, _ in pm_hists.keys()))
    all_one_procs = sorted(one_hists.keys())

    # draw one-sided FIRST
    offset = len(all_pm_procs)
    for i, proc in enumerate(all_one_procs):
        h = one_hists[proc]
        color = get_color(proc, offset + i)
        h.SetLineColor(color)
        h.SetLineWidth(3)
        h.SetLineStyle(3)
        h.SetMarkerSize(0)
        h.SetFillStyle(0)
        h.Draw("HIST SAME")
        leg.AddEntry(h, f"{get_proc_label(proc)} sys. unc.", "l")

    # draw two-sided AFTER
    for iproc, proc in enumerate(all_pm_procs):
        color = get_color(proc, iproc)
        for plusminus in ["plus", "minus"]:
            key = (proc, plusminus)
            if key not in pm_hists:
                continue
            h = pm_hists[key]
            h.SetLineColor(color)
            h.SetLineWidth(3)
            h.SetMarkerSize(0)
            h.SetLineStyle(1 if plusminus == "plus" else 2)
            h.SetFillStyle(0)
            h.Draw("HIST SAME")
            leg.AddEntry(h, f"{get_proc_label(proc)} ({'+'if plusminus == 'plus' else '-'}) sys. unc.", "l")

    # draw total unc lines
    TOTAL_COLOR = ROOT.kRed - 3

    for h_tot, label, style in [
        (h_total_plus,  "Total (+) unc", 1),
        (h_total_minus, "Total (-) unc", 2),
    ]:
        if h_tot:
            h_tot.SetLineColor(TOTAL_COLOR)
            h_tot.SetLineWidth(3)
            h_tot.SetLineStyle(style)
            h_tot.SetMarkerSize(0)
            h_tot.SetFillStyle(0)
            h_tot.Draw("HIST SAME")
            leg.AddEntry(h_tot, label, "l")

    hzero = make_zero_line_from_nominal(h_nom)
    hzero.Draw("HIST SAME")

    ROOT.gPad.RedrawAxis()
    leg.Draw()

    out_path = os.path.join(output_dir, f"{quantity}.pdf")
    c.SaveAs(out_path)
    print(f"Saved: {out_path}")

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
if __name__ == "__main__":
    for channel, era in CONFIGS:
        print(f"\n{'='*60}\nChannel: {channel}   Era: {era}\n{'='*60}")
        for quantity in QUANTITIES:
            plot_quantity(quantity, channel, era)
