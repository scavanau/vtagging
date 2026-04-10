#!/usr/bin/env python3
import os
import ROOT
from tagging_eff import write_file
ROOT.gROOT.SetBatch(True)
ROOT.TH1.SetDefaultSumw2(True)

def add_histograms(hist_list, new_name):
    if not hist_list:
        return None
    h_sum = hist_list[0].Clone(new_name)
    h_sum.SetDirectory(0)
    for h in hist_list[1:]:
        h_sum.Add(h)
    return h_sum

def compute_efficiency(h_tag, h_all, name):
    h_eff = h_tag.Clone(name)
    h_eff.SetDirectory(0)
    h_eff.Divide(h_tag, h_all, 1.0, 1.0, "B")
    return h_eff

def compute_scale_factor(h_data_eff, h_mc_eff, name):
    # Note: tagging_eff.compute_sf is file-based; this operates directly on histograms
    h_sf = h_data_eff.Clone(name)
    h_sf.SetDirectory(0)
    h_sf.Divide(h_data_eff, h_mc_eff)
    return h_sf

def combine_regions(region_list, output_region, input_dir="rootfiles", output_dir="rootfiles"):
    files = [
        ROOT.TFile.Open(os.path.join(input_dir, f"eff_{r}.root"))
        for r in region_list
    ]

    def collect(hist_type):
        return [
            f.Get(f"{hist_type}_{r}")
            for f, r in zip(files, region_list)
        ]

    h_mc_tag   = add_histograms(collect("h_mc_tag"),   f"h_mc_tag_{output_region}")
    h_mc_all   = add_histograms(collect("h_mc_all"),   f"h_mc_all_{output_region}")
    h_data_tag = add_histograms(collect("h_data_tag"), f"h_data_tag_{output_region}")
    h_data_all = add_histograms(collect("h_data_all"), f"h_data_all_{output_region}")

    for f in files:
        f.Close()

    h_mc_eff   = compute_efficiency(h_mc_tag,   h_mc_all,   f"h_mc_eff_{output_region}")
    h_data_eff = compute_efficiency(h_data_tag, h_data_all, f"h_data_eff_{output_region}")
    h_sf       = compute_scale_factor(h_data_eff, h_mc_eff, f"h_sf_{output_region}")

    write_file(
        output_region,
        {
            h_mc_tag.GetName():   h_mc_tag,
            h_mc_all.GetName():   h_mc_all,
            h_data_tag.GetName(): h_data_tag,
            h_data_all.GetName(): h_data_all,
            h_mc_eff.GetName():   h_mc_eff,
            h_data_eff.GetName(): h_data_eff,
            h_sf.GetName():       h_sf,
        }
    )

if __name__ == "__main__":
    combine_regions(
        ["smu_EE", "sele_EE"],  # EDIT
        "slep_EE"
    )
    print("Done.")