from plotting import plot_histogram
from plotting import plot_basic
from plotting import plot_eff_with_sf

region = "smu" #Change based of region you want to plot
name = "Single Muon CR"
rootfile = f"rootfiles/eff_{region}.root"
plot_basic(
    rootfile=rootfile,
    histname=f"h_mc_tag_{region}",
    title=f"MC Tagged ({name})",
    xtitle="FatJet p_{T} [GeV]",
    output_name=f"{region}_mc_tag",
)

plot_basic(
    rootfile=rootfile,
    histname=f"h_mc_all_{region}",
    title=f"MC All ({name})",
    xtitle="FatJet p_{T} [GeV]",
    output_name=f"{region}_mc_all",
)

plot_basic(
    rootfile=rootfile,
    histname=f"h_data_tag_{region}",
    title=f"Data Tagged ({name})",
    xtitle="FatJet p_{T} [GeV]",
    output_name=f"{region}_data_tag",
)

plot_basic(
    rootfile=rootfile,
    histname=f"h_data_all_{region}",
    title=f"Data All ({name})",
    xtitle="FatJet p_{T} [GeV]",
    output_name=f"{region}_data_all",
)

# Plot MC efficiency
plot_histogram(
    rootfile=rootfile,
    histname=f"h_mc_eff_{region}",
    title=f"MC Efficiency ({name})",
    xtitle="FatJet p_{T} [GeV]",
    ytitle="Efficiency",
    output_name=f"{region}_mc_eff",
    ymin=0,
    ymax=1,
)

# Plot Data efficiency
plot_histogram(
    rootfile=rootfile,
    histname=f"h_data_eff_{region}",
    title=f"Data Efficiency ({name})",
    xtitle="FatJet p_{T} [GeV]",
    ytitle="Efficiency",
    output_name=f"{region}_data_eff",
    ymin=0,
    ymax=1,
)

# Plot Scale Factor
plot_histogram(
    rootfile=rootfile,
    histname=f"h_sf_{region}",
    title=f"Scale Factor ({name})",
    xtitle="FatJet p_{T} [GeV]",
    ytitle="Scale Factor",
    output_name=f"{region}_sf",
    ymin=0,
    ymax=1,
)

# Combination efficiencies with sf as ratio
plot_eff_with_sf(
    rootfile=rootfile,
    region=region,
    title=f"V-Tagging Efficiency ({name})",
    output_name=f"{region}_combined_eff_sf",
)