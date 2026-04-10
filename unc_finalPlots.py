#!/usr/bin/env python3
import ROOT
import os
from tagging_eff_unc import open_root, get_safe_clone
from plotting import plot_eff_sf_with_uncertainty, plot_eff_with_uncertainty

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)

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


def negate_hist(h):
    """Return a clone with all bin contents negated.

    h_total_delta_minus stores negative magnitudes; make_uncertainty_band
    passes them directly as TGraphAsymmErrors eyl which must be positive.
    """
    h_neg = h.Clone(h.GetName() + "_neg")
    h_neg.SetDirectory(0)
    for i in range(0, h_neg.GetNbinsX() + 2):
        h_neg.SetBinContent(i, -h_neg.GetBinContent(i))
    return h_neg


if __name__ == "__main__":
    for channel, era in CONFIGS:
        eff_dir = os.path.join("rootfiles", "eff_uncertainties", f"{channel}_{era}")
        sf_dir  = os.path.join("rootfiles", "sf_uncertainties",  f"{channel}_{era}")

        mc_eff_file   = os.path.join(eff_dir, "mc_eff.root")
        data_eff_file = os.path.join(eff_dir, "data_eff.root")
        sf_file       = os.path.join(sf_dir,  "sf.root")

        print(f"\n{'='*60}")
        print(f"Channel: {channel}   Era: {era}")
        print('='*60)

        f_mc   = open_root(mc_eff_file)
        f_data = open_root(data_eff_file)
        f_sf   = open_root(sf_file)

        h_mc_nom    = get_safe_clone(f_mc,   "h_nominal")
        h_mc_up     = get_safe_clone(f_mc,   "h_total_delta_plus")
        h_mc_down   = negate_hist(get_safe_clone(f_mc,   "h_total_delta_minus"))

        h_data_nom  = get_safe_clone(f_data, "h_nominal")
        h_data_up   = get_safe_clone(f_data, "h_total_delta_plus")
        h_data_down = negate_hist(get_safe_clone(f_data, "h_total_delta_minus"))

        h_sf_nom    = get_safe_clone(f_sf, "h_nominal")
        h_sf_up     = get_safe_clone(f_sf, "h_total_delta_plus")
        h_sf_down   = negate_hist(get_safe_clone(f_sf, "h_total_delta_minus"))

        f_mc.Close()
        f_data.Close()
        f_sf.Close()

        _channel_label = {
            "smu":  "Single Muon CR",
            "sele": "Single Electron CR",
            "slep": "Single Lepton CR",
        }
        _era_label = {"22": "2022", "22EE": "2022EE", "23": "2023", "23BPix": "2023BPix"}
        label    = f"{_channel_label[channel]} {_era_label[era]}"
        out_base = f"{channel}_{era}"
        out_dir  = "plots_tagging/final_plots"

        # Combined efficiency + scale factor plot (two-pad)
        plot_eff_sf_with_uncertainty(
            h_mc_nom, h_data_nom, h_sf_nom,
            h_mc_up,   h_mc_down,
            h_data_up, h_data_down,
            h_sf_up,   h_sf_down,
            region=out_base,
            name=label,
            output_name=f"eff_sf_unc_{out_base}",
            output_dir=out_dir,
        )

        # Efficiency-only plot
        plot_eff_with_uncertainty(
            h_mc_nom, h_data_nom,
            h_mc_up,   h_mc_down,
            h_data_up, h_data_down,
            region=out_base,
            name=label,
            output_name=f"eff_unc_{out_base}",
            output_dir=out_dir,
        )

    print("\nDone.")
