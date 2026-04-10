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

def sum_mc_from_files(*files, only_name=None):
    """Sum MC histograms across multiple files"""
    h_total = None
    for root_file in files:
        h = sum_mc_histograms(root_file, only_name=only_name)
        if h_total is None:
            h_total = h
        else:
            h_total.Add(h)
    return h_total

def sum_data_obs_from_files(*files):
    """Sum data_obs histograms across multiple files"""
    h_total = None
    for root_file in files:
        f = ROOT.TFile.Open(root_file)
        h = f.Get("data_obs")
        h = h.Clone()
        h.SetDirectory(0)
        f.Close()
        if h_total is None:
            h_total = h
        else:
            h_total.Add(h)
    return h_total

def mc_eff(num_file, den_tagged_file, den_untagged_file, region):
    """Denominator matched+tagged + matched+untagged"""
    h_tag = sum_mc_histograms(num_file)
    h_all = sum_mc_from_files(den_tagged_file, den_untagged_file)
    #h_tag = sum_mc_histograms(num_file, only_name="Top") #Change here for individiual sample histogram
    #h_all = sum_mc_from_files(den_tagged_file, den_untagged_file, only_name="Top")

    # Rename
    h_tag.SetName(f"h_mc_tag_{region}")
    h_all.SetName(f"h_mc_all_{region}")
    # Efficiency
    h_eff = h_tag.Clone(f"h_mc_eff_{region}")
    h_eff.SetDirectory(0)
    h_eff.Divide(h_tag, h_all, 1.0, 1.0, "B")
    return h_eff, h_tag, h_all

def data_minus_mc(data_file):
    """Data and MC now both come from the unmatched file"""
    f = ROOT.TFile.Open(data_file)
    h_data = f.Get("data_obs")
    h_data = h_data.Clone()
    h_data.SetDirectory(0)
    f.Close()

    h_mc = sum_mc_histograms(data_file)

    h_matched = h_data.Clone()
    h_matched.Add(h_mc, -1.0)
    return h_matched

def data_minus_mc_from_files(data_files):
    """Same as data_minus_mc but sums across multiple files"""
    h_data = sum_data_obs_from_files(*data_files)
    h_mc   = sum_mc_from_files(*data_files)

    h_matched = h_data.Clone()
    h_matched.Add(h_mc, -1.0)
    return h_matched

def data_eff(num_file, den_tagged_file, den_untagged_file, region):
    """Numerator: data_obs minus MC from unmatched+tagged"""
    h_tag = data_minus_mc(num_file)
    """Denominator: (data_obs tagged + untagged) minus (MC tagged + untagged)"""
    h_all = data_minus_mc_from_files([den_tagged_file, den_untagged_file])

    h_tag.SetName(f"h_data_tag_{region}")
    h_all.SetName(f"h_data_all_{region}")

    # Efficiency
    h_eff = h_tag.Clone(f"h_data_eff_{region}")
    h_eff.SetDirectory(0)
    h_eff.Divide(h_tag, h_all, 1.0, 1.0, "B")
    return h_eff, h_tag, h_all

def write_file(region, histograms, output_dir="rootfiles"):
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"eff_{region}.root") #Running individual samples change path
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

    region = "sele_EE" # smu , sele , smu_EE , sele_EE , slep , slep_EE

    #for_efficiency ==> no top reweighting, 250Gev
    #top_reweighted ==> top reweighting, 250GeV
    #CHANGE FILE PATHS FOR DIFFERENT REGIONS AND YEARS
    # file paths
    matched_tagged     = "pt_lowered/matched/Run3Summer22EE/NanoAODv12/singleElectron_CR_MonoV/plots/root/monov_FatJet_pt_forefficiency_tagged.root"
    matched_untagged   = "pt_lowered/matched/Run3Summer22EE/NanoAODv12/singleElectron_CR_MonoV/plots/root/monov_FatJet_pt_forefficiency_untagged.root"
    unmatched_tagged   = "pt_lowered/unmatched/Run3Summer22EE/NanoAODv12/singleElectron_CR_MonoV/plots/root/monov_FatJet_pt_forefficiency_tagged.root"
    unmatched_untagged = "pt_lowered/unmatched/Run3Summer22EE/NanoAODv12/singleElectron_CR_MonoV/plots/root/monov_FatJet_pt_forefficiency_untagged.root"

    # mc
    h_mc_eff, h_mc_tag, h_mc_all = mc_eff(
        matched_tagged,    # numerator
        matched_tagged,    # denominator tagged
        matched_untagged,  # denominator untagged
        region
    )

    # data
    h_data_eff, h_data_tag, h_data_all = data_eff(
        unmatched_tagged,    # numerator (data_obs + MC from same file)
        unmatched_tagged,    # denominator tagged
        unmatched_untagged,  # denominator untagged
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

    compute_sf("sele_EE")
    print("Done.")