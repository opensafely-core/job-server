import React from "react";
import { Link } from "wouter";
import Button from "../components/Button";

function Glossary() {
  return (
    <>
      <div className="prose prose-blue">
        <p className="text-lg">
          Requesting an analysis requires you to select two SNOMED CT or dm+d
          codelists to see how they are used in combination over time.
        </p>
        <p className="text-lg">
          To make sure this is the right tool for you, check that you understand
          the following terms before continuing.
        </p>
        <h3>Codelist</h3>
        <p>
          A codelist is a set of codes that can be recorded in clinical systems.
          Codelists are used to select patients with activities and conditions
          of interest.
        </p>
        <p>Any codelist you require in your Analysis Request must:</p>
        <ul>
          <li>use either the SNOMED CT or dm+d coding system</li>
          <li>
            be published on{" "}
            <a
              href="https://www.opencodelists.org/"
              rel="noopener noreferrer"
              target="_blank"
            >
              OpenCodelists
            </a>
          </li>
        </ul>
        <p>
          You should review the codelists you wish to use on OpenCodelists and
          confirm it is suitable for your request before you start.
        </p>
        <p>
          Speak to your co-pilot if you can’t find a codelist you want to use,
          or you wish to add a new codelist to OpenCodelists.
        </p>
        <h3>SNOMED CT</h3>
        <p>
          <a
            href="https://digital.nhs.uk/services/terminology-and-classifications/snomed-ct"
            rel="noopener noreferrer"
            target="_blank"
          >
            SNOMED CT
          </a>{" "}
          is a systematically organised computer-processable collection of
          medical terms used in clinical documentation and reporting. It
          provides a consistent vocabulary for recording patient clinical
          information across the NHS and helps ensure data is recorded
          consistently and accurately.
        </p>
        <p>
          SNOMED CT codelists can query data related to recording of events such
          as:
        </p>
        <ul>
          <li>
            <strong>Condition Diagnoses </strong>&mdash; for example: Crohn’s
            Disease, Bipolar disorder
          </li>
          <li>
            <strong>Symptoms </strong>&mdash; for example: Headache, Blood in
            urine
          </li>
          <li>
            <strong>Test Results </strong>&mdash; for example: Potassium level,
            Abnormal ECG
          </li>
          <li>
            <strong>Procedures </strong>&mdash; for example: Coronary artery
            bypass graft, Hysterectomy
          </li>
          <li>
            <strong>Activities </strong>&mdash; for example: Medication review
          </li>
        </ul>
        <h3>dm+d</h3>
        <p>
          <a
            href="https://www.nhsbsa.nhs.uk/pharmacies-gp-practices-and-appliance-contractors/dictionary-medicines-and-devices-dmd"
            rel="noopener noreferrer"
            target="_blank"
          >
            dm+d
          </a>{" "}
          is a dictionary of descriptions and codes which represent medicines
          and devices in use across the NHS.
        </p>
        <p>
          dm+d codelists can query data related to prescriptions that have been
          issued for medicines or devices, for example: a prescription for
          Paracetamol 500mg tablets or for a Salbutamol 100micrograms/dose
          inhaler.
        </p>
      </div>

      <div className="flex flex-row w-full gap-2 mt-10">
        <Link asChild to="/find-codelists">
          <Button>Next</Button>
        </Link>
      </div>
    </>
  );
}

export default Glossary;
