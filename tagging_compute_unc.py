#!/usr/bin/env python3
import ROOT
import os
ROOT.gROOT.SetBatch(True)
ROOT.TH1.SetDefaultSumw2(True)
ROOT.gStyle.SetOptStat(0)

SYSTEMATICS = [
    ("Top",   0.05),   # 5% Top cross section uncertainty
    #("QCD_W", 0.02),   # 2% W+jets cross section uncertainty
]
ZERO_TOL = 1e-12
TOP_REWEIGHT_NAME = "top_reweighting"

# Each entry:
# (
#   channel, era,
#   nominal_CR_directory, nominal_subdir,
#   reweight_CR_directory, reweight_subdir,
# )
CONFIGS = [
    ("smu",  "22",     "singleMuon_CR_MonoV",              "plots_noreweight/root", "singleMuon_CR_MonoV",              "plots/root"),
    ("smu",  "22EE",   "singleMuon_CR_MonoV",              "plots_noreweight/root", "singleMuon_CR_MonoV",              "plots/root"),
    ("smu",  "23",     "singleMuon_CR_MonoV",              "plots_noreweight/root", "singleMuon_CR_MonoV",              "plots/root"),
    ("smu",  "23BPix", "singleMuon_CR_MonoV",              "plots_noreweight/root", "singleMuon_CR_MonoV",              "plots/root"),
    ("sele", "22",     "singleElectron_CR_MonoV",          "plots_noreweight/root", "singleElectron_CR_MonoV",          "plots/root"),
    ("sele", "22EE",   "singleElectron_CR_MonoV",          "plots_noreweight/root", "singleElectron_CR_MonoV",          "plots/root"),
    ("sele", "23",     "singleElectron_CR_MonoV",          "plots_noreweight/root", "singleElectron_CR_MonoV",          "plots/root"),
    ("sele", "23BPix", "singleElectron_CR_MonoV",          "plots_noreweight/root", "singleElectron_CR_MonoV",          "plots/root"),
    ("slep", "22",     "singleLepton_CR_MonoV_noreweight", "",                      "singleLepton_CR_MonoV",            ""),
    ("slep", "22EE",   "singleLepton_CR_MonoV_noreweight", "",                      "singleLepton_CR_MonoV",            ""),
    ("slep", "23",     "singleLepton_CR_MonoV_noreweight", "",                      "singleLepton_CR_MonoV",            ""),
    ("slep", "23BPix", "singleLepton_CR_MonoV_noreweight", "",                      "singleLepton_CR_MonoV",            ""),
]

def get_files(era, cr_dir, subdir):
    full_era = f"Run3Summer{era}"

    def base(match):
        parts = ["pt_lowered_corr", match, full_era, "NanoAODv12", cr_dir]
        if subdir:
            parts.append(subdir)
        return "/".join(parts)

    return {
        "matched_tagged":     f"{base('matched')}/monov_FatJet_pt_forefficiency_tagged.root",
        "matched_untagged":   f"{base('matched')}/monov_FatJet_pt_forefficiency_untagged.root",
        "unmatched_tagged":   f"{base('unmatched')}/monov_FatJet_pt_forefficiency_tagged.root",
        "unmatched_untagged": f"{base('unmatched')}/monov_FatJet_pt_forefficiency_untagged.root",
    }

def require_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing ROOT file: {path}")
def all_files_exist(paths):
    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        for p in missing:
            print(f"  [skip] Missing file: {p}")
        return False
    return True

# ---------------------------------------------------------------------------
# Sum histogram functions for mc and data numerators/denominators
# ---------------------------------------------------------------------------

def sum_mc_histograms(root_file, proc_scales=None):
    """Sum all MC histograms in a single file, optionally scaling one process."""
    f = ROOT.TFile.Open(root_file)
    h_sum = None
    for key in f.GetListOfKeys():
        name  = key.GetName()
        lname = name.lower()
        if "data_obs" in lname or "stack" in lname:
            continue

        h = f.Get(name)
        if not isinstance(h, ROOT.TH1):
            continue

        h_clone = h.Clone()
        h_clone.SetDirectory(0)
        if proc_scales:
            for proc, scale in proc_scales.items():
                if proc in name:
                    h_clone.Scale(scale)
                    break
        if h_sum is None:
            h_sum = h_clone
        else:
            h_sum.Add(h_clone)
    f.Close()
    return h_sum

def sum_mc_from_files(*files, proc_scales=None):
    """Sum MC histograms across multiple files."""
    h_total = None
    for root_file in files:
        h = sum_mc_histograms(root_file, proc_scales=proc_scales)
        if h_total is None:
            h_total = h
        else:
            h_total.Add(h)
    return h_total

def get_data_obs(root_file):
    """Return data_obs histogram from a file."""
    f = ROOT.TFile.Open(root_file)
    h = f.Get("data_obs").Clone()
    h.SetDirectory(0)
    f.Close()
    return h

def data_minus_mc(*files, proc_scales=None):
    """Sum data_obs across files then subtract the MC sum."""
    h_data = None
    for root_file in files:
        h = get_data_obs(root_file)
        if h_data is None:
            h_data = h
        else:
            h_data.Add(h)
    h_mc = sum_mc_from_files(*files, proc_scales=proc_scales)
    h_data.Add(h_mc, -1.0)
    return h_data

def clone_reset(template, name):
    h = template.Clone(name)
    h.SetDirectory(0)
    h.Reset("ICES")
    return h

def make_delta_hist(h_varied, h_nominal, name):
    """Return signed delta histogram: delta = varied - nominal."""
    h_delta = h_varied.Clone(name)
    h_delta.SetDirectory(0)
    h_delta.Add(h_nominal, -1.0)

    # Keep the bin contents only; downstream code should use the delta values.
    for ibin in range(0, h_delta.GetNbinsX() + 2):
        h_delta.SetBinError(ibin, 0.0)
    return h_delta

def split_delta_hist(h_delta, up_name, down_name):
    """
    Split a signed delta histogram into two signed histograms.
      up(bin)   = delta(bin) if delta(bin) > 0 else 0
      down(bin) = delta(bin) if delta(bin) < 0 else 0
    The stored values keep their original sign, so down bins are negative.
    There will be two deltas per systematic: one for the "up" variation and one for the "down" variation.
    """
    h_up = clone_reset(h_delta, up_name)
    h_down = clone_reset(h_delta, down_name)

    for ibin in range(0, h_delta.GetNbinsX() + 2):
        val = h_delta.GetBinContent(ibin)
        if val > 0.0:
            h_up.SetBinContent(ibin, val)
        elif val < 0.0:
            h_down.SetBinContent(ibin, val)
        h_up.SetBinError(ibin, 0.0)
        h_down.SetBinError(ibin, 0.0)
    return h_up, h_down

def hist_has_nonzero_content(hist, tol=ZERO_TOL):
    for ibin in range(0, hist.GetNbinsX() + 2):
        if abs(hist.GetBinContent(ibin)) > tol:
            return True
    return False

# ---------------------------------------------------------------------------
# write one output file for a given quantity
# ---------------------------------------------------------------------------

def write_hist(f_out, hist):
    f_out.cd()
    hist.Write()

def write_two_sided_systematic(f_out, proc, frac, nominal_hist, varied_fn):
    """
    For a two-sided systematic like Top or QCD_W:
      1) build the + variation sum histogram and save it
      2) build delta_plus = plus_sum - nominal and save it
      3) split delta_plus into plus_up / plus_down and save them
      4) repeat for the - variation
    """
    for scale_label, scale_val in (("plus", 1.0 + frac), ("minus", 1.0 - frac)):
        varied_sum = varied_fn({proc: scale_val})
        varied_sum.SetName(f"h_{proc}_{scale_label}_sum")

        delta_hist = make_delta_hist(
            varied_sum,
            nominal_hist,
            f"h_{proc}_{scale_label}_delta",
        )
        up_hist, down_hist = split_delta_hist(
            delta_hist,
            f"h_{proc}_{scale_label}_up",
            f"h_{proc}_{scale_label}_down",
        )

        if not hist_has_nonzero_content(delta_hist):
            print(f"  [{proc} {scale_label}] no effect -> skipping write")
            continue

        write_hist(f_out, varied_sum)
        write_hist(f_out, delta_hist)
        if hist_has_nonzero_content(up_hist):
            write_hist(f_out, up_hist)
        if hist_has_nonzero_content(down_hist):
            write_hist(f_out, down_hist)

        print(
            f"  [{proc} {scale_label}] scale={scale_val:.4f} "
            f"delta_integral={delta_hist.Integral():+.6f}"
        )


def write_one_sided_systematic(f_out, syst_name, nominal_hist, varied_fn):
    """
    For a one-sided systematic like top reweighting:
      1) build the varied sum histogram and save it
      2) build delta = varied_sum - nominal and save it
      3) split delta into up / down and save them
    """
    varied_sum = varied_fn()
    varied_sum.SetName(f"h_{syst_name}_sum")

    delta_hist = make_delta_hist(varied_sum, nominal_hist, f"h_{syst_name}_delta")
    up_hist, down_hist = split_delta_hist(
        delta_hist,
        f"h_{syst_name}_up",
        f"h_{syst_name}_down",
    )

    if not hist_has_nonzero_content(delta_hist):
        print(f"  [{syst_name}] no effect -> skipping write")
        return

    write_hist(f_out, varied_sum)
    write_hist(f_out, delta_hist)
    if hist_has_nonzero_content(up_hist):
        write_hist(f_out, up_hist)
    if hist_has_nonzero_content(down_hist):
        write_hist(f_out, down_hist)

    print(f"  [{syst_name}] delta_integral={delta_hist.Integral():+.6f}")


def write_uncertainty_file(label, nominal_fn, varied_fn, output_dir, one_sided_systematics=None):
    """
    Write one output ROOT file for a quantity such as mc_numerator.
    Saved objects:
      h_nominal
      h_<proc>_plus_sum
      h_<proc>_plus_delta => difference of sum histogram with nominal, signed
      h_<proc>_plus_up
      h_<proc>_plus_down
      h_<proc>_minus_sum
      h_<proc>_minus_delta
      h_<proc>_minus_up
      h_<proc>_minus_down
      h_top_reweight_sum
      h_top_reweight_delta
      h_top_reweight_up
      h_top_reweight_down

    The up/down histograms store the signed delta itself, split by sign.
         This can be to check if some bins move up and some move down
    """
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{label}.root")
    f_out = ROOT.TFile(out_path, "RECREATE")

    h_nominal = nominal_fn()
    h_nominal.SetName("h_nominal")
    write_hist(f_out, h_nominal)

    print(f"\n=== {label} ===")
    print(f"  nominal integral = {h_nominal.Integral():.6f}")

    for proc, frac in SYSTEMATICS:
        write_two_sided_systematic(f_out, proc, frac, h_nominal, varied_fn)

    if one_sided_systematics:
        for syst_name, syst_fn in one_sided_systematics:
            write_one_sided_systematic(f_out, syst_name, h_nominal, syst_fn)

    f_out.Close()
    print(f"  written: {out_path}")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    for (
        channel, era,
        nominal_cr_dir, nominal_subdir,
        reweight_cr_dir, reweight_subdir,
    ) in CONFIGS:
        nominal_files = get_files(era, nominal_cr_dir, nominal_subdir)
        reweight_files = get_files(era, reweight_cr_dir, reweight_subdir)

        mt_nom = nominal_files["matched_tagged"]
        mu_nom = nominal_files["matched_untagged"]
        ut_nom = nominal_files["unmatched_tagged"]
        uu_nom = nominal_files["unmatched_untagged"]

        mt_rw = reweight_files["matched_tagged"]
        mu_rw = reweight_files["matched_untagged"]
        ut_rw = reweight_files["unmatched_tagged"]
        uu_rw = reweight_files["unmatched_untagged"]

        out_dir = os.path.join("rootfiles", "uncertainties", f"{channel}_{era}")

        print(f"\n{'=' * 72}")
        print(f"Channel: {channel}   Era: {era}")
        print(f"Nominal CR path:   {nominal_cr_dir} / {nominal_subdir}")
        print(f"Reweighted path:   {reweight_cr_dir} / {reweight_subdir}")
        print(f"{'=' * 72}")

        extra_mc_num = []
        if all_files_exist([mt_rw]):
            extra_mc_num.append((TOP_REWEIGHT_NAME, lambda mt_rw=mt_rw: sum_mc_histograms(mt_rw)))

        extra_mc_den = []
        if all_files_exist([mt_rw, mu_rw]):
            extra_mc_den.append((TOP_REWEIGHT_NAME, lambda mt_rw=mt_rw, mu_rw=mu_rw: sum_mc_from_files(mt_rw, mu_rw)))

        extra_data_num = []
        if all_files_exist([ut_rw]):
            extra_data_num.append((TOP_REWEIGHT_NAME, lambda ut_rw=ut_rw: data_minus_mc(ut_rw)))

        extra_data_den = []
        if all_files_exist([ut_rw, uu_rw]):
            extra_data_den.append((TOP_REWEIGHT_NAME, lambda ut_rw=ut_rw, uu_rw=uu_rw: data_minus_mc(ut_rw, uu_rw)))

        write_uncertainty_file(
            label="mc_numerator",
            nominal_fn=lambda mt_nom=mt_nom: sum_mc_histograms(mt_nom),
            varied_fn=lambda ps, mt_nom=mt_nom: sum_mc_histograms(mt_nom, proc_scales=ps),
            output_dir=out_dir,
            one_sided_systematics=extra_mc_num,
        )

        write_uncertainty_file(
            label="mc_denominator",
            nominal_fn=lambda mt_nom=mt_nom, mu_nom=mu_nom: sum_mc_from_files(mt_nom, mu_nom),
            varied_fn=lambda ps, mt_nom=mt_nom, mu_nom=mu_nom: sum_mc_from_files(mt_nom, mu_nom, proc_scales=ps),
            output_dir=out_dir,
            one_sided_systematics=extra_mc_den,
        )

        write_uncertainty_file(
            label="data_numerator",
            nominal_fn=lambda ut_nom=ut_nom: data_minus_mc(ut_nom),
            varied_fn=lambda ps, ut_nom=ut_nom: data_minus_mc(ut_nom, proc_scales=ps),
            output_dir=out_dir,
            one_sided_systematics=extra_data_num,
        )

        write_uncertainty_file(
            label="data_denominator",
            nominal_fn=lambda ut_nom=ut_nom, uu_nom=uu_nom: data_minus_mc(ut_nom, uu_nom),
            varied_fn=lambda ps, ut_nom=ut_nom, uu_nom=uu_nom: data_minus_mc(ut_nom, uu_nom, proc_scales=ps),
            output_dir=out_dir,
            one_sided_systematics=extra_data_den,
        )

    print("\nDone.")