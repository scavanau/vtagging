
class MonojetSelection(Module):
    """Module for selecting monojet events based on jet kinematics.

    Attributes:
        collection (str): Prefix for output keys to distinguish collections.
        jet_flavor (str): Specifies the jet type (e.g., "Jet" or "FatJet").
        jets (str): Name of the cleaned jets collection.
        min_pt_jet (float): Minimum transverse momentum for selected jets.
        max_eta_jet (float): Maximum pseudorapidity for selected jets.
        mass_type (Optional[str]): Type of the mass for FatJets
        min_mass (Optional[float]): Minimum mass for FatJets.
        max_mass (Optional[float]): Maximum mass for FatJets.
        veto_list (list[str]): List of selections to veto.
    """

    def __init__(self, cfg: dict[str, Any], events: Optional[Events] = None):
        """Initialize the MonojetSelection module."""
        super().__init__(cfg, events=events)
        self.collection: str = self.cfg.get("collection", "")
        self.jets: str = self.cfg.get("jets", "")
        self.min_pt_jet: Optional[float] = self.cfg.get("min_pt_jet", None)
        self.max_eta_jet: Optional[float] = self.cfg.get("max_eta_jet", None)
        self.mass_type: Optional[str] = self.cfg.get("mass_type", None)
        self.min_mass: Optional[float] = self.cfg.get("min_mass", None)
        self.max_mass: Optional[float] = self.cfg.get("max_mass", None)
        self.veto_list: list[str] = self.cfg.get("veto_list", [])
        self.sample: str = self.cfg.get("sample", "")

        self.validate_parameters()

    def call(self, events: Events) -> dict[str, Any]:
        """Perform monojet selection and return the selected jets."""
        jets = self.extract_jets(events)
        sublead_jet = get_subleading_object(obj=extract_object(events=events, obj_name=self.jets))
        monojet_sel = select_by_object_count(jets, min_count=1)

        for veto in self.veto_list:
            monojet_sel = monojet_sel * ~get_object(events=events, obj_name=veto)

        out = {
        f"{self.collection}selection": monojet_sel,
        f"{self.collection}{'Fatjets' if 'FatJet' in self.jets else 'jets'}": jets,
        f"{self.collection}sublead_{'Fatjets' if 'FatJet' in self.jets else 'jets'}": sublead_jet,
        }

        if "FatJet" in self.jets:
            weights1, weights2, matched, tagged = self.compute_tagging_sfs(events=events, jets=jets, do_matching=True)
            out["weight_matching_tagging_sf"] = weights1
            out["weight_tagging_sf_derived"] = weights2
            out["vjet_matched_selection"] = matched
            out["vjet_tagged_selection"] = tagged
            out["vjet_unmatched_selection"] = ~matched
            out["vjet_untagged_selection"] = ~tagged

        return out

    def extract_jets(self, events: Events) -> ak.Array:
        """Extract and apply selection criteria to jets."""
        jets = extract_object(events=events, obj_name=self.jets)
        # Select only the leading jet
        jets = get_leading_object(obj=jets)
        # Apply basic kinematic selection
        mask_jets = pt_selection(obj=jets, min_value=self.min_pt_jet)
        mask_jets = mask_jets & eta_selection(obj=jets, max_value=self.max_eta_jet)
        jets = jets[mask_jets]

        if "FatJet" in self.jets:
            # Apply mass cuts when given with mass type
            if self.mass_type:
                mass_mask = generic_selection(obj=jets, variable=self.mass_type, min_value=self.min_mass, max_value=self.max_mass)
                jets = jets[mass_mask]
        else:
            # Additional standard jet-specific selection
            ef_mask = generic_selection(obj=jets, variable="chHEF", min_value=0.1)
            ef_mask = ef_mask & generic_selection(obj=jets, variable="neHEF", max_value=0.8)
            jets = jets[ef_mask]

        return jets

    def compute_tagging_sfs(self, events, jets, do_matching):
    
        weights1 = ak.ones_like(events.run)
        weights2 = ak.ones_like(events.run)
        matched = ak.ones_like(events.run, dtype=bool)

        tagged = jets["particleNetWithMass_WvsQCD"] > 0.959
        tagged = ak.any(tagged, axis=1)
    
        samples_to_match = False
        for diboson in ["WW", "WZ", "ZZ"]:
         if self.sample.startswith(diboson):
                samples_to_match = True
        for singletop in ["TbarQto2Q-t-channel", "TQbarto2Q-t-channel"]:
            if self.sample.startswith(singletop):
                samples_to_match = True
        for ttbar in ["TTtoLNu2Q", "TTto4Q"]:
            if self.sample.startswith(ttbar):
                samples_to_match = True
        for vgamma in ["WGto2QG", "ZGto2QG"]:
            if self.sample.startswith(vgamma):
                samples_to_match = True


        if self.is_data:
            return weights1, weights2, matched, tagged
    
        if not samples_to_match:
            return weights1, weights2, ~matched, tagged

        if self.campaign == "Run3Summer22":
            pt_weights1 = [0.86, 0.86, 0.69]
            pt_weights2 = [0.67, 0.79, 1.02]
        elif self.campaign == "Run3Summer22EE":
            pt_weights1 = [0.94, 0.81, 0.76]
            pt_weights2 = [0.72, 0.85, 0.90]
        else:
            return weights1, weights2, matched, tagged
    
        
        if do_matching:
            gen_bosons = extract_object(events=events, obj_name="GenPart", variables=["pdgId", "status"])
            gen_bosons = gen_bosons[(abs(gen_bosons.pdgId) == 24) | (gen_bosons.pdgId == 23)]
            gen_bosons = gen_bosons[(gen_bosons.status == 22) | (gen_bosons.status == 62)]
            gen_bosons = gen_bosons[gen_bosons.pt > 100]
            overlap = has_overlap(obj_toclean=jets, clean_against=gen_bosons, max_dr=0.4)
            jets = jets[overlap]
        else:
            pass

        pt = jets.pt
        weights1 = ak.where(ak.any((pt >= 200) & (pt < 300), axis=1), weights1*pt_weights1[0], weights1)
        weights1 = ak.where(ak.any((pt >= 300) & (pt < 400), axis=1), weights1*pt_weights1[1], weights1)
        weights1 = ak.where(ak.any((pt >= 400), axis=1), weights1*pt_weights1[2], weights1)
        
        weights2 = ak.where(ak.any((pt >= 200) & (pt < 300), axis=1), weights2*pt_weights2[0], weights2)
        weights2 = ak.where(ak.any((pt >= 300) & (pt < 400), axis=1), weights2*pt_weights2[1], weights2)
        weights2 = ak.where(ak.any((pt >= 400), axis=1), weights2*pt_weights2[2], weights2)
        matched = ak.num(jets, axis=1) > 0

        return weights1, weights2, matched, tagged

    def validate_parameters(self) -> None:
        """Validate configuration parameters."""
        if not self.jets:
            self.logger.critical("Parameter 'jets' must be specified.", exception_cls=ValueError)
        if "FatJet" not in self.jets:
            if self.min_mass is not None or self.max_mass is not None:
                self.logger.critical(f"'min_mass' or 'max_mass' provided for jet_flavor '{self.jets}'.", exception_cls=ValueError)
        else:
            if self.mass_type is None and (self.min_mass is not None or self.max_mass is not None):
                self.logger.critical("'mass_type' must be specified to give the mass cuts ('pnetRegMass', 'msoftdrop', 'mass') .", exception_cls=ValueError)
        if self.collection:
            self.collection = f"{self.collection}_"


### Located in samples.py
def get_mc_settings(sample: str, dataset: str, is_background: bool, is_bsm: bool) -> dict[str, Any]:
        #weight_func = get_weight_total
        weight_func = partial(get_scaled_weight_total, multiply=["weight_tagging_sf_derived"])
        multiply = []
        if is_hf_cr:
            if "VBF" in region:
                multiply = ["weight_hf_noise_tf_nominal"]
            weight_func = partial(get_scaled_weight_total, multiply=multiply)
        settings = {
            "name": dataset,
            "group": sample,
            "datatier": datatier,
            "year": year,
            "energy": energy,
            "is_background": is_background,
            "is_signal": not is_background,
            "input_files": get_files_in_directory(directory=os.path.join(path, dataset), substring=""),
            "weight": weight_func,
            "weight_variations": partial(calculate_weight_variations, systematics=systematics["weight_variations"], multiply=multiply),
            "shape_variations": systematics["shape_variations"],
            "name_shape_nominal": systematics["name_shape_nominal"],
            "systematics": systematics["sources"],
        }
        settings.update(background_infos[sample] if is_background else signals_infos[sample] if not is_bsm else signals_infos["BSM"])

        return settings