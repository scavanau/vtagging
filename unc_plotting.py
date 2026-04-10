#!/usr/bin/env python3
import ROOT
import os
import re
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.TH1.AddDirectory(False)   # prevent clones from being owned/deleted by TFile

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
    "mc_numerator",
    "mc_denominator",
    "data_numerator",
    "data_denominator",
]

Y_MIN_MC_NUMERATOR   = -200
Y_MAX_MC_NUMERATOR   =  200
Y_MIN_MC_DENOMINATOR = -200
Y_MAX_MC_DENOMINATOR =  200

Y_MIN_DATA_NUMERATOR   = -50
Y_MAX_DATA_NUMERATOR   =  50
Y_MIN_DATA_DENOMINATOR = -100
Y_MAX_DATA_DENOMINATOR =  100

COLORS = {
    "Top":             ROOT.kGreen - 2,
    #"QCD_W":           ROOT.kAzure + 2,
    "top_reweighting": ROOT.kViolet - 2,
}

PROC_LABELS = {
    "QCD_W": "W+Jet",
}

def get_proc_label(proc):
    return PROC_LABELS.get(proc, proc)

# ------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------
def get_safe_clone(root_file, name):
    """Clone a histogram from a TFile by name. Uses f.Get() — only call
    this before any TList iteration so ROOT's cache is still clean."""
    h = root_file.Get(name)
    if not h:
        return None
    clone = h.Clone(f"{name}_clone")
    clone.SetDirectory(0)
    return clone

def clone_from_key(key):
    """Clone a histogram directly from a TKey, bypassing ROOT's object
    cache. Safer than f.Get(name) when iterating GetListOfKeys()."""
    name = key.GetName()
    h = key.ReadObj()
    if not h or not hasattr(h, "GetNbinsX"):
        return None, name
    clone = h.Clone(f"{name}_clone")
    clone.SetDirectory(0)
    return clone, name

def get_color(proc, idx):
    if proc in COLORS:
        return COLORS[proc]

    fallback = [
        ROOT.kGreen + 2,
        ROOT.kOrange + 7,
        ROOT.kCyan + 2,
        ROOT.kViolet + 1,
        ROOT.kTeal + 2,
        ROOT.kPink + 7,
    ]
    return fallback[idx % len(fallback)]

def make_frame_from_nominal(h_nom, title):
    hframe = h_nom.Clone("hframe")
    hframe.SetDirectory(0)

    for ibin in range(0, hframe.GetNbinsX() + 2):
        hframe.SetBinContent(ibin, 0.0)
        hframe.SetBinError(ibin, 0.0)

    hframe.SetTitle(title)
    hframe.GetXaxis().SetTitleSize(0.048)
    hframe.GetYaxis().SetTitleSize(0.048)
    hframe.GetYaxis().SetTitleOffset(0.9)
    hframe.SetLineWidth(0)
    hframe.SetMarkerSize(0)
    return hframe

def make_zero_line_from_nominal(h_nom):
    hzero = h_nom.Clone("hzero")
    hzero.SetDirectory(0)

    for ibin in range(0, hzero.GetNbinsX() + 2):
        hzero.SetBinContent(ibin, 0.0)
        hzero.SetBinError(ibin, 0.0)

    hzero.SetLineColor(ROOT.kBlack)
    hzero.SetLineWidth(2)
    hzero.SetMarkerSize(0)
    return hzero

def make_stat_band_at_zero(h_nom):
    """
    Build a band centered at 0 whose error is nominal stat error.
    """
    h_stat = h_nom.Clone("h_stat")
    h_stat.SetDirectory(0)

    for ibin in range(0, h_stat.GetNbinsX() + 2):
        err = h_nom.GetBinError(ibin)
        h_stat.SetBinContent(ibin, 0.0)
        h_stat.SetBinError(ibin, err)

    h_stat.SetFillColorAlpha(ROOT.kGray + 1, 0.23)
    h_stat.SetLineColor(ROOT.kGray + 2)
    h_stat.SetMarkerSize(0)
    return h_stat

# ------------------------------------------------------------------
# Plot one ROOT uncertainty file
# ------------------------------------------------------------------
def plot_quantity(quantity, channel, era):
    input_dir  = os.path.join("rootfiles",    "uncertainties", f"{channel}_{era}")
    output_dir = os.path.join("plots_tagging", "uncertainties", f"{channel}_{era}")
    os.makedirs(output_dir, exist_ok=True)

    infile = os.path.join(input_dir, f"{quantity}.root")

    f = ROOT.TFile.Open(infile)
    if not f or f.IsZombie():
        raise RuntimeError(f"Could not open ROOT file: {infile}")

    h_nom = get_safe_clone(f, "h_nominal")
    if not h_nom:
        raise RuntimeError(f"h_nominal not found in {infile}")

    # want:
    #   h_<proc>_plus_delta
    #   h_<proc>_minus_delta
    #   h_top_reweight_delta
    pattern_pm  = re.compile(r"^h_(.+)_(plus|minus)_delta$")
    pattern_one = re.compile(r"^h_(.+)_delta$")

    pm_hists = {}      # (proc, plusminus) -> hist
    one_hists = {}     # proc -> hist

    for tkey in f.GetListOfKeys():
        name = tkey.GetName()
        if name == "h_nominal":
            continue

        m_pm = pattern_pm.match(name)
        if m_pm:
            proc, plusminus = m_pm.groups()
            h, _ = clone_from_key(tkey)
            if h:
                pm_hists[(proc, plusminus)] = h
            continue

        # catch one-sided delta, but avoid double-counting plus/minus ones
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

    title = f"{quantity.replace('_', ' ')} - {channel} {era};FatJet p_{{T}} [GeV];Events (varied - nominal)"

    is_data = quantity.startswith("data")
    if "denominator" in quantity:
        y_min = Y_MIN_DATA_DENOMINATOR if is_data else Y_MIN_MC_DENOMINATOR
        y_max = Y_MAX_DATA_DENOMINATOR if is_data else Y_MAX_MC_DENOMINATOR
    else:
        y_min = Y_MIN_DATA_NUMERATOR if is_data else Y_MIN_MC_NUMERATOR
        y_max = Y_MAX_DATA_NUMERATOR if is_data else Y_MAX_MC_NUMERATOR

    # frame only
    hframe = make_frame_from_nominal(h_nom, title)
    hframe.GetYaxis().SetRangeUser(y_min, y_max)
    hframe.Draw("HIST")

    # stat band
    h_stat = make_stat_band_at_zero(h_nom)
    h_stat.Draw("E2 SAME")

    leg = ROOT.TLegend(0.60, 0.56, 0.93, 0.88)
    leg.SetBorderSize(1)
    leg.SetFillColor(ROOT.kWhite)
    leg.SetFillStyle(1001)
    leg.SetTextSize(0.028)
    leg.AddEntry(h_stat, "Nominal stat. unc.", "f")

    all_pm_procs = sorted(set(proc for proc, _ in pm_hists.keys()))
    all_one_procs = sorted(one_hists.keys())

    # draw one-sided FIRST so they do not hide Top minus
    offset = len(all_pm_procs)
    for i, proc in enumerate(all_one_procs):
        h = one_hists[proc]
        color = get_color(proc, offset + i)

        h.SetLineColor(color)
        h.SetLineWidth(3)
        h.SetLineStyle(3)
        h.SetMarkerSize(0)
        h.Draw("HIST SAME")
        leg.AddEntry(h, f"{get_proc_label(proc)} sys. unc.", "l")

    # draw two-sided AFTER so dashed minus is visible on top
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

            h.Draw("HIST SAME")
            leg.AddEntry(h, f"{get_proc_label(proc)} ({'+'if plusminus == 'plus' else '-'}) sys. unc.", "l")
    # draw the black nominal zero line LAST
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