export interface CodelistType {
  label: string;
  value: string;
  organisation: string;
}

export interface CodelistPageDataTypes {
  name: string;
  id: string;
  codelists: CodelistType[];
}

export const codelistData: CodelistPageDataTypes[] = [
  {
    name: "Event",
    id: "codelist_event",
    codelists: [
      {
        label: "Abdominal aortic aneurysm diagnosis codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/aaa_cod/20210127",
      },
      {
        label: "Active and inactive ethnicity codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/ethnall_cod/20210127",
      },
      {
        label: "Alanine aminotransferase (ALT) tests",
        organisation: "OpenSAFELY",
        value: "opensafely/alanine-aminotransferase-alt-tests/2298df3e",
      },
      {
        label: "Alanine aminotransferase (ALT) tests (numerical value)",
        value:
          "opensafely/alanine-aminotransferase-alt-tests-numerical-value/78d4a307",
        organisation: "OpenSAFELY",
      },
      {
        label: "All BMI coded terms",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/bmi_stage/v.1.5.3",
      },
      {
        label: "Asplenia or Dysfunction of the Spleen codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/spln_cov/v.1.5.3",
      },
      {
        label: "Assessment instruments and outcome measures for long covid",
        value:
          "opensafely/assessment-instruments-and-outcome-measures-for-long-covid/79c0fa8a",
        organisation: "OpenSAFELY",
      },
      {
        label: "Asthma Admission codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/astadm/v.1.5.3",
      },
      {
        label: "Asthma Diagnosis code",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/ast/v.1.5.3",
      },
      {
        label: "Asthma annual review QOF",
        organisation: "OpenSAFELY",
        value: "opensafely/asthma-annual-review-qof/33eeb7da",
      },
      {
        label: "Asthma diagnosis codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/ast_cod/20210127",
      },
      {
        label: "Asthma resolved codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/astres_cod/20200812",
      },
      {
        label: "Atrial fibrillation codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/afib_cod/20200812",
      },
      {
        label: "Autism diagnosis codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/autism_cod/20210127",
      },
      {
        label: "BMI",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/bmi/v.1.5.3",
      },
      {
        label: "Blood Pressure recorded at home",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/homebp_cod/20200812",
      },
      {
        label: "Blood pressure (BP) recording codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/bp_cod/20200812",
      },
      {
        label: "COVID vaccination contraindication codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/covcontra/v.1.5.3",
      },
      {
        label: "COVID-19 Vaccination - Contraindication or Allergy",
        value:
          "opensafely/covid-19-vaccination-contraindication-or-allergy/59f7a1a0",
        organisation: "OpenSAFELY",
      },
      {
        label: "COVID-19 Vaccination - Did not attend first appointment",
        value:
          "opensafely/covid-19-vaccination-did-not-attend-first-appointment/300d360f",
        organisation: "OpenSAFELY",
      },
      {
        label: "COVID-19 Vaccination - Did not attend second appointment",
        value:
          "opensafely/covid-19-vaccination-did-not-attend-second-appointment/53e7a91c",
        organisation: "OpenSAFELY",
      },
      {
        label: "COVID-19 Vaccination - First dose not given",
        organisation: "OpenSAFELY",
        value: "opensafely/covid-19-vaccination-first-dose-not-given/786c94c1",
      },
      {
        label: "COVID-19 Vaccination - Second dose not given",
        organisation: "OpenSAFELY",
        value: "opensafely/covid-19-vaccination-second-dose-not-given/5d126fdc",
      },
      {
        label: "COVID-19 Vaccination Given",
        organisation: "OpenSAFELY",
        value: "opensafely/covid-19-vaccination-given/0f315647",
      },
      {
        label: "COVID-19 Vaccination Unavailable",
        organisation: "OpenSAFELY",
        value: "opensafely/covid-19-vaccination-unavailable/21c8c2b2",
      },
      {
        label: "CVD risk assessment score QOF",
        organisation: "OpenSAFELY",
        value: "opensafely/cvd-risk-assessment-score-qof/1adf44a5",
      },
      {
        label:
          "Care planning medication review simple reference set - NHS Digital",
        value:
          "opensafely/care-planning-medication-review-simple-reference-set-nhs-digital/61b13c39",
        organisation: "OpenSAFELY",
      },
      {
        label: "Carer codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/carer/v.1.5.3",
      },
      {
        label: "Cholesterol tests",
        organisation: "OpenSAFELY",
        value: "opensafely/cholesterol-tests/09896c09",
      },
      {
        label: "Cholesterol tests (numerical value)",
        organisation: "OpenSAFELY",
        value: "opensafely/cholesterol-tests-numerical-value/7e3a22f3",
      },
      {
        label: "Chronic Liver disease codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/cld/v.1.5.3",
      },
      {
        label:
          "Chronic Neurological Disease including Significant Learning Disorder",
        value: "primis-covid19-vacc-uptake/cns_cov/v.1.5.3",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
      },
      {
        label: "Chronic Respiratory Disease",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/resp_cov/v.1.5.3",
      },
      {
        label: "Chronic heart disease codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/chd_cov/v.1.5.3",
      },
      {
        label: "Chronic kidney disease (CKD) stage 1-2 codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/ckd1and2_cod/20200812",
      },
      {
        label: "Chronic kidney disease (CKD) stage 3-5 codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/ckd_cod/20200812",
      },
      {
        label: "Chronic kidney disease codes - all stages",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/ckd15/v.1.5.3",
      },
      {
        label: "Chronic kidney disease codes-stages 3 - 5",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/ckd35/v.1.5.3",
      },
      {
        label: "Chronic kidney disease diagnostic codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/ckd_cov/v.1.5.3",
      },
      {
        label: "Chronic obstructive pulmonary disease (COPD) codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/copd_cod/20210127",
      },
      {
        label: "Chronic obstructive pulmonary disease (COPD) review QoF",
        value:
          "opensafely/chronic-obstructive-pulmonary-disease-copd-review-qof/01cfd170",
        organisation: "OpenSAFELY",
      },
      {
        label: "Codes for dementia",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/dem_cod/20210127",
      },
      {
        label:
          "Codes for depression quality indicator care unsuitable for patient",
        value: "nhsd-primary-care-domain-refsets/deprpcapu_cod/20200812",
        organisation: "NHSD Primary Care Domain Refsets",
      },
      {
        label:
          "Codes for hypertension quality indicator care unsuitable for patient",
        value: "nhsd-primary-care-domain-refsets/hyppcapu_cod/20200812",
        organisation: "NHSD Primary Care Domain Refsets",
      },
      {
        label: "Codes for maximal blood pressure (BP) therapy",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/htmax_cod/20200812",
      },
      {
        label: "Codes indicating care home residency",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/carehome_cod/20211221",
      },
      {
        label:
          "Codes indicating the patient has chosen not to have blood pressure procedure",
        value: "nhsd-primary-care-domain-refsets/bpdec_cod/20200812",
        organisation: "NHSD Primary Care Domain Refsets",
      },
      {
        label:
          "Codes indicating the patient has chosen not to receive a flu vaccination",
        value: "nhsd-primary-care-domain-refsets/fludec_cod/20200812",
        organisation: "NHSD Primary Care Domain Refsets",
      },
      {
        label:
          "Codes indicating the patient has chosen not to receive depression quality indicator care",
        value: "nhsd-primary-care-domain-refsets/deprpcadec_cod/20200812",
        organisation: "NHSD Primary Care Domain Refsets",
      },
      {
        label:
          "Codes indicating the patient has chosen not to receive hypertension quality indicator care",
        value: "nhsd-primary-care-domain-refsets/hyppcadec_cod/20200812",
        organisation: "NHSD Primary Care Domain Refsets",
      },
      {
        label: "Coronary heart disease (CHD) codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/chd_cod/20210127",
      },
      {
        label: "Depression diagnosis codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/depr_cod/20210127",
      },
      {
        label: "Depression resolved codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/depres_cod/20200812",
      },
      {
        label: "Depression review codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/deprvw_cod/20210127",
      },
      {
        label: "Diabetes diagnosis codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/diab/v.1.5.3",
      },
      {
        label: "Diabetes mellitus codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/dm_cod/20210127",
      },
      {
        label: "Diabetes resolved codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/dmres/v.1.5.3",
      },
      {
        label: "Diabetes resolved codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/dmres_cod/20200812",
      },
      {
        label: "Employed by Care Home codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/carehome/v.1.5.3",
      },
      {
        label: "Employed by domiciliary care provider codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/domcare/v.1.5.3",
      },
      {
        label: "Employed by nursing home codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/nursehome/v.1.5.3",
      },
      {
        label: "Epilepsy diagnosis codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/epil_cod/20210127",
      },
      {
        label: "Ethnicity codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/eth2001/v1",
      },
      {
        label: "First COVID vaccination administration codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/covadm1/v.1.5.3",
      },
      {
        label: "First COVID vaccination declined",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/cov1decl/v.1.5.3",
      },
      {
        label: "Flu vaccination codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/flu_cod/20200812",
      },
      {
        label: "Glycated haemoglobin (HbA1c) tests",
        organisation: "OpenSAFELY",
        value: "opensafely/glycated-haemoglobin-hba1c-tests/2ab11f20",
      },
      {
        label: "Glycated haemoglobin (HbA1c) tests (numerical value)",
        value:
          "opensafely/glycated-haemoglobin-hba1c-tests-numerical-value/5134e926",
        organisation: "OpenSAFELY",
      },
      {
        label: "Haematological cancer codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/c19haemcan_cod/20210127",
      },
      {
        label: "Heart failure codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/hf_cod/20210127",
      },
      {
        label: "Height (SNOMED)",
        organisation: "OpenSAFELY",
        value: "opensafely/height-snomed/3b4a3891",
      },
      {
        label: "High Risk from COVID-19 code",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/shield/v.1.5.3",
      },
      {
        label: "Hypertension diagnosis codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/hyp_cod/20210127",
      },
      {
        label: "Hypertension resolved codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/hypres_cod/20200812",
      },
      {
        label: "Immunosuppression diagnosis codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/immdx_cov/v.1.5.3",
      },
      {
        label: "Invite for hypertension care review codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/hypinvite_cod/20200812",
      },
      {
        label: "Learning disability (LD) codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/ld_cod/20210127",
      },
      {
        label: "Lower Risk from COVID-19 codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/nonshield/v.1.5.3",
      },
      {
        label: "Mechanical or Artificial Valves",
        organisation: "OpenSAFELY",
        value: "opensafely/mechanical-or-artificial-valves/18c42b4d",
      },
      {
        label: "Medication review codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/medrvw_cod/20200812",
      },
      {
        label: "NHS England Care Homes residential status",
        organisation: "OpenSAFELY",
        value: "opensafely/nhs-england-care-homes-residential-status/3712ef13",
      },
      {
        label: "NICE managing the long-term effects of COVID-19",
        value:
          "opensafely/nice-managing-the-long-term-effects-of-covid-19/64f1ae69",
        organisation: "OpenSAFELY",
      },
      {
        label: "No longer a carer codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/notcarer/v.1.5.3",
      },
      {
        label: "Non-diabetic hyperglycaemia codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/ndh_cod/20200812",
      },
      {
        label:
          "Non-haematological cancer diagnosis codes with or without associated treatment",
        value: "nhsd-primary-care-domain-refsets/c19can_cod/20210127",
        organisation: "NHSD Primary Care Domain Refsets",
      },
      {
        label: "Osteoporosis codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/osteo_cod/20200812",
      },
      {
        label: "Palliative care codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/palcare_cod/20200812",
      },
      {
        label: "Palliative care not clinically indicated codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/palcareni_cod/20200812",
      },
      {
        label: "Patients in long-stay nursing and residential care",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/longres/v.1.5.3",
      },
      {
        label: "Peripheral arterial disease (PAD) diagnostic codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/pad_cod/20210127",
      },
      {
        label: "Prediabetes (SNOMED)",
        organisation: "OpenSAFELY",
        value: "opensafely/prediabetes-snomed/6bdbb7dd",
      },
      {
        label:
          "Pregnancy codes recorded in the 8.5 months before the audit run date",
        value: "primis-covid19-vacc-uptake/preg/v.1.5.3",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
      },
      {
        label:
          "Pregnancy or Delivery codes recorded in the 8.5 months before audit run date",
        value: "primis-covid19-vacc-uptake/pregdel/v.1.5.3",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
      },
      {
        label: "Psoriatic Arthritis",
        organisation: "OpenSAFELY",
        value: "opensafely/psoriatic-arthritis/2020-10-21",
      },
      {
        label:
          "Psychosis and schizophrenia and bipolar affective disease codes",
        value: "nhsd-primary-care-domain-refsets/mh_cod/20210127",
        organisation: "NHSD Primary Care Domain Refsets",
      },
      {
        label: "Pulse Oximetry - NHS Digtial COVID at Home",
        organisation: "OpenSAFELY",
        value: "opensafely/pulse-oximetry/72ce1380",
      },
      {
        label: "Red blood cell (RBC) tests",
        organisation: "OpenSAFELY",
        value: "opensafely/red-blood-cell-rbc-tests/576a859e",
      },
      {
        label: "Referral and signposting for long COVID",
        organisation: "OpenSAFELY",
        value: "opensafely/referral-and-signposting-for-long-covid/12d06dc0",
      },
      {
        label: "Remission codes relating to Severe Mental Illness",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/smhres/v.1.5.3",
      },
      {
        label: "Rheumatoid arthritis diagnosis codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/rarth_cod/20210127",
      },
      {
        label: "Second COVID vaccination administration codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/covadm2/v.1.5.3",
      },
      {
        label: "Second COVID vaccination declined",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/cov2decl/v.1.5.3",
      },
      {
        label: "Severe Mental Illness codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/sev_mental/v.1.5.3",
      },
      {
        label: "Severe Obesity code recorded",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/sev_obesity/v.1.5.3",
      },
      {
        label: "Sodium tests (numerical value)",
        organisation: "OpenSAFELY",
        value: "opensafely/sodium-tests-numerical-value/32bff605",
      },
      {
        label: "Stroke diagnosis codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/strk_cod/20210127",
      },
      {
        label: "Structured Medication Review - NHS England",
        organisation: "OpenSAFELY",
        value: "opensafely/structured-medication-review-nhs-england/5459205f",
      },
      {
        label: "Systolic blood pressure QoF",
        organisation: "OpenSAFELY",
        value: "opensafely/systolic-blood-pressure-qof/3572b5fb",
      },
      {
        label: "Thyroid stimulating hormone (TSH) testing",
        organisation: "OpenSAFELY",
        value: "opensafely/thyroid-stimulating-hormone-tsh-testing/11a1abeb",
      },
      {
        label: "Transient ischaemic attack (TIA) codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/tia_cod/20201016",
      },
      {
        label: "Weight (SNOMED)",
        organisation: "OpenSAFELY",
        value: "opensafely/weight-snomed/5459abc6",
      },
      {
        label: "Wider Learning Disability",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/learndis/v.1.5.3",
      },
      {
        label: "to represent household contact of shielding individual",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/hhld_imdef/v.1.5.3",
      },
    ],
  },
  {
    name: "Medication",
    id: "codelist_medication",
    codelists: [
      {
        label: "Abdominal aortic aneurysm diagnosis codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/aaa_cod/20210127",
      },
      {
        label: "Active and inactive ethnicity codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/ethnall_cod/20210127",
      },
      {
        label: "Alanine aminotransferase (ALT) tests",
        organisation: "OpenSAFELY",
        value: "opensafely/alanine-aminotransferase-alt-tests/2298df3e",
      },
      {
        label: "Alanine aminotransferase (ALT) tests (numerical value)",
        value:
          "opensafely/alanine-aminotransferase-alt-tests-numerical-value/78d4a307",
        organisation: "OpenSAFELY",
      },
      {
        label: "All BMI coded terms",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/bmi_stage/v.1.5.3",
      },
      {
        label: "Asplenia or Dysfunction of the Spleen codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/spln_cov/v.1.5.3",
      },
      {
        label: "Assessment instruments and outcome measures for long covid",
        value:
          "opensafely/assessment-instruments-and-outcome-measures-for-long-covid/79c0fa8a",
        organisation: "OpenSAFELY",
      },
      {
        label: "Asthma Admission codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/astadm/v.1.5.3",
      },
      {
        label: "Asthma Diagnosis code",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/ast/v.1.5.3",
      },
      {
        label: "Asthma annual review QOF",
        organisation: "OpenSAFELY",
        value: "opensafely/asthma-annual-review-qof/33eeb7da",
      },
      {
        label: "Asthma diagnosis codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/ast_cod/20210127",
      },
      {
        label: "Asthma resolved codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/astres_cod/20200812",
      },
      {
        label: "Atrial fibrillation codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/afib_cod/20200812",
      },
      {
        label: "Autism diagnosis codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/autism_cod/20210127",
      },
      {
        label: "BMI",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/bmi/v.1.5.3",
      },
      {
        label: "Blood Pressure recorded at home",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/homebp_cod/20200812",
      },
      {
        label: "Blood pressure (BP) recording codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/bp_cod/20200812",
      },
      {
        label: "COVID vaccination contraindication codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/covcontra/v.1.5.3",
      },
      {
        label: "COVID-19 Vaccination - Contraindication or Allergy",
        value:
          "opensafely/covid-19-vaccination-contraindication-or-allergy/59f7a1a0",
        organisation: "OpenSAFELY",
      },
      {
        label: "COVID-19 Vaccination - Did not attend first appointment",
        value:
          "opensafely/covid-19-vaccination-did-not-attend-first-appointment/300d360f",
        organisation: "OpenSAFELY",
      },
      {
        label: "COVID-19 Vaccination - Did not attend second appointment",
        value:
          "opensafely/covid-19-vaccination-did-not-attend-second-appointment/53e7a91c",
        organisation: "OpenSAFELY",
      },
      {
        label: "COVID-19 Vaccination - First dose not given",
        organisation: "OpenSAFELY",
        value: "opensafely/covid-19-vaccination-first-dose-not-given/786c94c1",
      },
      {
        label: "COVID-19 Vaccination - Second dose not given",
        organisation: "OpenSAFELY",
        value: "opensafely/covid-19-vaccination-second-dose-not-given/5d126fdc",
      },
      {
        label: "COVID-19 Vaccination Given",
        organisation: "OpenSAFELY",
        value: "opensafely/covid-19-vaccination-given/0f315647",
      },
      {
        label: "COVID-19 Vaccination Unavailable",
        organisation: "OpenSAFELY",
        value: "opensafely/covid-19-vaccination-unavailable/21c8c2b2",
      },
      {
        label: "CVD risk assessment score QOF",
        organisation: "OpenSAFELY",
        value: "opensafely/cvd-risk-assessment-score-qof/1adf44a5",
      },
      {
        label:
          "Care planning medication review simple reference set - NHS Digital",
        value:
          "opensafely/care-planning-medication-review-simple-reference-set-nhs-digital/61b13c39",
        organisation: "OpenSAFELY",
      },
      {
        label: "Carer codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/carer/v.1.5.3",
      },
      {
        label: "Cholesterol tests",
        organisation: "OpenSAFELY",
        value: "opensafely/cholesterol-tests/09896c09",
      },
      {
        label: "Cholesterol tests (numerical value)",
        organisation: "OpenSAFELY",
        value: "opensafely/cholesterol-tests-numerical-value/7e3a22f3",
      },
      {
        label: "Chronic Liver disease codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/cld/v.1.5.3",
      },
      {
        label:
          "Chronic Neurological Disease including Significant Learning Disorder",
        value: "primis-covid19-vacc-uptake/cns_cov/v.1.5.3",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
      },
      {
        label: "Chronic Respiratory Disease",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/resp_cov/v.1.5.3",
      },
      {
        label: "Chronic heart disease codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/chd_cov/v.1.5.3",
      },
      {
        label: "Chronic kidney disease (CKD) stage 1-2 codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/ckd1and2_cod/20200812",
      },
      {
        label: "Chronic kidney disease (CKD) stage 3-5 codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/ckd_cod/20200812",
      },
      {
        label: "Chronic kidney disease codes - all stages",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/ckd15/v.1.5.3",
      },
      {
        label: "Chronic kidney disease codes-stages 3 - 5",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/ckd35/v.1.5.3",
      },
      {
        label: "Chronic kidney disease diagnostic codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/ckd_cov/v.1.5.3",
      },
      {
        label: "Chronic obstructive pulmonary disease (COPD) codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/copd_cod/20210127",
      },
      {
        label: "Chronic obstructive pulmonary disease (COPD) review QoF",
        value:
          "opensafely/chronic-obstructive-pulmonary-disease-copd-review-qof/01cfd170",
        organisation: "OpenSAFELY",
      },
      {
        label: "Codes for dementia",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/dem_cod/20210127",
      },
      {
        label:
          "Codes for depression quality indicator care unsuitable for patient",
        value: "nhsd-primary-care-domain-refsets/deprpcapu_cod/20200812",
        organisation: "NHSD Primary Care Domain Refsets",
      },
      {
        label:
          "Codes for hypertension quality indicator care unsuitable for patient",
        value: "nhsd-primary-care-domain-refsets/hyppcapu_cod/20200812",
        organisation: "NHSD Primary Care Domain Refsets",
      },
      {
        label: "Codes for maximal blood pressure (BP) therapy",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/htmax_cod/20200812",
      },
      {
        label: "Codes indicating care home residency",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/carehome_cod/20211221",
      },
      {
        label:
          "Codes indicating the patient has chosen not to have blood pressure procedure",
        value: "nhsd-primary-care-domain-refsets/bpdec_cod/20200812",
        organisation: "NHSD Primary Care Domain Refsets",
      },
      {
        label:
          "Codes indicating the patient has chosen not to receive a flu vaccination",
        value: "nhsd-primary-care-domain-refsets/fludec_cod/20200812",
        organisation: "NHSD Primary Care Domain Refsets",
      },
      {
        label:
          "Codes indicating the patient has chosen not to receive depression quality indicator care",
        value: "nhsd-primary-care-domain-refsets/deprpcadec_cod/20200812",
        organisation: "NHSD Primary Care Domain Refsets",
      },
      {
        label:
          "Codes indicating the patient has chosen not to receive hypertension quality indicator care",
        value: "nhsd-primary-care-domain-refsets/hyppcadec_cod/20200812",
        organisation: "NHSD Primary Care Domain Refsets",
      },
      {
        label: "Coronary heart disease (CHD) codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/chd_cod/20210127",
      },
      {
        label: "Depression diagnosis codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/depr_cod/20210127",
      },
      {
        label: "Depression resolved codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/depres_cod/20200812",
      },
      {
        label: "Depression review codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/deprvw_cod/20210127",
      },
      {
        label: "Diabetes diagnosis codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/diab/v.1.5.3",
      },
      {
        label: "Diabetes mellitus codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/dm_cod/20210127",
      },
      {
        label: "Diabetes resolved codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/dmres/v.1.5.3",
      },
      {
        label: "Diabetes resolved codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/dmres_cod/20200812",
      },
      {
        label: "Employed by Care Home codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/carehome/v.1.5.3",
      },
      {
        label: "Employed by domiciliary care provider codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/domcare/v.1.5.3",
      },
      {
        label: "Employed by nursing home codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/nursehome/v.1.5.3",
      },
      {
        label: "Epilepsy diagnosis codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/epil_cod/20210127",
      },
      {
        label: "Ethnicity codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/eth2001/v1",
      },
      {
        label: "First COVID vaccination administration codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/covadm1/v.1.5.3",
      },
      {
        label: "First COVID vaccination declined",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/cov1decl/v.1.5.3",
      },
      {
        label: "Flu vaccination codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/flu_cod/20200812",
      },
      {
        label: "Glycated haemoglobin (HbA1c) tests",
        organisation: "OpenSAFELY",
        value: "opensafely/glycated-haemoglobin-hba1c-tests/2ab11f20",
      },
      {
        label: "Glycated haemoglobin (HbA1c) tests (numerical value)",
        value:
          "opensafely/glycated-haemoglobin-hba1c-tests-numerical-value/5134e926",
        organisation: "OpenSAFELY",
      },
      {
        label: "Haematological cancer codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/c19haemcan_cod/20210127",
      },
      {
        label: "Heart failure codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/hf_cod/20210127",
      },
      {
        label: "Height (SNOMED)",
        organisation: "OpenSAFELY",
        value: "opensafely/height-snomed/3b4a3891",
      },
      {
        label: "High Risk from COVID-19 code",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/shield/v.1.5.3",
      },
      {
        label: "Hypertension diagnosis codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/hyp_cod/20210127",
      },
      {
        label: "Hypertension resolved codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/hypres_cod/20200812",
      },
      {
        label: "Immunosuppression diagnosis codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/immdx_cov/v.1.5.3",
      },
      {
        label: "Invite for hypertension care review codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/hypinvite_cod/20200812",
      },
      {
        label: "Learning disability (LD) codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/ld_cod/20210127",
      },
      {
        label: "Lower Risk from COVID-19 codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/nonshield/v.1.5.3",
      },
      {
        label: "Mechanical or Artificial Valves",
        organisation: "OpenSAFELY",
        value: "opensafely/mechanical-or-artificial-valves/18c42b4d",
      },
      {
        label: "Medication review codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/medrvw_cod/20200812",
      },
      {
        label: "NHS England Care Homes residential status",
        organisation: "OpenSAFELY",
        value: "opensafely/nhs-england-care-homes-residential-status/3712ef13",
      },
      {
        label: "NICE managing the long-term effects of COVID-19",
        value:
          "opensafely/nice-managing-the-long-term-effects-of-covid-19/64f1ae69",
        organisation: "OpenSAFELY",
      },
      {
        label: "No longer a carer codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/notcarer/v.1.5.3",
      },
      {
        label: "Non-diabetic hyperglycaemia codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/ndh_cod/20200812",
      },
      {
        label:
          "Non-haematological cancer diagnosis codes with or without associated treatment",
        value: "nhsd-primary-care-domain-refsets/c19can_cod/20210127",
        organisation: "NHSD Primary Care Domain Refsets",
      },
      {
        label: "Osteoporosis codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/osteo_cod/20200812",
      },
      {
        label: "Palliative care codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/palcare_cod/20200812",
      },
      {
        label: "Palliative care not clinically indicated codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/palcareni_cod/20200812",
      },
      {
        label: "Patients in long-stay nursing and residential care",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/longres/v.1.5.3",
      },
      {
        label: "Peripheral arterial disease (PAD) diagnostic codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/pad_cod/20210127",
      },
      {
        label: "Prediabetes (SNOMED)",
        organisation: "OpenSAFELY",
        value: "opensafely/prediabetes-snomed/6bdbb7dd",
      },
      {
        label:
          "Pregnancy codes recorded in the 8.5 months before the audit run date",
        value: "primis-covid19-vacc-uptake/preg/v.1.5.3",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
      },
      {
        label:
          "Pregnancy or Delivery codes recorded in the 8.5 months before audit run date",
        value: "primis-covid19-vacc-uptake/pregdel/v.1.5.3",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
      },
      {
        label: "Psoriatic Arthritis",
        organisation: "OpenSAFELY",
        value: "opensafely/psoriatic-arthritis/2020-10-21",
      },
      {
        label:
          "Psychosis and schizophrenia and bipolar affective disease codes",
        value: "nhsd-primary-care-domain-refsets/mh_cod/20210127",
        organisation: "NHSD Primary Care Domain Refsets",
      },
      {
        label: "Pulse Oximetry - NHS Digtial COVID at Home",
        organisation: "OpenSAFELY",
        value: "opensafely/pulse-oximetry/72ce1380",
      },
      {
        label: "Red blood cell (RBC) tests",
        organisation: "OpenSAFELY",
        value: "opensafely/red-blood-cell-rbc-tests/576a859e",
      },
      {
        label: "Referral and signposting for long COVID",
        organisation: "OpenSAFELY",
        value: "opensafely/referral-and-signposting-for-long-covid/12d06dc0",
      },
      {
        label: "Remission codes relating to Severe Mental Illness",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/smhres/v.1.5.3",
      },
      {
        label: "Rheumatoid arthritis diagnosis codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/rarth_cod/20210127",
      },
      {
        label: "Second COVID vaccination administration codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/covadm2/v.1.5.3",
      },
      {
        label: "Second COVID vaccination declined",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/cov2decl/v.1.5.3",
      },
      {
        label: "Severe Mental Illness codes",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/sev_mental/v.1.5.3",
      },
      {
        label: "Severe Obesity code recorded",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/sev_obesity/v.1.5.3",
      },
      {
        label: "Sodium tests (numerical value)",
        organisation: "OpenSAFELY",
        value: "opensafely/sodium-tests-numerical-value/32bff605",
      },
      {
        label: "Stroke diagnosis codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/strk_cod/20210127",
      },
      {
        label: "Structured Medication Review - NHS England",
        organisation: "OpenSAFELY",
        value: "opensafely/structured-medication-review-nhs-england/5459205f",
      },
      {
        label: "Systolic blood pressure QoF",
        organisation: "OpenSAFELY",
        value: "opensafely/systolic-blood-pressure-qof/3572b5fb",
      },
      {
        label: "Thyroid stimulating hormone (TSH) testing",
        organisation: "OpenSAFELY",
        value: "opensafely/thyroid-stimulating-hormone-tsh-testing/11a1abeb",
      },
      {
        label: "Transient ischaemic attack (TIA) codes",
        organisation: "NHSD Primary Care Domain Refsets",
        value: "nhsd-primary-care-domain-refsets/tia_cod/20201016",
      },
      {
        label: "Weight (SNOMED)",
        organisation: "OpenSAFELY",
        value: "opensafely/weight-snomed/5459abc6",
      },
      {
        label: "Wider Learning Disability",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/learndis/v.1.5.3",
      },
      {
        label: "to represent household contact of shielding individual",
        organisation: "PRIMIS Covid Vaccination Uptake Reporting",
        value: "primis-covid19-vacc-uptake/hhld_imdef/v.1.5.3",
      },
      {
        label: "Disease-modifying antirheumatic drugs (DMARDs)",
        value: "opensafely/dmards",
        organisation: "OpenSAFELY",
      },
    ],
  },
];
