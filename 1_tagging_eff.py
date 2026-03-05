#!/usr/bin/env python3
import ROOT
import os
from array import array

ROOT.gROOT.SetBatch(True)
ROOT.TH1.SetDefaultSumw2(True)
ROOT.gStyle.SetOptStat(0)

def sum_mc_histograms(root_file, only_name=None):
    f = ROOT.TFile.Open(root_file)
    h_sum = None
    
    only_l = only_name.lower() if only_name else None #Use for look at specific sample histogram

    for key in f.GetListOfKeys():
        name = key.GetName()
        lname = name.lower()

        if "data_obs" in lname:
            continue
        if "stack" in lname:
            continue

        if only_l and only_l not in lname:
            continue

        h = f.Get(name)
        if not isinstance(h, ROOT.TH1):
            continue

        if h_sum is None:
            h_sum = h.Clone()
            h_sum.SetDirectory(0)
        else:
            h_sum.Add(h)

    f.Close()
    return h_sum

def mc_eff(num_file, den_file, region):
    h_tag = sum_mc_histograms(num_file)
    h_all = sum_mc_histograms(den_file)

    #h_tag = sum_mc_histograms(num_file, only_name="WW") #Change here for individiual sample histogram
    #h_all = sum_mc_histograms(den_file, only_name="WW")

    # Rename
    h_tag.SetName(f"h_mc_tag_{region}") #Change output names if running individual sample hists
    h_all.SetName(f"h_mc_all_{region}")

    # Efficiency
    h_eff = h_tag.Clone(f"h_mc_eff_{region}")
    h_eff.SetDirectory(0)
    h_eff.Divide(h_tag, h_all, 1.0, 1.0, "B")

    return h_eff, h_tag, h_all

def data_minus_mc(unmatched_file, data_file):
    h_mc_unmatched = sum_mc_histograms(unmatched_file)

    f_data = ROOT.TFile.Open(data_file)
    h_data = f_data.Get("data_obs")

    h_data = h_data.Clone()
    h_data.SetDirectory(0)

    f_data.Close()

    h_matched = h_data.Clone()
    h_matched.Add(h_mc_unmatched, -1.0)

    return h_matched

def data_eff(num_unmatched, num_data, den_unmatched, den_data, region):
    h_tag = data_minus_mc(num_unmatched, num_data)
    h_all = data_minus_mc(den_unmatched, den_data)

    h_tag.SetName(f"h_data_tag_{region}")
    h_all.SetName(f"h_data_all_{region}")

    # Efficiency
    h_eff = h_tag.Clone(f"h_data_eff_{region}")
    h_eff.SetDirectory(0)

    h_eff.Divide(h_tag, h_all, 1.0, 1.0, "B")

    return h_eff, h_tag, h_all

def write_file(region, histograms, output_dir="rootfiles"):
    import os
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    filepath = os.path.join(output_dir, f"eff_{region}.root")
    f_out = ROOT.TFile(filepath, "RECREATE")

    for name, hist in histograms.items():
        hist.SetName(name)
        hist.Write()

    f_out.Close()

def compute_sf(region, input_dir="rootfiles"):
    filepath = os.path.join(input_dir, f"eff_{region}.root")
    f = ROOT.TFile.Open(filepath, "UPDATE")

    h_data_eff = f.Get(f"h_data_eff_{region}")
    h_mc_eff   = f.Get(f"h_mc_eff_{region}")

    h_data_eff = h_data_eff.Clone()
    h_data_eff.SetDirectory(0)

    h_mc_eff = h_mc_eff.Clone()
    h_mc_eff.SetDirectory(0)

    # scale factor histogram
    h_sf = h_data_eff.Clone(f"h_sf_{region}")
    h_sf.SetDirectory(0)
    h_sf.Divide(h_data_eff, h_mc_eff)
    h_sf.Write()

    f.Close()

    print(f"Scale factor added to {filepath}")

if __name__ == "__main__":

    region = "smu" ###Change region if running for different region

    # file paths
    matched = "top_reweighted/matched/Run3Summer22/NanoAODv12/singleMuon_CR_MonoV/plots/root/monov_FatJet_pt_forefficiency.root"
    matched_tagged = "top_reweighted/matched+tagged/Run3Summer22/NanoAODv12/singleMuon_CR_MonoV/plots/root/monov_FatJet_pt_forefficiency.root"
    unmatched = "top_reweighted/unmatched/Run3Summer22/NanoAODv12/singleMuon_CR_MonoV/plots/root/monov_FatJet_pt_forefficiency.root"
    unmatched_tagged = "top_reweighted/unmatched+tagged/Run3Summer22/NanoAODv12/singleMuon_CR_MonoV/plots/root/monov_FatJet_pt_forefficiency.root"

    # mc
    h_mc_eff, h_mc_tag, h_mc_all = mc_eff(
        matched_tagged,   # numerator
        matched,          # denominator
        region
    )
    
    # data
    h_data_eff, h_data_tag, h_data_all = data_eff(
        unmatched_tagged,   # numerator unmatched
        matched_tagged,     # numerator data
        unmatched,          # denominator unmatched
        matched,            # denominator data
        region
    )
    
    write_file(
        region,
        {
            h_mc_eff.GetName(): h_mc_eff,
            h_mc_tag.GetName(): h_mc_tag,
            h_mc_all.GetName(): h_mc_all,
            h_data_eff.GetName(): h_data_eff,
            h_data_tag.GetName(): h_data_tag,
            h_data_all.GetName(): h_data_all,
        }
    )

    compute_sf("smu") ###Change region if running for different region
    print("Done.")