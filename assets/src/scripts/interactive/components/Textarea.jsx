import { Field } from "formik";
import { bool, number, string } from "prop-types";
import React from "react";

function Textarea({ id, label, name, resize, rows, required }) {
  return (
    <div className="flex flex-col gap-y-3 text-lg leading-tight">
      <label className="font-semibold tracking-tight" htmlFor={id}>
        {label}
      </label>
      <Field
        as="textarea"
        className={`
          mt-1 block w-full max-w-prose rounded-md border-gray-400 text-gray-900 shadow-sm
          ${resize ? "" : "resize-none"}
          sm:text-sm
          focus:outline-none focus:ring-oxford-500 focus:border-oxford-500
        `}
        name={name}
        required={required}
        rows={rows}
      />
    </div>
  );
}

export default Textarea;

Textarea.defaultProps = {
  required: false,
  rows: 8,
};

Textarea.propTypes = {
  id: string.isRequired,
  label: string.isRequired,
  name: string.isRequired,
  required: bool,
  resize: bool.isRequired,
  rows: number,
};
