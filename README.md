Run the following scripts to compute and plot systematic uncertainties on the V-tagging efficiencies and scale factors for all regions and eras.

1. tagging_compute_unc.py — Starting from the control region FatJet pT histograms, computes nominal and systematically varied MC and data numerator/denominator histograms. Systematics included are defined based on either histogram name or separate file paths for top reweighting. Outputs to rootfiles/uncertainties/.

2. unc_plotting.py — Plots the signed delta (varied − nominal) for each systematic across the four quantities (MC/data numerator/denominator). Outputs to plots_tagging/uncertainties/.

3. tagging_eff_unc.py — Forms efficiency ratios from the Step 1 outputs and propagates uncertainties, including a quadrature sum over all systematics and statistical. Outputs to rootfiles/eff_uncertainties/.

4. unc_plotting_eff.py — Plots per-systematic efficiency deltas and the total uncertainty envelope for MC and data. Outputs to plots_tagging/eff_uncertainties/.

5. tagging_sf_unc.py — Computes SF = data_eff / mc_eff under each variation and propagates uncertainties in quadrature. Outputs to rootfiles/sf_uncertainties/.

6. unc_plotting_sf.py — Plots per-systematic SF deltas and total uncertainty envelope. Outputs to plots_tagging/sf_uncertainties/.

7. unc_finalPlots.py — Produces the final plots showing MC efficiency, data efficiency, and scale factor together with their total asymmetric uncertainty bands. Outputs to plots_tagging/final_plots/.


The files in the nominal processing sf folder were prior to the unc implementation. They calculate the nominal sf's and plot in the same format just without sys unc.
- tagging_eff.py - Only need to run 1 and it will output to rootfiles the efficiencies and scale factors. Need to change region between muon and electron.
- tagging_combineregions.py - must run after running tagging_eff for both muon and electron. This will combine the regions into single lepton. Following this run tagging_eff again changing it to slep to produce the eff and sf for the lepton region.
- tagging_comparison.py - This will generate a plot that will compare any region to the POG values or other specified values.
- tagging_plots.py - will output all plots for the region. Including the efficiency plots and the all numerator and denominator plots. 
