#!/usr/bin/env python3
from plotting import plot_histogram, plot_eff_with_sf
import ROOT

region   = "sele_EE"             # EDIT
name     = "Single Electron CR" # EDIT
rootfile = f"rootfiles/eff_{region}.root"
plot_dir = f"plots_tagging/{region}" 
xtitle   = "FatJet p_{T} [GeV]"

# tag/all counts
for histname, label, output_name in [
    (f"h_mc_tag_{region}",   "MC Tagged",   "mc_tag"),
    (f"h_mc_all_{region}",   "MC All",      "mc_all"),
    (f"h_data_tag_{region}", "Data Tagged", "data_tag"),
    (f"h_data_all_{region}", "Data All",    "data_all"),
]:
    plot_histogram(
        rootfile=rootfile,
        histname=histname,
        title=f"{label} ({name})",
        xtitle=xtitle,
        output_name=output_name,
        output_dir=plot_dir,
        color=ROOT.kBlue+1,
    )
    
# efficiencies and sf
for histname, label, ytitle, ymin, ymax, output_name in [
    (f"h_mc_eff_{region}",   "MC Efficiency",   "Efficiency",   0, 1.0, "mc_eff"),
    (f"h_data_eff_{region}", "Data Efficiency", "Efficiency",   0, 1.0, "data_eff"),
    (f"h_sf_{region}",       "Scale Factor",    "Scale Factor", 0, 1.5, "sf"),
]:
    plot_histogram(
        rootfile=rootfile,
        histname=histname,
        title=f"{label} ({name})",
        xtitle=xtitle,
        ytitle=ytitle,
        output_name=output_name,
        output_dir=plot_dir,
        ymin=ymin,
        ymax=ymax,
    )

# combined
plot_eff_with_sf(
    rootfile=rootfile,
    region=region,
    title=f"V-Tagging Efficiency ({name})",
    output_name="combined_eff_sf",
    output_dir=plot_dir,
)