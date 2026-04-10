#!/usr/bin/env python3
import ROOT
import os
import re
from tagging_compute_unc import (
    make_delta_hist,
    split_delta_hist,
    hist_has_nonzero_content,
    write_hist,
    require_file,
)
ROOT.gROOT.SetBatch(True)
ROOT.TH1.SetDefaultSumw2(True)
ROOT.gStyle.SetOptStat(0)

ZERO_TOL = 1e-12

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

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def open_root(path):
    require_file(path)
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        raise OSError(f"Could not open ROOT file: {path}")
    return f

def get_safe_clone(root_file, name):
    h = root_file.Get(name)
    if not h:
        return None
    h = h.Clone(f"{name}_clone")
    h.SetDirectory(0)
    return h

# ---------------------------------------------------------------------------
# Efficiency helper
# ---------------------------------------------------------------------------

def make_efficiency_hist(h_num, h_den, name, binomial=True):
    """
    Build efficiency = numerator / denominator.

    MC (binomial=True): numerator is a strict subset of denominator so
    binomial errors apply (ROOT "B" option).

    Data (binomial=False): numerator/denominator are background-subtracted
    (data_obs - MC_bkg) and can go negative, so standard ratio error
    propagation is used instead.
    """
    h_eff = h_num.Clone(name)
    h_eff.SetDirectory(0)
    opt = "B" if binomial else ""
    h_eff.Divide(h_num, h_den, 1.0, 1.0, opt)
    return h_eff


# ---------------------------------------------------------------------------
# available stored sum histograms
# ---------------------------------------------------------------------------

def discover_variations(f_num, f_den):
    """
    From the numerator and denominator ROOT files, find the common variations
    that exist as stored SUM histograms.

    Two-sided:
      h_<proc>_plus_sum
      h_<proc>_minus_sum

    One-sided:
      h_<proc>_sum
    """
    pattern_pm  = re.compile(r"^h_(.+)_(plus|minus)_sum$")
    pattern_one = re.compile(r"^h_(.+)_sum$")

    num_pm = {}
    den_pm = {}
    num_one = {}
    den_one = {}

    # numerator file
    for key in f_num.GetListOfKeys():
        name = key.GetName()

        m_pm = pattern_pm.match(name)
        if m_pm:
            proc, plusminus = m_pm.groups()
            num_pm[(proc, plusminus)] = name
            continue

        m_one = pattern_one.match(name)
        if m_one and ("_plus_sum" not in name) and ("_minus_sum" not in name):
            proc = m_one.group(1)
            num_one[proc] = name

    # denominator file
    for key in f_den.GetListOfKeys():
        name = key.GetName()

        m_pm = pattern_pm.match(name)
        if m_pm:
            proc, plusminus = m_pm.groups()
            den_pm[(proc, plusminus)] = name
            continue

        m_one = pattern_one.match(name)
        if m_one and ("_plus_sum" not in name) and ("_minus_sum" not in name):
            proc = m_one.group(1)
            den_one[proc] = name

    common_pm = sorted(set(num_pm.keys()) & set(den_pm.keys()), key=lambda x: (x[0], x[1]))
    common_one = sorted(set(num_one.keys()) & set(den_one.keys()))

    return num_pm, den_pm, num_one, den_one, common_pm, common_one


# ---------------------------------------------------------------------------
# Total uncertainty
# ---------------------------------------------------------------------------

def make_total_uncertainty(h_nom, all_up_hists, all_down_hists):
    """
    Quadrature sum all sign-split delta histograms plus the nominal stat error.

      h_total_delta_plus[bin]  = +sqrt( sum_i(up_i[bin]^2)   + stat[bin]^2 )
      h_total_delta_minus[bin] = -sqrt( sum_i(down_i[bin]^2) + stat[bin]^2 )
      h_total_sum              = nominal efficiency with bin error
                                 = max(|plus|, |minus|) per bin
    """
    h_plus = h_nom.Clone("h_total_delta_plus")
    h_plus.SetDirectory(0)
    h_plus.Reset("ICES")

    h_minus = h_nom.Clone("h_total_delta_minus")
    h_minus.SetDirectory(0)
    h_minus.Reset("ICES")

    h_total = h_nom.Clone("h_total_sum")
    h_total.SetDirectory(0)

    for ibin in range(0, h_nom.GetNbinsX() + 2):
        stat = h_nom.GetBinError(ibin)

        sum_up_sq   = stat ** 2
        sum_down_sq = stat ** 2

        for h in all_up_hists:
            val = h.GetBinContent(ibin)
            if val > 0.0:
                sum_up_sq += val ** 2

        for h in all_down_hists:
            val = h.GetBinContent(ibin)
            if val < 0.0:
                sum_down_sq += val ** 2

        total_plus  =  sum_up_sq   ** 0.5
        total_minus = -sum_down_sq ** 0.5

        h_plus.SetBinContent(ibin,  total_plus)
        h_plus.SetBinError(ibin, 0.0)
        h_minus.SetBinContent(ibin, total_minus)
        h_minus.SetBinError(ibin, 0.0)
        h_total.SetBinError(ibin, max(total_plus, abs(total_minus)))

    return h_plus, h_minus, h_total


# ---------------------------------------------------------------------------
# writer
# ---------------------------------------------------------------------------

def build_efficiency_uncertainty_file(num_file_path, den_file_path, out_file_path, binomial=True):
    f_num = open_root(num_file_path)
    f_den = open_root(den_file_path)

    h_num_nom = get_safe_clone(f_num, "h_nominal")
    h_den_nom = get_safe_clone(f_den, "h_nominal")

    if not h_num_nom:
        raise RuntimeError(f"h_nominal missing in {num_file_path}")
    if not h_den_nom:
        raise RuntimeError(f"h_nominal missing in {den_file_path}")

    h_eff_nom = make_efficiency_hist(h_num_nom, h_den_nom, "h_nominal", binomial=binomial)

    num_pm, den_pm, num_one, den_one, common_pm, common_one = discover_variations(f_num, f_den)

    os.makedirs(os.path.dirname(out_file_path), exist_ok=True)
    f_out = ROOT.TFile(out_file_path, "RECREATE")

    write_hist(f_out, h_eff_nom)

    print(f"\nWriting: {out_file_path}")
    print(f"  nominal efficiency integral = {h_eff_nom.Integral():.6f}")

    all_up_hists   = []
    all_down_hists = []

    # ----------------------------------------------------------------------
    # Two-sided systematics: Top, QCD_W, ...
    # ----------------------------------------------------------------------
    for proc, plusminus in common_pm:
        h_num_var = get_safe_clone(f_num, num_pm[(proc, plusminus)])
        h_den_var = get_safe_clone(f_den, den_pm[(proc, plusminus)])

        if not h_num_var or not h_den_var:
            continue

        h_eff_var = make_efficiency_hist(
            h_num_var,
            h_den_var,
            f"h_{proc}_{plusminus}_sum",
            binomial=binomial,
        )

        h_delta = make_delta_hist(
            h_eff_var,
            h_eff_nom,
            f"h_{proc}_{plusminus}_delta"
        )

        h_up, h_down = split_delta_hist(
            h_delta,
            f"h_{proc}_{plusminus}_up",
            f"h_{proc}_{plusminus}_down"
        )

        all_up_hists.append(h_up)
        all_down_hists.append(h_down)

        write_hist(f_out, h_eff_var)
        write_hist(f_out, h_delta)
        if hist_has_nonzero_content(h_up):
            write_hist(f_out, h_up)
        if hist_has_nonzero_content(h_down):
            write_hist(f_out, h_down)

        print(
            f"  [{proc} {plusminus}] "
            f"eff_integral={h_eff_var.Integral():+.6f} "
            f"delta_integral={h_delta.Integral():+.6f}"
        )

    # ----------------------------------------------------------------------
    # One-sided systematics: top_reweighting, ...
    # ----------------------------------------------------------------------
    for proc in common_one:
        h_num_var = get_safe_clone(f_num, num_one[proc])
        h_den_var = get_safe_clone(f_den, den_one[proc])

        if not h_num_var or not h_den_var:
            continue

        h_eff_var = make_efficiency_hist(
            h_num_var,
            h_den_var,
            f"h_{proc}_sum",
            binomial=binomial,
        )

        h_delta = make_delta_hist(
            h_eff_var,
            h_eff_nom,
            f"h_{proc}_delta"
        )

        h_up, h_down = split_delta_hist(
            h_delta,
            f"h_{proc}_up",
            f"h_{proc}_down"
        )

        all_up_hists.append(h_up)
        all_down_hists.append(h_down)

        write_hist(f_out, h_eff_var)
        write_hist(f_out, h_delta)
        if hist_has_nonzero_content(h_up):
            write_hist(f_out, h_up)
        if hist_has_nonzero_content(h_down):
            write_hist(f_out, h_down)

        print(
            f"  [{proc}] "
            f"eff_integral={h_eff_var.Integral():+.6f} "
            f"delta_integral={h_delta.Integral():+.6f}"
        )

    # ----------------------------------------------------------------------
    # Total quadrature uncertainty
    # ----------------------------------------------------------------------
    h_total_plus, h_total_minus, h_total_sum = make_total_uncertainty(
        h_eff_nom, all_up_hists, all_down_hists
    )
    write_hist(f_out, h_total_plus)
    write_hist(f_out, h_total_minus)
    write_hist(f_out, h_total_sum)

    print(
        f"  [total] "
        f"plus_integral={h_total_plus.Integral():+.6f}  "
        f"minus_integral={h_total_minus.Integral():+.6f}"
    )

    f_out.Close()
    f_num.Close()
    f_den.Close()

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    for channel, era in CONFIGS:
        in_dir  = os.path.join("rootfiles", "uncertainties",     f"{channel}_{era}")
        out_dir = os.path.join("rootfiles", "eff_uncertainties", f"{channel}_{era}")

        mc_num_file   = os.path.join(in_dir, "mc_numerator.root")
        mc_den_file   = os.path.join(in_dir, "mc_denominator.root")
        data_num_file = os.path.join(in_dir, "data_numerator.root")
        data_den_file = os.path.join(in_dir, "data_denominator.root")

        mc_out_file   = os.path.join(out_dir, "mc_eff.root")
        data_out_file = os.path.join(out_dir, "data_eff.root")

        print("\n" + "=" * 72)
        print(f"Channel: {channel}   Era: {era}")
        print("=" * 72)

        build_efficiency_uncertainty_file(
            mc_num_file,
            mc_den_file,
            mc_out_file
        )

        build_efficiency_uncertainty_file(
            data_num_file,
            data_den_file,
            data_out_file,
            binomial=False,
        )

    print("\nDone.")