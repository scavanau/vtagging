#!/usr/bin/env python3
import ROOT
import os
from tagging_compute_unc import (
    make_delta_hist,
    split_delta_hist,
    hist_has_nonzero_content,
    write_hist,
)
from tagging_eff_unc import (
    open_root,
    get_safe_clone,
    discover_variations,
    make_total_uncertainty,
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
# SF helper
# ---------------------------------------------------------------------------

def make_sf_hist(h_data, h_mc, name):
    """
    SF = data_eff / mc_eff, plain ratio (no binomial — neither is a subset
    of the other). Bins where mc_eff == 0 are set to 0.
    """
    h_sf = h_data.Clone(name)
    h_sf.SetDirectory(0)
    h_sf.Divide(h_data, h_mc)
    return h_sf

# ---------------------------------------------------------------------------
# writer
# ---------------------------------------------------------------------------

def build_sf_uncertainty_file(mc_eff_path, data_eff_path, out_file_path):
    f_mc   = open_root(mc_eff_path)
    f_data = open_root(data_eff_path)

    h_mc_nom   = get_safe_clone(f_mc,   "h_nominal")
    h_data_nom = get_safe_clone(f_data, "h_nominal")

    if not h_mc_nom:
        raise RuntimeError(f"h_nominal missing in {mc_eff_path}")
    if not h_data_nom:
        raise RuntimeError(f"h_nominal missing in {data_eff_path}")

    h_sf_nom = make_sf_hist(h_data_nom, h_mc_nom, "h_nominal")

    # discover_variations expects (f_num, f_den); pass (f_data, f_mc) so that
    # data_pm plays the role of num and mc_pm plays the role of den.
    # Use the union of variations: if one side is missing, fall back to its
    # nominal (e.g. QCD_W shifts data eff but not MC eff).
    data_pm, mc_pm, data_one, mc_one, _, _ = discover_variations(f_data, f_mc)

    # exclude "total" — h_total_sum in the eff files matches the one-sided
    # pattern but is not a systematic; it's the pre-computed total unc band.
    _RESERVED = {"total"}

    all_pm  = sorted(set(data_pm.keys()) | set(mc_pm.keys()),  key=lambda x: (x[0], x[1]))
    all_one = sorted((set(data_one.keys()) | set(mc_one.keys())) - _RESERVED)

    os.makedirs(os.path.dirname(out_file_path), exist_ok=True)
    f_out = ROOT.TFile(out_file_path, "RECREATE")

    write_hist(f_out, h_sf_nom)

    print(f"\nWriting: {out_file_path}")
    print(f"  nominal SF integral = {h_sf_nom.Integral():.6f}")

    all_up_hists   = []
    all_down_hists = []

    # ----------------------------------------------------------------------
    # Two-sided systematics: Top, QCD_W, ...
    # ----------------------------------------------------------------------
    for proc, plusminus in all_pm:
        h_data_var = get_safe_clone(f_data, data_pm[(proc, plusminus)]) if (proc, plusminus) in data_pm else h_data_nom
        h_mc_var   = get_safe_clone(f_mc,   mc_pm[(proc, plusminus)])   if (proc, plusminus) in mc_pm   else h_mc_nom

        if not h_data_var or not h_mc_var:
            continue

        h_sf_var = make_sf_hist(h_data_var, h_mc_var, f"h_{proc}_{plusminus}_sum")

        h_delta = make_delta_hist(h_sf_var, h_sf_nom, f"h_{proc}_{plusminus}_delta")

        h_up, h_down = split_delta_hist(
            h_delta,
            f"h_{proc}_{plusminus}_up",
            f"h_{proc}_{plusminus}_down",
        )

        all_up_hists.append(h_up)
        all_down_hists.append(h_down)

        write_hist(f_out, h_sf_var)
        write_hist(f_out, h_delta)
        if hist_has_nonzero_content(h_up):
            write_hist(f_out, h_up)
        if hist_has_nonzero_content(h_down):
            write_hist(f_out, h_down)

        print(
            f"  [{proc} {plusminus}] "
            f"sf_integral={h_sf_var.Integral():+.6f}  "
            f"delta_integral={h_delta.Integral():+.6f}"
        )

    # ----------------------------------------------------------------------
    # One-sided systematics: top_reweighting, ...
    # ----------------------------------------------------------------------
    for proc in all_one:
        h_data_var = get_safe_clone(f_data, data_one[proc]) if proc in data_one else h_data_nom
        h_mc_var   = get_safe_clone(f_mc,   mc_one[proc])   if proc in mc_one   else h_mc_nom

        if not h_data_var or not h_mc_var:
            continue

        h_sf_var = make_sf_hist(h_data_var, h_mc_var, f"h_{proc}_sum")

        h_delta = make_delta_hist(h_sf_var, h_sf_nom, f"h_{proc}_delta")

        h_up, h_down = split_delta_hist(
            h_delta,
            f"h_{proc}_up",
            f"h_{proc}_down",
        )

        all_up_hists.append(h_up)
        all_down_hists.append(h_down)

        write_hist(f_out, h_sf_var)
        write_hist(f_out, h_delta)
        if hist_has_nonzero_content(h_up):
            write_hist(f_out, h_up)
        if hist_has_nonzero_content(h_down):
            write_hist(f_out, h_down)

        print(
            f"  [{proc}] "
            f"sf_integral={h_sf_var.Integral():+.6f}  "
            f"delta_integral={h_delta.Integral():+.6f}"
        )

    # ----------------------------------------------------------------------
    # Total quadrature uncertainty
    # ----------------------------------------------------------------------
    h_total_plus, h_total_minus, h_total_sum = make_total_uncertainty(
        h_sf_nom, all_up_hists, all_down_hists
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
    f_mc.Close()
    f_data.Close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    for channel, era in CONFIGS:
        eff_dir = os.path.join("rootfiles", "eff_uncertainties", f"{channel}_{era}")
        out_dir = os.path.join("rootfiles", "sf_uncertainties",  f"{channel}_{era}")

        mc_eff_file   = os.path.join(eff_dir, "mc_eff.root")
        data_eff_file = os.path.join(eff_dir, "data_eff.root")
        sf_out_file   = os.path.join(out_dir,  "sf.root")

        print("\n" + "=" * 72)
        print(f"Channel: {channel}   Era: {era}")
        print("=" * 72)

        build_sf_uncertainty_file(mc_eff_file, data_eff_file, sf_out_file)

    print("\nDone.")
